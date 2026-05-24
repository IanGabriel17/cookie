from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import ActivityLog, Category, InventoryLog, Product, Sale, SaleItem, VoidedSaleItem

ROLE_ADMIN = "Admin"
ROLE_CASHIER = "Cashier"
ROLE_INVENTORY = "Inventory Staff"

DEFAULT_CATEGORIES = [
    ("Bread", "BRD", "#f59e0b"),
    ("Cakes", "CKE", "#ec4899"),
    ("Pastries", "PAS", "#8b5cf6"),
    ("Cookies", "COOKIE", "#a16207"),
    ("Drinks", "DRINK", "#0ea5e9"),
    ("Custom Orders", "CUSTOM", "#10b981"),
]


def bootstrap_roles():
    for role in (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY):
        Group.objects.get_or_create(name=role)


def bootstrap_default_categories():
    for name, prefix, color in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            defaults={
                "description": f"{name} category",
                "barcode_prefix": prefix,
                "color": color,
            },
        )


def log_activity(*, user=None, action, instance=None, description="", ip_address=None, metadata=None):
    ActivityLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        model_name=instance.__class__.__name__ if instance is not None else "",
        object_id=str(instance.pk) if getattr(instance, "pk", None) else "",
        object_repr=str(instance)[:255] if instance is not None else "",
        description=description,
        ip_address=ip_address,
        metadata=metadata or {},
    )


def _money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _next_category_code(*, category, field_name):
    prefix = category.barcode_prefix or category.name[:3].upper()
    prefix = "".join(character for character in prefix.upper() if character.isalnum()) or "PRD"
    next_number = Product.objects.filter(**{f"{field_name}__startswith": f"{prefix}-"}).count() + 1
    while True:
        code = f"{prefix}-{next_number:04d}"
        if not Product.objects.filter(**{field_name: code}).exists():
            return code
        next_number += 1


def generate_product_sku(category):
    return _next_category_code(category=category, field_name="sku")


def generate_product_barcode(category):
    return _next_category_code(category=category, field_name="barcode")


def create_inventory_log(
    *,
    item_type,
    action,
    quantity_before,
    quantity_change,
    quantity_after,
    user=None,
    note="",
    reason="",
    product=None,
    sale=None,
):
    InventoryLog.objects.create(
        item_type=item_type,
        action=action,
        quantity_before=quantity_before,
        quantity_change=quantity_change,
        quantity_after=quantity_after,
        user=user,
        note=note,
        reason=reason,
        product=product,
        sale=sale,
    )


def _format_stock_quantity(value):
    value = Decimal(value)
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return str(value)


@transaction.atomic
def adjust_product_stock(product, quantity_change, user=None, note="", action=InventoryLog.ACTION_ADJUSTMENT, reason=""):
    quantity_change = int(quantity_change)
    product = Product.objects.select_for_update().get(pk=product.pk)
    before = Decimal(product.stock_quantity)
    after = before + Decimal(quantity_change)
    if after < 0:
        raise ValidationError(f"Stock for {product.name} cannot go below zero.")
    Product.objects.filter(pk=product.pk).update(stock_quantity=int(after))
    product.refresh_from_db()
    create_inventory_log(
        item_type=InventoryLog.ITEM_PRODUCT,
        action=action,
        quantity_before=before,
        quantity_change=Decimal(quantity_change),
        quantity_after=Decimal(product.stock_quantity),
        user=user,
        note=note,
        reason=reason,
        product=product,
    )
    log_activity(
        user=user,
        action=ActivityLog.ACTION_STOCK,
        instance=product,
        description=note or f"Product stock changed by {_format_stock_quantity(quantity_change)}.",
        metadata={"before": str(before), "change": str(quantity_change), "after": str(product.stock_quantity), "reason": reason},
    )
    return product


@transaction.atomic
def restock_product(product, quantity, user=None, note="", reason=InventoryLog.REASON_RESTOCK):
    return adjust_product_stock(
        product=product,
        quantity_change=quantity,
        user=user,
        note=note,
        action=InventoryLog.ACTION_RESTOCK,
        reason=reason,
    )


def _generate_receipt_number():
    stamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
    count = Sale.objects.count() + 1
    return f"OR-{stamp}-{count:04d}"


def _discount_amount(subtotal, discount_type, promo_discount_amount):
    if discount_type in (Sale.DISCOUNT_SENIOR, Sale.DISCOUNT_PWD):
        return _money(subtotal * Decimal("0.20"))
    if discount_type == Sale.DISCOUNT_PROMO:
        return min(_money(promo_discount_amount or "0"), subtotal)
    return Decimal("0.00")


@transaction.atomic
def create_sale(
    *,
    cashier,
    payment_type,
    payment_amount,
    items,
    notes="",
    sale_channel=Sale.CHANNEL_WALK_IN,
    discount_type=Sale.DISCOUNT_NONE,
    promo_discount_amount="0",
    tax_rate="0",
):
    if not items:
        raise ValidationError("At least one item is required to complete the sale.")

    payment_amount = _money(payment_amount)
    tax_rate = Decimal(tax_rate or "0")
    if tax_rate < 0:
        raise ValidationError("Tax rate cannot be negative.")
    subtotal = Decimal("0.00")
    normalized_items = []
    requested_quantities = {}

    for item in items:
        try:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
        except (KeyError, TypeError, ValueError):
            raise ValidationError("Invalid product or quantity in sale items.")
        if quantity <= 0:
            raise ValidationError("Invalid product or quantity in sale items.")
        requested_quantities[product_id] = requested_quantities.get(product_id, 0) + quantity

    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=requested_quantities.keys(), is_active=True)
    }
    if len(products) != len(requested_quantities):
        raise ValidationError("Invalid product or quantity in sale items.")

    for product_id, quantity in requested_quantities.items():
        product = products[product_id]
        if product.stock_quantity < quantity:
            raise ValidationError(f"Not enough stock for {product.name}.")

        line_total = product.price * quantity
        subtotal += line_total
        normalized_items.append(
            {
                "product": product,
                "quantity": quantity,
                "unit_price": product.price,
                "unit_cost": product.cost,
                "line_total": line_total,
            }
        )

    discount_amount = _discount_amount(subtotal, discount_type, promo_discount_amount)
    taxable_amount = subtotal - discount_amount
    tax_amount = _money(taxable_amount * tax_rate)
    total_amount = _money(taxable_amount + tax_amount)

    if payment_amount < total_amount:
        raise ValidationError("Payment amount must cover the total sale amount.")

    sale = Sale.objects.create(
        receipt_number=_generate_receipt_number(),
        cashier=cashier,
        sale_channel=sale_channel,
        payment_type=payment_type,
        subtotal=subtotal,
        discount_type=discount_type,
        discount_amount=discount_amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_amount=payment_amount,
        change_amount=payment_amount - total_amount,
        notes=notes,
    )

    for item in normalized_items:
        product = item["product"]
        quantity = item["quantity"]
        before = Decimal(product.stock_quantity)
        Product.objects.filter(pk=product.pk).update(stock_quantity=F("stock_quantity") - quantity)
        product.refresh_from_db()
        SaleItem.objects.create(sale=sale, **item)
        create_inventory_log(
            item_type=InventoryLog.ITEM_PRODUCT,
            action=InventoryLog.ACTION_SALE,
            quantity_before=before,
            quantity_change=Decimal(-quantity),
            quantity_after=Decimal(product.stock_quantity),
            user=cashier,
            note=f"Sold via {sale.receipt_number}",
            product=product,
            sale=sale,
        )
    log_activity(
        user=cashier,
        action=ActivityLog.ACTION_SALE,
        instance=sale,
        description=f"Completed sale {sale.receipt_number}.",
        metadata={"total": str(sale.total_amount), "discount": str(sale.discount_amount), "tax": str(sale.tax_amount)},
    )
    return sale


@transaction.atomic
def void_sale(*, sale, approved_by, reason):
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Void reason is required.")

    sale = Sale.objects.select_for_update().prefetch_related("items__product").get(pk=sale.pk)
    if sale.status == Sale.STATUS_VOIDED:
        raise ValidationError("This sale is already voided.")

    for item in sale.items.select_related("product"):
        product = Product.objects.select_for_update().get(pk=item.product_id)
        before = Decimal(product.stock_quantity)
        Product.objects.filter(pk=product.pk).update(stock_quantity=F("stock_quantity") + item.quantity)
        product.refresh_from_db()
        create_inventory_log(
            item_type=InventoryLog.ITEM_PRODUCT,
            action=InventoryLog.ACTION_VOID,
            quantity_before=before,
            quantity_change=Decimal(item.quantity),
            quantity_after=Decimal(product.stock_quantity),
            user=approved_by,
            note=f"Voided sale {sale.receipt_number}: {reason}",
            reason=InventoryLog.REASON_RETURNED,
            product=product,
            sale=sale,
        )
        VoidedSaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
            reason=reason,
        )
    sale.status = Sale.STATUS_VOIDED
    sale.void_reason = reason
    sale.voided_by = approved_by
    sale.voided_at = timezone.now()
    sale.save(update_fields=["status", "void_reason", "voided_by", "voided_at", "updated_at"])
    log_activity(
        user=approved_by,
        action=ActivityLog.ACTION_VOID,
        instance=sale,
        description=f"Voided sale {sale.receipt_number}.",
        metadata={"reason": reason},
    )
    return sale


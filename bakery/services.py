from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Ingredient, IngredientPurchase, InventoryLog, Product, Sale, SaleItem

ROLE_ADMIN = "Admin"
ROLE_CASHIER = "Cashier"
ROLE_INVENTORY = "Inventory Staff"


def bootstrap_roles():
    for role in (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY):
        Group.objects.get_or_create(name=role)


def create_inventory_log(
    *,
    item_type,
    action,
    quantity_before,
    quantity_change,
    quantity_after,
    user=None,
    note="",
    product=None,
    ingredient=None,
    sale=None,
    purchase=None,
):
    InventoryLog.objects.create(
        item_type=item_type,
        action=action,
        quantity_before=quantity_before,
        quantity_change=quantity_change,
        quantity_after=quantity_after,
        user=user,
        note=note,
        product=product,
        ingredient=ingredient,
        sale=sale,
        purchase=purchase,
    )


def _format_stock_quantity(value):
    value = Decimal(value)
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return str(value)


@transaction.atomic
def adjust_product_stock(product, quantity_change, user=None, note="", action=InventoryLog.ACTION_ADJUSTMENT):
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
        product=product,
    )
    return product


@transaction.atomic
def restock_product(product, quantity, user=None, note=""):
    return adjust_product_stock(
        product=product,
        quantity_change=quantity,
        user=user,
        note=note,
        action=InventoryLog.ACTION_RESTOCK,
    )


@transaction.atomic
def adjust_ingredient_stock(ingredient, quantity_change, user=None, note="", purchase=None, action=InventoryLog.ACTION_ADJUSTMENT):
    quantity_change = Decimal(quantity_change)
    ingredient = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
    before = ingredient.quantity_in_stock
    after = before + quantity_change
    if after < 0:
        raise ValidationError(f"Stock for {ingredient.name} cannot go below zero.")
    Ingredient.objects.filter(pk=ingredient.pk).update(quantity_in_stock=after)
    ingredient.refresh_from_db()
    create_inventory_log(
        item_type=InventoryLog.ITEM_INGREDIENT,
        action=action,
        quantity_before=before,
        quantity_change=quantity_change,
        quantity_after=ingredient.quantity_in_stock,
        user=user,
        note=note,
        ingredient=ingredient,
        purchase=purchase,
    )
    return ingredient


@transaction.atomic
def restock_ingredient(ingredient, quantity, user=None, note="", purchase=None, action=InventoryLog.ACTION_RESTOCK):
    return adjust_ingredient_stock(
        ingredient=ingredient,
        quantity_change=quantity,
        user=user,
        note=note,
        purchase=purchase,
        action=action,
    )


def _generate_receipt_number():
    stamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
    count = Sale.objects.count() + 1
    return f"OR-{stamp}-{count:04d}"


@transaction.atomic
def create_sale(*, cashier, payment_type, payment_amount, items, notes=""):
    if not items:
        raise ValidationError("At least one item is required to complete the sale.")

    payment_amount = Decimal(payment_amount)
    subtotal = Decimal("0.00")
    normalized_items = []
    requested_quantities = defaultdict(int)

    for item in items:
        try:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
        except (KeyError, TypeError, ValueError):
            raise ValidationError("Invalid product or quantity in sale items.")
        if quantity <= 0:
            raise ValidationError("Invalid product or quantity in sale items.")
        requested_quantities[product_id] += quantity

    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=requested_quantities.keys(), is_active=True)
    }
    if len(products) != len(requested_quantities):
        raise ValidationError("Invalid product or quantity in sale items.")

    ingredient_requirements = defaultdict(Decimal)

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

        for recipe in product.recipe_items.select_related("ingredient"):
            needed = recipe.quantity_required * quantity
            ingredient_requirements[recipe.ingredient_id] += needed

    ingredients = {
        ingredient.id: ingredient
        for ingredient in Ingredient.objects.select_for_update().filter(id__in=ingredient_requirements.keys())
    }
    for ingredient_id, needed in ingredient_requirements.items():
        ingredient = ingredients[ingredient_id]
        if ingredient.quantity_in_stock < needed:
            raise ValidationError(f"Not enough ingredient stock for {ingredient.name}.")

    if payment_amount < subtotal:
        raise ValidationError("Payment amount must cover the total sale amount.")

    sale = Sale.objects.create(
        receipt_number=_generate_receipt_number(),
        cashier=cashier,
        payment_type=payment_type,
        subtotal=subtotal,
        total_amount=subtotal,
        payment_amount=payment_amount,
        change_amount=payment_amount - subtotal,
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

    for ingredient_id, needed in ingredient_requirements.items():
        ingredient = ingredients[ingredient_id]
        before_ingredient = ingredient.quantity_in_stock
        Ingredient.objects.filter(pk=ingredient.pk).update(quantity_in_stock=F("quantity_in_stock") - needed)
        ingredient.refresh_from_db()
        create_inventory_log(
            item_type=InventoryLog.ITEM_INGREDIENT,
            action=InventoryLog.ACTION_SALE,
            quantity_before=before_ingredient,
            quantity_change=-needed,
            quantity_after=ingredient.quantity_in_stock,
            user=cashier,
            note=f"Used in {sale.receipt_number}",
            ingredient=ingredient,
            sale=sale,
        )
    return sale


@transaction.atomic
def record_purchase(*, purchase: IngredientPurchase, user=None):
    ingredient = Ingredient.objects.select_for_update().get(pk=purchase.ingredient_id)
    ingredient.cost_per_unit = purchase.unit_cost
    ingredient.supplier = purchase.supplier
    ingredient.expiration_date = purchase.expiration_date
    ingredient.save(update_fields=["cost_per_unit", "supplier", "expiration_date", "updated_at"])
    restock_ingredient(
        ingredient=ingredient,
        quantity=purchase.quantity,
        user=user,
        note=f"Purchased from {purchase.supplier.name}",
        purchase=purchase,
        action=InventoryLog.ACTION_PURCHASE,
    )


@transaction.atomic
def reconcile_purchase_update(*, purchase: IngredientPurchase, previous_purchase: IngredientPurchase, user=None):
    if not purchase.unit:
        purchase.unit = purchase.ingredient.unit
        purchase.save(update_fields=["unit", "updated_at"])

    if previous_purchase.ingredient_id == purchase.ingredient_id:
        delta = purchase.quantity - previous_purchase.quantity
        if delta:
            adjust_ingredient_stock(
                ingredient=purchase.ingredient,
                quantity_change=delta,
                user=user,
                note=f"Purchase updated: {_format_stock_quantity(delta)} {purchase.display_unit}",
                purchase=purchase,
                action=InventoryLog.ACTION_PURCHASE if delta > 0 else InventoryLog.ACTION_ADJUSTMENT,
            )
    else:
        adjust_ingredient_stock(
            ingredient=previous_purchase.ingredient,
            quantity_change=-previous_purchase.quantity,
            user=user,
            note=f"Purchase moved to {purchase.ingredient.name}",
            purchase=purchase,
            action=InventoryLog.ACTION_ADJUSTMENT,
        )
        adjust_ingredient_stock(
            ingredient=purchase.ingredient,
            quantity_change=purchase.quantity,
            user=user,
            note=f"Purchase moved from {previous_purchase.ingredient.name}",
            purchase=purchase,
            action=InventoryLog.ACTION_PURCHASE,
        )

    ingredient = Ingredient.objects.select_for_update().get(pk=purchase.ingredient_id)
    ingredient.cost_per_unit = purchase.unit_cost
    ingredient.supplier = purchase.supplier
    ingredient.expiration_date = purchase.expiration_date
    ingredient.save(update_fields=["cost_per_unit", "supplier", "expiration_date", "updated_at"])


@transaction.atomic
def reverse_purchase_stock(*, purchase: IngredientPurchase, user=None):
    adjust_ingredient_stock(
        ingredient=purchase.ingredient,
        quantity_change=-purchase.quantity,
        user=user,
        note=f"Deleted purchase from {purchase.supplier.name}",
        purchase=purchase,
        action=InventoryLog.ACTION_ADJUSTMENT,
    )

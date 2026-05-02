from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .forms import (
    CategoryForm,
    IngredientForm,
    IngredientPurchaseForm,
    LoginForm,
    OrderForm,
    ProductForm,
    RecipeForm,
    RestockIngredientForm,
    RestockProductForm,
    SupplierForm,
)
from .models import Category, Ingredient, IngredientPurchase, InventoryLog, Order, Product, Recipe, Sale, Supplier
from .permissions import RoleRequiredMixin, user_has_role
from .services import (
    ROLE_ADMIN,
    ROLE_CASHIER,
    ROLE_INVENTORY,
    adjust_ingredient_stock,
    adjust_product_stock,
    bootstrap_roles,
    create_sale,
    reconcile_purchase_update,
    record_purchase,
    reverse_purchase_stock,
)


STOCK_STATUS_CHOICES = [
    ("in", "In Stock"),
    ("low", "Low Stock"),
    ("out", "Out of Stock"),
]


def filter_products_by_status(queryset, status):
    if status == "in":
        return queryset.filter(stock_quantity__gt=F("low_stock_threshold"))
    if status == "low":
        return queryset.filter(stock_quantity__gt=0, stock_quantity__lte=F("low_stock_threshold"))
    if status == "out":
        return queryset.filter(stock_quantity=0)
    return queryset


def filter_ingredients_by_status(queryset, status):
    if status == "in":
        return queryset.filter(quantity_in_stock__gt=F("reorder_level"))
    if status == "low":
        return queryset.filter(quantity_in_stock__gt=0, quantity_in_stock__lte=F("reorder_level"))
    if status == "out":
        return queryset.filter(quantity_in_stock__lte=0)
    return queryset


class BakeryLoginView(LoginView):
    template_name = "bakery/login.html"
    authentication_form = LoginForm

    def dispatch(self, request, *args, **kwargs):
        bootstrap_roles()
        return super().dispatch(request, *args, **kwargs)


class BakeryLogoutView(LogoutView):
    pass


class DashboardView(RoleRequiredMixin, TemplateView):
    template_name = "bakery/dashboard.html"
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        sales_today = Sale.objects.filter(sold_at__date=today)
        sales_month = Sale.objects.filter(sold_at__date__gte=month_start)

        top_products = (
            Product.objects.filter(sale_items__sale__isnull=False)
            .annotate(total_sold=Sum("sale_items__quantity"))
            .order_by("-total_sold", "name")[:5]
        )
        recent_transactions = Sale.objects.select_related("cashier").prefetch_related("items__product")[:6]
        low_products = Product.objects.filter(stock_quantity__lte=F("low_stock_threshold"), is_active=True).order_by("stock_quantity")[:6]
        low_ingredients = Ingredient.objects.filter(quantity_in_stock__lte=F("reorder_level")).order_by("quantity_in_stock")[:6]
        sales_series = (
            Sale.objects.filter(sold_at__date__gte=today - timedelta(days=6))
            .annotate(day=TruncDate("sold_at"))
            .values("day")
            .annotate(total=Sum("total_amount"))
            .order_by("day")
        )

        context.update(
            {
                "daily_sales": sales_today.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00"),
                "monthly_sales": sales_month.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00"),
                "recent_transactions": recent_transactions,
                "top_products": top_products,
                "low_products": low_products,
                "low_ingredients": low_ingredients,
                "low_stock_count": low_products.count() + low_ingredients.count(),
                "chart_labels": [entry["day"].strftime("%b %d") for entry in sales_series],
                "chart_values": [float(entry["total"]) for entry in sales_series],
            }
        )
        return context


class BaseListView(RoleRequiredMixin, ListView):
    paginate_by = 10
    allowed_roles = (ROLE_ADMIN, ROLE_INVENTORY)


class BaseCreateView(RoleRequiredMixin, CreateView):
    template_name = "bakery/form.html"
    allowed_roles = (ROLE_ADMIN, ROLE_INVENTORY)


class BaseUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "bakery/form.html"
    allowed_roles = (ROLE_ADMIN, ROLE_INVENTORY)


class BaseDeleteView(RoleRequiredMixin, DeleteView):
    template_name = "bakery/confirm_delete.html"
    allowed_roles = (ROLE_ADMIN, ROLE_INVENTORY)


class CategoryListView(BaseListView):
    model = Category
    template_name = "bakery/category_list.html"


class CategoryCreateView(BaseCreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("category-list")


class CategoryUpdateView(BaseUpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("category-list")


class CategoryDeleteView(BaseDeleteView):
    model = Category
    success_url = reverse_lazy("category-list")


class ProductListView(BaseListView):
    model = Product
    template_name = "bakery/product_list.html"
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        search = self.request.GET.get("search", "").strip()
        category = self.request.GET.get("category", "")
        status = self.request.GET.get("status", "")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(category__name__icontains=search))
        if category:
            queryset = queryset.filter(category_id=category)
        queryset = filter_products_by_status(queryset, status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "categories": Category.objects.all(),
                "stock_status_choices": STOCK_STATUS_CHOICES,
            }
        )
        return context


class ProductCreateView(BaseCreateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy("product-list")


class ProductUpdateView(BaseUpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy("product-list")


class ProductDeleteView(BaseDeleteView):
    model = Product
    success_url = reverse_lazy("product-list")


class InventoryDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "bakery/inventory_dashboard.html"
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get("search", "").strip()
        item_type = self.request.GET.get("type", "")
        category = self.request.GET.get("category", "")
        status = self.request.GET.get("status", "")

        products = Product.objects.select_related("category").order_by("name")
        ingredients = Ingredient.objects.select_related("supplier").order_by("name")

        if search:
            products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(category__name__icontains=search))
            ingredients = ingredients.filter(Q(name__icontains=search) | Q(unit__icontains=search) | Q(supplier__name__icontains=search))
        if category:
            products = products.filter(category_id=category)
            ingredients = Ingredient.objects.none()

        products = filter_products_by_status(products, status)
        ingredients = filter_ingredients_by_status(ingredients, status)

        if item_type == "products":
            ingredients = Ingredient.objects.none()
        elif item_type == "ingredients":
            products = Product.objects.none()

        inventory_rows = [
            {
                "kind": "Product",
                "name": product.name,
                "sku": product.sku,
                "category": product.category.name,
                "available_stock": product.stock_quantity,
                "unit": "pcs",
                "cost_price": product.cost,
                "price": product.price,
                "supplier": "",
                "expiration_date": None,
                "status": product.stock_status,
                "image": product.product_image,
                "object": product,
            }
            for product in products
        ]
        inventory_rows.extend(
            [
                {
                    "kind": "Stock Item",
                    "name": ingredient.name,
                    "sku": f"STK-{ingredient.pk:04d}",
                    "category": "Raw Material",
                    "available_stock": ingredient.quantity_in_stock,
                    "unit": ingredient.unit,
                    "cost_price": ingredient.cost_per_unit,
                    "price": ingredient.cost_per_unit,
                    "supplier": ingredient.supplier.name if ingredient.supplier else "",
                    "expiration_date": ingredient.expiration_date,
                    "status": ingredient.stock_status,
                    "image": None,
                    "object": ingredient,
                }
                for ingredient in ingredients
            ]
        )

        stock_issues = Product.objects.filter(stock_quantity__lte=F("low_stock_threshold"), is_active=True).count()
        stock_issues += Ingredient.objects.filter(quantity_in_stock__lte=F("reorder_level")).count()

        context.update(
            {
                "inventory_rows": inventory_rows,
                "categories": Category.objects.all(),
                "stock_status_choices": STOCK_STATUS_CHOICES,
                "sku_total": Product.objects.count() + Ingredient.objects.count(),
                "products_reserved": Order.objects.exclude(status=Order.STATUS_CLAIMED).aggregate(total=Sum("quantity"))["total"] or 0,
                "stock_issues": stock_issues,
                "featured_stock": inventory_rows[0] if inventory_rows else None,
                "can_manage_inventory": user_has_role(self.request.user, ROLE_ADMIN, ROLE_INVENTORY),
            }
        )
        return context


class IngredientListView(BaseListView):
    model = Ingredient
    template_name = "bakery/ingredient_list.html"

    def get_queryset(self):
        queryset = Ingredient.objects.select_related("supplier")
        search = self.request.GET.get("search", "").strip()
        supplier = self.request.GET.get("supplier", "")
        status = self.request.GET.get("status", "")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(unit__icontains=search) | Q(supplier__name__icontains=search))
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        queryset = filter_ingredients_by_status(queryset, status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "suppliers": Supplier.objects.all(),
                "stock_status_choices": STOCK_STATUS_CHOICES,
            }
        )
        return context


class IngredientCreateView(BaseCreateView):
    model = Ingredient
    form_class = IngredientForm
    success_url = reverse_lazy("ingredient-list")


class IngredientUpdateView(BaseUpdateView):
    model = Ingredient
    form_class = IngredientForm
    success_url = reverse_lazy("ingredient-list")


class IngredientDeleteView(BaseDeleteView):
    model = Ingredient
    success_url = reverse_lazy("ingredient-list")


class RecipeListView(BaseListView):
    model = Recipe
    template_name = "bakery/recipe_list.html"

    def get_queryset(self):
        return Recipe.objects.select_related("product", "ingredient")


class RecipeCreateView(BaseCreateView):
    model = Recipe
    form_class = RecipeForm
    success_url = reverse_lazy("recipe-list")


class RecipeUpdateView(BaseUpdateView):
    model = Recipe
    form_class = RecipeForm
    success_url = reverse_lazy("recipe-list")


class RecipeDeleteView(BaseDeleteView):
    model = Recipe
    success_url = reverse_lazy("recipe-list")


class SupplierListView(BaseListView):
    model = Supplier
    template_name = "bakery/supplier_list.html"


class SupplierCreateView(BaseCreateView):
    model = Supplier
    form_class = SupplierForm
    success_url = reverse_lazy("supplier-list")


class SupplierUpdateView(BaseUpdateView):
    model = Supplier
    form_class = SupplierForm
    success_url = reverse_lazy("supplier-list")


class SupplierDeleteView(BaseDeleteView):
    model = Supplier
    success_url = reverse_lazy("supplier-list")


class OrderListView(BaseListView):
    model = Order
    template_name = "bakery/order_list.html"
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY)


class OrderCreateView(BaseCreateView):
    model = Order
    form_class = OrderForm
    success_url = reverse_lazy("order-list")
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY)


class OrderUpdateView(BaseUpdateView):
    model = Order
    form_class = OrderForm
    success_url = reverse_lazy("order-list")
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY)


class OrderDeleteView(BaseDeleteView):
    model = Order
    success_url = reverse_lazy("order-list")
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER)


class PurchaseListView(BaseListView):
    model = IngredientPurchase
    template_name = "bakery/purchase_list.html"

    def get_queryset(self):
        return IngredientPurchase.objects.select_related("supplier", "ingredient")


class PurchaseCreateView(BaseCreateView):
    model = IngredientPurchase
    form_class = IngredientPurchaseForm
    success_url = reverse_lazy("purchase-list")

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            record_purchase(purchase=self.object, user=self.request.user)
        messages.success(self.request, "Ingredient purchase recorded and stock updated.")
        return redirect(self.get_success_url())


class PurchaseUpdateView(BaseUpdateView):
    model = IngredientPurchase
    form_class = IngredientPurchaseForm
    success_url = reverse_lazy("purchase-list")

    def form_valid(self, form):
        previous_purchase = IngredientPurchase.objects.select_related("ingredient", "supplier").get(pk=self.object.pk)
        try:
            with transaction.atomic():
                self.object = form.save()
                reconcile_purchase_update(
                    purchase=self.object,
                    previous_purchase=previous_purchase,
                    user=self.request.user,
                )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Purchase updated and stock reconciled.")
        return redirect(self.get_success_url())


class PurchaseDeleteView(BaseDeleteView):
    model = IngredientPurchase
    success_url = reverse_lazy("purchase-list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                reverse_purchase_stock(purchase=self.object, user=request.user)
                self.object.delete()
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect(self.get_success_url())
        messages.success(request, "Purchase deleted and stock reconciled.")
        return redirect(self.get_success_url())


class InventoryLogListView(BaseListView):
    model = InventoryLog
    template_name = "bakery/inventory_log_list.html"
    paginate_by = 20

    def get_queryset(self):
        return InventoryLog.objects.select_related("product", "ingredient", "user", "sale", "purchase")


class SaleListView(RoleRequiredMixin, ListView):
    model = Sale
    template_name = "bakery/sale_list.html"
    paginate_by = 12
    allowed_roles = (ROLE_ADMIN, ROLE_CASHIER)

    def get_queryset(self):
        return Sale.objects.select_related("cashier").prefetch_related("items__product")


@login_required
def sale_receipt_view(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_CASHIER):
        return redirect("dashboard")
    sale = get_object_or_404(Sale.objects.select_related("cashier").prefetch_related("items__product"), pk=pk)
    return render(request, "bakery/receipt.html", {"sale": sale})


@login_required
def pos_view(request):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_CASHIER):
        return redirect("dashboard")
    products = Product.objects.filter(is_active=True).select_related("category").order_by("category__name", "name")
    if request.method == "POST":
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")
        items = [{"product_id": product_id, "quantity": quantity} for product_id, quantity in zip(product_ids, quantities) if product_id and quantity]
        try:
            sale = create_sale(
                cashier=request.user,
                payment_type=request.POST.get("payment_type", Sale.PAYMENT_CASH),
                payment_amount=request.POST.get("payment_amount", "0"),
                items=items,
                notes=request.POST.get("notes", ""),
            )
            messages.success(request, f"Transaction {sale.receipt_number} saved successfully.")
            return redirect("sale-receipt", pk=sale.pk)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
    return render(request, "bakery/pos.html", {"products": products, "payment_types": Sale.PAYMENT_CHOICES})


@login_required
@require_POST
def restock_product_view(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_INVENTORY):
        return redirect("dashboard")
    product = get_object_or_404(Product, pk=pk)
    form = RestockProductForm(request.POST)
    if form.is_valid():
        quantity_change = form.signed_quantity()
        note = form.cleaned_data["note"] or ("Manual product restock" if quantity_change > 0 else "Manual product usage")
        try:
            adjust_product_stock(
                product,
                quantity_change,
                request.user,
                note,
                InventoryLog.ACTION_RESTOCK if quantity_change > 0 else InventoryLog.ACTION_ADJUSTMENT,
            )
            movement = "increased" if quantity_change > 0 else "decreased"
            messages.success(request, f"{product.name} stock {movement} successfully.")
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
    else:
        messages.error(request, "Could not restock product.")
    return redirect(request.POST.get("next") or "product-list")


@login_required
@require_POST
def restock_ingredient_view(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_INVENTORY):
        return redirect("dashboard")
    ingredient = get_object_or_404(Ingredient, pk=pk)
    form = RestockIngredientForm(request.POST)
    if form.is_valid():
        quantity_change = form.signed_quantity()
        note = form.cleaned_data["note"] or ("Manual stock restock" if quantity_change > 0 else "Manual stock usage")
        try:
            adjust_ingredient_stock(
                ingredient,
                quantity_change,
                request.user,
                note,
                action=InventoryLog.ACTION_RESTOCK if quantity_change > 0 else InventoryLog.ACTION_ADJUSTMENT,
            )
            movement = "increased" if quantity_change > 0 else "decreased"
            messages.success(request, f"{ingredient.name} stock {movement} successfully.")
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
    else:
        messages.error(request, "Could not restock ingredient.")
    return redirect(request.POST.get("next") or "ingredient-list")


class ReportsView(RoleRequiredMixin, TemplateView):
    template_name = "bakery/reports.html"
    allowed_roles = (ROLE_ADMIN, ROLE_INVENTORY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = Sale.objects.prefetch_related("items__product")
        total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        total_profit = sum(sale.total_profit for sale in sales)
        product_profits = Product.objects.annotate(
            total_sold=Sum("sale_items__quantity"),
            profit_value=Sum(
                ExpressionWrapper(
                    (F("sale_items__unit_price") - F("sale_items__unit_cost")) * F("sale_items__quantity"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
        ).order_by("-profit_value")
        context.update(
            {
                "sales": sales[:12],
                "total_sales": total_sales,
                "total_profit": total_profit,
                "product_profits": product_profits[:6],
                "low_products": Product.objects.filter(stock_quantity__lte=F("low_stock_threshold")),
                "low_ingredients": Ingredient.objects.filter(quantity_in_stock__lte=F("reorder_level")),
            }
        )
        return context


@login_required
def sales_excel_export(request):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_INVENTORY):
        return redirect("dashboard")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales Report"
    sheet.append(["Receipt", "Cashier", "Date", "Payment Type", "Total Amount", "Profit"])
    for sale in Sale.objects.select_related("cashier"):
        sheet.append(
            [
                sale.receipt_number,
                sale.cashier.username,
                timezone.localtime(sale.sold_at).strftime("%Y-%m-%d %H:%M"),
                sale.get_payment_type_display(),
                float(sale.total_amount),
                float(sale.total_profit),
            ]
        )
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="bakery-sales-report.xlsx"'
    return response


@login_required
def sales_pdf_export(request):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_INVENTORY):
        return redirect("dashboard")
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30, height - 40, "Bakery Sales Report")
    pdf.setFont("Helvetica", 10)
    y = height - 80
    headers = ["Receipt", "Cashier", "Date", "Total", "Profit"]
    x_positions = [30, 130, 230, 360, 450]
    for index, header in enumerate(headers):
        pdf.drawString(x_positions[index], y, header)
    y -= 18
    for sale in Sale.objects.select_related("cashier")[:30]:
        row = [
            sale.receipt_number,
            sale.cashier.username,
            timezone.localtime(sale.sold_at).strftime("%Y-%m-%d"),
            f"PHP {sale.total_amount:,.2f}",
            f"PHP {sale.total_profit:,.2f}",
        ]
        for index, value in enumerate(row):
            pdf.drawString(x_positions[index], y, str(value))
        y -= 16
        if y < 50:
            pdf.showPage()
            y = height - 40
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="bakery-sales-report.pdf"'
    return response


@login_required
def backup_database_view(request):
    if not user_has_role(request.user, ROLE_ADMIN):
        return redirect("dashboard")
    from django.conf import settings

    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        messages.warning(request, "Database backup download is only available for SQLite in this build.")
        return redirect("reports")
    db_path = settings.DATABASES["default"]["NAME"]
    with open(db_path, "rb") as file_handle:
        response = HttpResponse(file_handle.read(), content_type="application/octet-stream")
        response["Content-Disposition"] = 'attachment; filename="bakery-backup.sqlite3"'
        return response


@login_required
def printable_receipt_pdf(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_CASHIER):
        return redirect("dashboard")
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product"), pk=pk)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(80 * mm, 200 * mm))
    y = 520
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(113, y, "Sweet Crumbs Bakery")
    y -= 20
    pdf.setFont("Helvetica", 9)
    pdf.drawString(20, y, f"Receipt: {sale.receipt_number}")
    y -= 14
    pdf.drawString(20, y, f"Date: {timezone.localtime(sale.sold_at).strftime('%Y-%m-%d %H:%M')}")
    y -= 20
    pdf.setStrokeColor(colors.grey)
    pdf.line(15, y, 210, y)
    y -= 14
    for item in sale.items.all():
        pdf.drawString(20, y, f"{item.product.name} x{item.quantity}")
        pdf.drawRightString(200, y, f"{item.line_total:,.2f}")
        y -= 14
    pdf.line(15, y, 210, y)
    y -= 16
    pdf.drawString(20, y, "Total")
    pdf.drawRightString(200, y, f"{sale.total_amount:,.2f}")
    y -= 14
    pdf.drawString(20, y, "Payment")
    pdf.drawRightString(200, y, f"{sale.payment_amount:,.2f}")
    y -= 14
    pdf.drawString(20, y, "Change")
    pdf.drawRightString(200, y, f"{sale.change_amount:,.2f}")
    y -= 24
    pdf.drawCentredString(113, y, "Thank you for your order!")
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{sale.receipt_number}.pdf"'
    return response

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Note(TimeStampedModel):
    title = models.CharField(max_length=150)
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    product_image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def profit_per_unit(self):
        return self.price - self.cost

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"


class Ingredient(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    unit = models.CharField(max_length=30, default="pcs")
    quantity_in_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=5, validators=[MinValueValidator(Decimal("0.00"))])
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    supplier = models.ForeignKey("Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_items")
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    @property
    def stock_status(self):
        if self.quantity_in_stock <= 0:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"


class Recipe(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recipe_items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recipe_items")
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit = models.CharField(max_length=30, blank=True)

    class Meta:
        unique_together = ("product", "ingredient")
        ordering = ["product__name", "ingredient__name"]

    def __str__(self):
        unit = self.unit or self.ingredient.unit
        return f"{self.product.name}: {self.quantity_required} {unit} {self.ingredient.name}"


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IngredientPurchase(TimeStampedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchases")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="purchases")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit = models.CharField(max_length=30, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    expiration_date = models.DateField(null=True, blank=True)
    purchased_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-purchased_at", "-created_at"]

    def __str__(self):
        return f"{self.ingredient.name} from {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.unit and self.ingredient_id:
            self.unit = self.ingredient.unit
        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    @property
    def display_unit(self):
        return self.unit or self.ingredient.unit


class Sale(TimeStampedModel):
    PAYMENT_CASH = "cash"
    PAYMENT_GCASH = "gcash"
    PAYMENT_CARD = "card"
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_GCASH, "GCash"),
        (PAYMENT_CARD, "Card"),
    ]

    receipt_number = models.CharField(max_length=30, unique=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    sold_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-sold_at", "-id"]

    def __str__(self):
        return self.receipt_number

    @property
    def total_profit(self):
        result = self.items.aggregate(
            total=Sum(
                models.ExpressionWrapper(
                    (F("unit_price") - F("unit_cost")) * F("quantity"),
                    output_field=models.DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )["total"]
        return result or Decimal("0.00")


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Order(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CLAIMED = "claimed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CLAIMED, "Claimed"),
    ]

    customer_name = models.CharField(max_length=150)
    contact = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    order_date = models.DateField(default=timezone.localdate)
    pickup_date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ["pickup_date", "customer_name"]

    def __str__(self):
        return f"{self.customer_name} - {self.pickup_date}"


class InventoryLog(TimeStampedModel):
    ITEM_PRODUCT = "product"
    ITEM_INGREDIENT = "ingredient"
    ITEM_CHOICES = [
        (ITEM_PRODUCT, "Product"),
        (ITEM_INGREDIENT, "Ingredient"),
    ]
    ACTION_RESTOCK = "restock"
    ACTION_SALE = "sale"
    ACTION_PURCHASE = "purchase"
    ACTION_ADJUSTMENT = "adjustment"
    ACTION_CHOICES = [
        (ACTION_RESTOCK, "Restock"),
        (ACTION_SALE, "Sale"),
        (ACTION_PURCHASE, "Purchase"),
        (ACTION_ADJUSTMENT, "Adjustment"),
    ]

    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name="inventory_logs")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, null=True, blank=True, related_name="inventory_logs")
    quantity_before = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_logs")
    purchase = models.ForeignKey(
        IngredientPurchase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_logs",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.product or self.ingredient
        return f"{target} - {self.action}"

from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Category, Ingredient, IngredientPurchase, Order, Product, Recipe, Supplier


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            base_class = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{base_class} form-check-input".strip()
            else:
                widget.attrs["class"] = f"{base_class} form-control".strip()


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "sku",
            "price",
            "cost",
            "stock_quantity",
            "low_stock_threshold",
            "product_image",
            "is_active",
        ]
        labels = {"cost": "Cost Price"}


class IngredientForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            "name",
            "quantity_in_stock",
            "unit",
            "cost_per_unit",
            "supplier",
            "expiration_date",
            "reorder_level",
        ]
        labels = {
            "name": "Product Name",
            "quantity_in_stock": "Quantity",
            "cost_per_unit": "Cost Price",
            "reorder_level": "Low Stock Level",
            "expiration_date": "Expiration Date",
        }
        widgets = {"expiration_date": forms.DateInput(attrs={"type": "date"})}


class RecipeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["product", "ingredient", "quantity_required", "unit"]


class SupplierForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "phone", "email", "address", "notes"]


class IngredientPurchaseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = IngredientPurchase
        fields = ["supplier", "ingredient", "quantity", "unit", "unit_cost", "expiration_date", "purchased_at", "notes"]
        labels = {
            "ingredient": "Product Name",
            "unit_cost": "Cost Price",
            "expiration_date": "Expiration Date",
        }
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
            "purchased_at": forms.DateInput(attrs={"type": "date"}),
        }


class OrderForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer_name",
            "contact",
            "product",
            "order_date",
            "pickup_date",
            "quantity",
            "estimated_total",
            "notes",
            "status",
        ]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class StockMovementFormMixin(StyledFormMixin, forms.Form):
    MOVEMENT_INCREASE = "increase"
    MOVEMENT_DECREASE = "decrease"
    MOVEMENT_CHOICES = [
        (MOVEMENT_INCREASE, "Increase"),
        (MOVEMENT_DECREASE, "Decrease"),
    ]

    movement = forms.ChoiceField(choices=MOVEMENT_CHOICES, required=False)
    note = forms.CharField(required=False)

    def clean_movement(self):
        return self.cleaned_data.get("movement") or self.MOVEMENT_INCREASE

    def signed_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if self.cleaned_data["movement"] == self.MOVEMENT_DECREASE:
            return -quantity
        return quantity


class RestockProductForm(StockMovementFormMixin):
    quantity = forms.IntegerField(min_value=1)


class RestockIngredientForm(StockMovementFormMixin):
    quantity = forms.DecimalField(min_value=Decimal("0.01"), decimal_places=2, max_digits=12)

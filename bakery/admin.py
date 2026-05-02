from django.contrib import admin

from .models import (
    Category,
    Ingredient,
    IngredientPurchase,
    InventoryLog,
    Order,
    Product,
    Recipe,
    Sale,
    SaleItem,
    Supplier,
)


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "cost", "stock_quantity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku")
    inlines = [RecipeInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "quantity_in_stock", "reorder_level", "cost_per_unit", "supplier", "expiration_date")
    list_filter = ("supplier", "expiration_date")
    search_fields = ("name", "supplier__name")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "cashier", "payment_type", "total_amount", "payment_amount", "change_amount", "sold_at")
    list_filter = ("payment_type", "sold_at")
    search_fields = ("receipt_number", "cashier__username")
    inlines = [SaleItemInline]


admin.site.register(Category)
admin.site.register(Recipe)
admin.site.register(Order)
admin.site.register(Supplier)
@admin.register(IngredientPurchase)
class IngredientPurchaseAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "supplier", "quantity", "unit", "unit_cost", "expiration_date", "purchased_at")
    list_filter = ("supplier", "expiration_date", "purchased_at")
    search_fields = ("ingredient__name", "supplier__name")


admin.site.register(InventoryLog)

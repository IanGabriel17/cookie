from django.contrib import admin

from .models import (
    ActivityLog,
    Category,
    InventoryLog,
    LoginHistory,
    Order,
    Product,
    ProductionBatch,
    Sale,
    SaleItem,
    Supplier,
    VoidedSaleItem,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "barcode", "category", "price", "cost", "stock_quantity", "display_status", "is_active", "is_archived")
    list_filter = ("category", "is_active", "is_archived", "expiry_date")
    search_fields = ("name", "sku", "barcode", "item_id")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total")


class VoidedSaleItemInline(admin.TabularInline):
    model = VoidedSaleItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total", "reason")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "cashier", "sale_channel", "payment_type", "total_amount", "status", "sold_at")
    list_filter = ("payment_type", "sale_channel", "status", "sold_at")
    search_fields = ("receipt_number", "cashier__username")
    inlines = [SaleItemInline, VoidedSaleItemInline]


admin.site.register(Category)
admin.site.register(Order)
admin.site.register(Supplier)

admin.site.register(InventoryLog)
admin.site.register(ProductionBatch)
admin.site.register(ActivityLog)
admin.site.register(LoginHistory)

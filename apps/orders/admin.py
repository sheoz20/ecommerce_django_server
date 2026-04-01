"""
Admin configuration for the orders app.
"""
from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for order items.
    """
    model = OrderItem
    extra = 0
    readonly_fields = [
        'product', 'variant', 'product_name', 'product_sku',
        'variant_name', 'quantity', 'unit_price', 'total_price'
    ]
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    """
    Inline admin for order status history.
    """
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'notes', 'created_by', 'created_at']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Order model.
    """
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'total', 'item_count', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'order_number', 'subtotal', 'shipping_cost', 'tax',
        'discount', 'total', 'created_at', 'updated_at',
        'paid_at', 'shipped_at', 'delivered_at'
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """
    Admin configuration for ShippingAddress model.
    """
    list_display = [
        'user', 'first_name', 'last_name', 'city',
        'state', 'country', 'is_default'
    ]
    list_filter = ['country', 'is_default', 'created_at']
    search_fields = [
        'user__email', 'first_name', 'last_name',
        'city', 'state', 'postal_code'
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderItem model.
    """
    list_display = [
        'order', 'product_name', 'quantity',
        'unit_price', 'total_price'
    ]
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = [
        'order', 'product', 'variant', 'product_name',
        'product_sku', 'variant_name', 'quantity',
        'unit_price', 'total_price'
    ]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderStatusHistory model.
    """
    list_display = ['order', 'old_status', 'new_status', 'created_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = [
        'order', 'old_status', 'new_status',
        'notes', 'created_by', 'created_at'
    ]

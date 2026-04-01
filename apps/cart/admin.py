"""
Admin configuration for the cart app.
"""
from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """
    Inline admin for cart items.
    """
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'unit_price', 'total_price', 'added_at']
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin configuration for Cart model.
    """
    list_display = ['user', 'total_items', 'subtotal', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'total_items', 'subtotal', 'total']
    inlines = [CartItemInline]

    def has_add_permission(self, request):
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for CartItem model.
    """
    list_display = ['cart', 'product', 'variant', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at', 'updated_at']
    search_fields = ['cart__user__email', 'product__name']
    readonly_fields = ['cart', 'product', 'variant', 'unit_price', 'total_price', 'added_at', 'updated_at']

    def has_add_permission(self, request):
        return False

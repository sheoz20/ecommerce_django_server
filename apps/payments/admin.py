"""
Admin configuration for the payments app.
"""
from django.contrib import admin

from .models import Payment, PaymentMethod, Transaction


class TransactionInline(admin.TabularInline):
    """
    Inline admin for transactions.
    """
    model = Transaction
    extra = 0
    readonly_fields = [
        'transaction_type', 'amount', 'status',
        'gateway_transaction_id', 'gateway_response',
        'error_message', 'created_at'
    ]
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model.
    """
    list_display = [
        'order', 'user', 'amount', 'method',
        'status', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'method', 'created_at']
    search_fields = [
        'order__order_number', 'user__email',
        'transaction_id', 'card_last_four'
    ]
    readonly_fields = [
        'order', 'user', 'amount', 'currency', 'method',
        'transaction_id', 'gateway_response',
        'card_last_four', 'card_brand',
        'created_at', 'updated_at', 'completed_at'
    ]
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction model.
    """
    list_display = [
        'payment', 'transaction_type', 'amount',
        'status', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['payment__order__order_number', 'gateway_transaction_id']
    readonly_fields = [
        'payment', 'transaction_type', 'amount', 'status',
        'gateway_transaction_id', 'gateway_response',
        'error_message', 'created_at'
    ]


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """
    Admin configuration for PaymentMethod model.
    """
    list_display = [
        'user', 'method_type', 'card_brand',
        'card_last_four', 'is_default', 'is_active'
    ]
    list_filter = ['method_type', 'is_default', 'is_active']
    search_fields = ['user__email', 'card_last_four']
    readonly_fields = ['created_at', 'updated_at']

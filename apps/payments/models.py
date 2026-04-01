"""
Models for the payments app.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models

from apps.orders.models import Order
from apps.users.models import CustomUser


class Payment(models.Model):
    """
    Payment model for order payments.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        CANCELLED = 'cancelled', 'Cancelled'

    class Method(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        PAYPAL = 'paypal', 'PayPal'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CASH_ON_DELIVERY = 'cash_on_delivery', 'Cash on Delivery'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    method = models.CharField(
        max_length=30,
        choices=Method.choices,
        default=Method.CREDIT_CARD
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Transaction IDs
    transaction_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Card Details (masked)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.order_number}"


class Transaction(models.Model):
    """
    Transaction records for payment gateway interactions.
    """
    class Type(models.TextChoices):
        CHARGE = 'charge', 'Charge'
        REFUND = 'refund', 'Refund'
        AUTHORIZATION = 'authorization', 'Authorization'
        CAPTURE = 'capture', 'Capture'
        VOID = 'void', 'Void'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=Type.choices
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.status} - {self.amount}"


class PaymentMethod(models.Model):
    """
    Saved payment methods for users.
    """
    class Type(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        PAYPAL = 'paypal', 'PayPal'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    method_type = models.CharField(
        max_length=20,
        choices=Type.choices
    )
    
    # Card Details (masked)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    card_expiry_month = models.CharField(max_length=2, blank=True)
    card_expiry_year = models.CharField(max_length=4, blank=True)
    
    # Token from payment gateway
    token = models.CharField(max_length=255, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        if self.method_type == self.Type.CREDIT_CARD:
            return f"{self.card_brand} ending in {self.card_last_four}"
        return f"{self.method_type} - {self.user.email}"

"""
Models for the orders app.
"""
import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.catalog.models import Product, ProductVariant
from apps.users.models import CustomUser


class ShippingAddress(models.Model):
    """
    Shipping address for orders.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipping_addresses'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='US')
    
    # For saved addresses
    is_default = models.BooleanField(default=False)
    address_name = models.CharField(max_length=100, blank=True, help_text="e.g., Home, Office")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shipping Address'
        verbose_name_plural = 'Shipping Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to non-default
            if self.user:
                ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Order model for customer purchases.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Shipping
    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate unique order number."""
        timestamp = self.created_at.strftime('%Y%m%d') if self.created_at else ''
        unique_id = str(self.id)[:8].upper()
        return f"ORD-{timestamp}-{unique_id}"

    @property
    def item_count(self):
        """Total number of items in order."""
        return sum(item.quantity for item in self.items.all())

    def can_cancel(self):
        """Check if order can be cancelled."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    def cancel(self):
        """Cancel the order and restore stock."""
        if self.can_cancel():
            self.status = self.Status.CANCELLED
            self.save()
            
            # Restore stock
            for item in self.items.all():
                if item.product.track_inventory:
                    if item.variant:
                        item.variant.stock_quantity += item.quantity
                        item.variant.save()
                    else:
                        item.product.stock_quantity += item.quantity
                        item.product.save()
            
            return True
        return False


class OrderItem(models.Model):
    """
    Individual items in an order.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    variant_name = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Track order status changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} -> {self.new_status}"

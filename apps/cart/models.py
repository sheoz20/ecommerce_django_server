"""
Models for the cart app.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Product, ProductVariant
from apps.users.models import CustomUser


class Cart(models.Model):
    """
    Shopping cart model linked to authenticated users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def total_items(self):
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Subtotal before discounts and taxes."""
        return sum(item.total_price for item in self.items.all())

    @property
    def total(self):
        """Final total (can be extended with tax, shipping)."""
        return self.subtotal

    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Individual items in a cart.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'product', 'variant']
        ordering = ['-added_at']

    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_info}"

    @property
    def unit_price(self):
        """Price per unit (considering variant)."""
        if self.variant:
            return self.variant.final_price
        return self.product.price

    @property
    def total_price(self):
        """Total price for this item."""
        return self.unit_price * self.quantity

    def clean(self):
        """Validate cart item."""
        from django.core.exceptions import ValidationError
        
        # Check if variant belongs to product
        if self.variant and self.variant.product != self.product:
            raise ValidationError("Variant does not belong to the selected product.")
        
        # Check stock availability
        if self.product.track_inventory:
            available_stock = self.variant.stock_quantity if self.variant else self.product.stock_quantity
            if self.quantity > available_stock:
                raise ValidationError(
                    f"Only {available_stock} items available in stock."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

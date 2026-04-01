"""
Models for the reviews app.
"""
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Product
from apps.orders.models import Order
from apps.users.models import CustomUser


class Review(models.Model):
    """
    Product review and rating model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    
    # Rating (1-5 stars)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Review content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Media
    images = models.JSONField(default=list, blank=True)
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Helpfulness
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per product per user

    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"

    def save(self, *args, **kwargs):
        # Check if this is a verified purchase
        if self.order:
            self.is_verified_purchase = self.order.items.filter(
                product=self.product
            ).exists()
        super().save(*args, **kwargs)


class ReviewHelpfulness(models.Model):
    """
    Track user votes on review helpfulness.
    """
    class Vote(models.TextChoices):
        HELPFUL = 'helpful', 'Helpful'
        NOT_HELPFUL = 'not_helpful', 'Not Helpful'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpfulness_votes'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    vote = models.CharField(max_length=15, choices=Vote.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Review Helpfulness Vote'
        verbose_name_plural = 'Review Helpfulness Votes'
        unique_together = ['review', 'user']

    def __str__(self):
        return f"{self.user.email} voted {self.vote} on review {self.review.id}"


class Wishlist(models.Model):
    """
    User wishlist for products.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-created_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.email} wishes for {self.product.name}"

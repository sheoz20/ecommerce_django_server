"""
Models for the catalog app.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """
    Product category with hierarchical structure.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    image = models.ImageField(
        upload_to='categories/%Y/%m/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """
    Product model with detailed information.
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'
        DISCONTINUED = 'discontinued', 'Discontinued'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    cost_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    track_inventory = models.BooleanField(default=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    is_featured = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    review_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"SKU-{str(self.id)[:8].upper()}"
        
        # Auto-update status based on stock
        if self.track_inventory and self.stock_quantity == 0:
            self.status = self.Status.OUT_OF_STOCK
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 if self.track_inventory else True

    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

    @property
    def primary_image(self):
        """Return the primary product image or first available image."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    def update_rating(self):
        """Update average rating based on reviews."""
        from apps.reviews.models import Review
        reviews = Review.objects.filter(product=self)
        if reviews.exists():
            self.average_rating = reviews.aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or 0
            self.review_count = reviews.count()
            self.save(update_fields=['average_rating', 'review_count'])


class ProductImage(models.Model):
    """
    Product images with multiple support.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """
    Product variants (e.g., size, color options).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attributes = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def final_price(self):
        return self.product.price + self.price_adjustment

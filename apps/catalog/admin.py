"""
Admin configuration for the catalog app.
"""
from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Category, Product, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    """
    Inline admin for product images.
    """
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']


class ProductVariantInline(admin.TabularInline):
    """
    Inline admin for product variants.
    """
    model = ProductVariant
    extra = 1
    fields = ['name', 'sku', 'price_adjustment', 'stock_quantity', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model.
    """
    list_display = [
        'name', 'sku', 'price', 'stock_quantity',
        'status', 'is_featured', 'average_rating', 'created_at'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status', 'is_featured', 'price']
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_per_item')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_inventory')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Ratings', {
            'fields': ('average_rating', 'review_count'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['average_rating', 'review_count']


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    """
    Admin configuration for Category model.
    """
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    mptt_level_indent = 20


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductImage model.
    """
    list_display = ['product', 'alt_text', 'is_primary', 'sort_order']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'alt_text']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductVariant model.
    """
    list_display = ['product', 'name', 'sku', 'final_price', 'stock_quantity', 'is_active']
    list_filter = ['is_active']
    search_fields = ['product__name', 'name', 'sku']

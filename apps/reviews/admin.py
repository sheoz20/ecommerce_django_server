"""
Admin configuration for the reviews app.
"""
from django.contrib import admin

from .models import Review, ReviewHelpfulness, Wishlist


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin configuration for Review model.
    """
    list_display = [
        'product', 'user', 'rating', 'is_verified_purchase',
        'is_approved', 'is_featured', 'helpful_count', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'is_approved',
        'is_featured', 'created_at'
    ]
    search_fields = [
        'product__name', 'user__email', 'title', 'comment'
    ]
    list_editable = ['is_approved', 'is_featured']
    readonly_fields = ['helpful_count', 'not_helpful_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'user', 'order', 'rating', 'title', 'comment')
        }),
        ('Media', {
            'fields': ('images',)
        }),
        ('Status', {
            'fields': ('is_verified_purchase', 'is_approved', 'is_featured')
        }),
        ('Helpfulness', {
            'fields': ('helpful_count', 'not_helpful_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    """
    Admin configuration for ReviewHelpfulness model.
    """
    list_display = ['review', 'user', 'vote', 'created_at']
    list_filter = ['vote', 'created_at']
    search_fields = ['review__product__name', 'user__email']
    readonly_fields = ['created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """
    Admin configuration for Wishlist model.
    """
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__email', 'product__name']
    readonly_fields = ['created_at']

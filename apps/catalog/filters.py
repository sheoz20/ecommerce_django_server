"""
Filters for the catalog app.
"""
import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filter set for products.
    """
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    search = django_filters.CharFilter(method='filter_search')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'newest'),
            ('price', 'price'),
            ('average_rating', 'rating'),
            ('name', 'name'),
        ),
        field_labels={
            'created_at': 'Newest',
            'price': 'Price',
            'average_rating': 'Rating',
            'name': 'Name',
        }
    )

    class Meta:
        model = Product
        fields = [
            'category', 'status', 'is_featured',
            'min_price', 'max_price', 'in_stock', 'has_discount'
        ]

    def filter_search(self, queryset, name, value):
        """Search in name, description, and tags."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(tags__icontains=value) |
                Q(sku__iexact=value)
            )
        return queryset

    def filter_in_stock(self, queryset, name, value):
        """Filter by stock availability."""
        if value:
            return queryset.filter(
                Q(track_inventory=False) |
                Q(track_inventory=True, stock_quantity__gt=0)
            )
        return queryset.filter(
            track_inventory=True, stock_quantity=0
        )

    def filter_has_discount(self, queryset, name, value):
        """Filter products with discount."""
        if value:
            return queryset.filter(
                compare_at_price__isnull=False,
                compare_at_price__gt=models.F('price')
            )
        return queryset


# Import models at the end to avoid circular imports
from django.db import models

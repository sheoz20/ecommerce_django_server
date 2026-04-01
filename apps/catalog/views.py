"""
Views for the catalog app.
"""
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for category operations.
    """
    queryset = Category.objects.filter(is_active=True)
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'tree':
            return CategoryTreeSerializer
        return CategorySerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get category tree structure.
        """
        root_categories = Category.objects.filter(parent=None, is_active=True)
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """
        Get products in a category (including subcategories).
        """
        category = self.get_object()
        # Get all subcategory IDs
        category_ids = category.get_descendants(include_self=True).values_list('id', flat=True)
        
        products = Product.objects.filter(
            category_id__in=category_ids,
            status=Product.Status.ACTIVE
        )
        
        # Apply filtering
        product_filter = ProductFilter(request.query_params, queryset=products)
        page = self.paginate_queryset(product_filter.qs)
        
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(product_filter.qs, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product operations.
    """
    queryset = Product.objects.all()
    lookup_field = 'slug'
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'price', 'average_rating', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Non-admin users only see active products
        if not self.request.user.is_staff:
            queryset = queryset.filter(status=Product.Status.ACTIVE)
        
        return queryset.select_related('category').prefetch_related('images', 'variants')

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products.
        """
        products = Product.objects.filter(
            is_featured=True,
            status=Product.Status.ACTIVE
        )[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """
        Get new arrival products.
        """
        products = Product.objects.filter(
            status=Product.Status.ACTIVE
        ).order_by('-created_at')[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """
        Get bestseller products (placeholder - would integrate with order data).
        """
        # For now, return featured products with highest ratings
        products = Product.objects.filter(
            status=Product.Status.ACTIVE
        ).order_by('-average_rating', '-review_count')[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_stock(self, request, slug=None):
        """
        Update product stock quantity (admin only).
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response(
                {'error': 'Quantity is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            product.stock_quantity = quantity
            product.save()
            return Response({
                'message': 'Stock updated successfully.',
                'stock_quantity': product.stock_quantity
            })
        except ValueError:
            return Response(
                {'error': 'Quantity must be a valid integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """
        Get related products (same category).
        """
        product = self.get_object()
        
        if product.category:
            related = Product.objects.filter(
                category=product.category,
                status=Product.Status.ACTIVE
            ).exclude(id=product.id)[:8]
        else:
            related = Product.objects.filter(
                status=Product.Status.ACTIVE
            ).exclude(id=product.id)[:8]
        
        serializer = ProductListSerializer(related, many=True)
        return Response(serializer.data)

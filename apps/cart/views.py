"""
Views for the cart app.
"""
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.catalog.models import Product, ProductVariant

from .models import Cart, CartItem
from .serializers import (
    AddToCartSerializer,
    CartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)


class CartViewSet(viewsets.GenericViewSet):
    """
    ViewSet for cart operations.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_or_create_cart(self):
        """Get or create cart for current user."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        """
        Get current user's cart.
        """
        cart = self.get_or_create_cart()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add item to cart.
        """
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self.get_or_create_cart()
        data = serializer.validated_data

        product = Product.objects.get(id=data['product_id'])
        variant = None
        if data.get('variant_id'):
            variant = ProductVariant.objects.get(id=data['variant_id'])

        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': data['quantity']}
        )

        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + data['quantity']
            
            # Check stock for updated quantity
            available_stock = variant.stock_quantity if variant else product.stock_quantity
            if product.track_inventory and new_quantity > available_stock:
                return Response(
                    {'error': f'Only {available_stock} items available in stock.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = new_quantity
            cart_item.save()

        response_serializer = CartItemSerializer(cart_item)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put'])
    def update_item(self, request):
        """
        Update cart item quantity.
        """
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_or_create_cart()
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_quantity = serializer.validated_data['quantity']
        
        # Check stock
        product = cart_item.product
        variant = cart_item.variant
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        
        if product.track_inventory and new_quantity > available_stock:
            return Response(
                {'error': f'Only {available_stock} items available in stock.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = new_quantity
        cart_item.save()

        response_serializer = CartItemSerializer(cart_item)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """
        Remove item from cart.
        """
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_or_create_cart()
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response(
                {'message': 'Item removed from cart.'},
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all items from cart.
        """
        cart = self.get_or_create_cart()
        cart.clear()
        return Response(
            {'message': 'Cart cleared successfully.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get cart summary (for header display).
        """
        cart = self.get_or_create_cart()
        return Response({
            'total_items': cart.total_items,
            'subtotal': cart.subtotal,
            'total': cart.total
        })

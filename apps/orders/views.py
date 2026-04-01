"""
Views for the orders app.
"""
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cart.models import Cart
from apps.users.models import UserActivity

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress
from .serializers import (
    CreateOrderSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderStatusHistorySerializer,
    OrderStatusUpdateSerializer,
    ShippingAddressSerializer,
)


class ShippingAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for shipping address operations.
    """
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_number'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_permissions(self):
        if self.action in ['update_status', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def create(self, request):
        """
        Create order from cart.
        """
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart or not cart.items.exists():
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipping_address = serializer.validated_data['shipping_address_id']
        notes = serializer.validated_data.get('notes', '')

        # Calculate totals
        subtotal = cart.subtotal
        shipping_cost = 0  # Can be calculated based on address/weight
        tax = subtotal * 0.08  # 8% tax example
        discount = 0  # Apply coupon logic here
        total = subtotal + shipping_cost + tax - discount

        # Create order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            discount=discount,
            total=total,
            notes=notes
        )

        # Create order items and reduce stock
        for cart_item in cart.items.all():
            product = cart_item.product
            variant = cart_item.variant

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                product_name=product.name,
                product_sku=variant.sku if variant else product.sku,
                variant_name=variant.name if variant else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )

            # Reduce stock
            if product.track_inventory:
                if variant:
                    variant.stock_quantity -= cart_item.quantity
                    variant.save()
                else:
                    product.stock_quantity -= cart_item.quantity
                    product.save()

        # Clear cart
        cart.clear()

        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.ActivityType.ORDER_PLACED,
            description=f'Order {order.order_number} placed'
        )

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status=order.status,
            notes='Order created'
        )

        response_serializer = OrderDetailSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, order_number=None):
        """
        Cancel an order.
        """
        order = self.get_object()

        if not order.can_cancel():
            return Response(
                {'error': 'This order cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = order.status
        order.cancel()

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=order.status,
            notes='Order cancelled by customer'
        )

        return Response(
            {'message': 'Order cancelled successfully.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, order_number=None):
        """
        Update order status (admin only).
        """
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = order.status
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        if old_status == new_status:
            return Response(
                {'error': 'New status is same as current status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status

        # Update timestamps based on status
        from django.utils import timezone
        if new_status == Order.Status.PAID:
            order.paid_at = timezone.now()
        elif new_status == Order.Status.SHIPPED:
            order.shipped_at = timezone.now()
        elif new_status == Order.Status.DELIVERED:
            order.delivered_at = timezone.now()

        order.save()

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
            created_by=request.user
        )

        return Response(
            {'message': f'Order status updated to {new_status}.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def history(self, request, order_number=None):
        """
        Get order status history.
        """
        order = self.get_object()
        history = order.status_history.all()
        serializer = OrderStatusHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Get current user's orders.
        """
        orders = Order.objects.filter(user=request.user)
        page = self.paginate_queryset(orders)
        
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

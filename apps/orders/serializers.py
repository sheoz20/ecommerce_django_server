"""
Serializers for the orders app.
"""
from rest_framework import serializers

from apps.catalog.models import Product, ProductVariant
from apps.catalog.serializers import ProductListSerializer

from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress


class ShippingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for shipping addresses.
    """
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'first_name', 'last_name', 'phone_number',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'is_default', 'address_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items.
    """
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'variant_name', 'quantity', 'unit_price', 'total_price'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for order list view.
    """
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'total', 'item_count', 'created_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for order detail view.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'shipping_address', 'subtotal', 'shipping_cost', 'tax',
            'discount', 'total', 'item_count', 'tracking_number',
            'notes', 'items', 'created_at', 'updated_at', 'paid_at',
            'shipped_at', 'delivered_at'
        ]
        read_only_fields = ['order_number', 'user']


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer for creating orders from cart.
    """
    shipping_address_id = serializers.UUIDField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_shipping_address_id(self, value):
        """Validate shipping address belongs to user."""
        user = self.context['request'].user
        try:
            address = ShippingAddress.objects.get(id=value, user=user)
            return address
        except ShippingAddress.DoesNotExist:
            raise serializers.ValidationError("Shipping address not found.")


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating order status.
    """
    status = serializers.ChoiceField(choices=Order.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for order status history.
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'old_status', 'new_status', 'notes',
            'created_by_name', 'created_at'
        ]

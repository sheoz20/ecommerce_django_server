"""
Serializers for the cart app.
"""
from rest_framework import serializers

from apps.catalog.models import Product, ProductVariant
from apps.catalog.serializers import ProductImageSerializer, ProductListSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items.
    """
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    variant_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'variant_id', 'variant_name',
            'quantity', 'unit_price', 'total_price', 'added_at', 'updated_at'
        ]
        read_only_fields = ['added_at', 'updated_at']

    def validate(self, data):
        """Validate cart item data."""
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_id": "Product not found."}
            )

        # Check if product is active
        if product.status != Product.Status.ACTIVE:
            raise serializers.ValidationError(
                {"product_id": "This product is not available."}
            )

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                if variant.product != product:
                    raise serializers.ValidationError(
                        {"variant_id": "Variant does not belong to the selected product."}
                    )
                if not variant.is_active:
                    raise serializers.ValidationError(
                        {"variant_id": "This variant is not available."}
                    )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"variant_id": "Variant not found."}
                )

        # Check stock
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        if product.track_inventory and quantity > available_stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {available_stock} items available in stock."}
            )

        return data


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'subtotal', 'total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart.
    """
    product_id = serializers.UUIDField(required=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, data):
        """Validate add to cart data."""
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_id": "Product not found."}
            )

        if product.status != Product.Status.ACTIVE:
            raise serializers.ValidationError(
                {"product_id": "This product is not available."}
            )

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                if variant.product != product:
                    raise serializers.ValidationError(
                        {"variant_id": "Variant does not belong to the selected product."}
                    )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"variant_id": "Variant not found."}
                )

        # Check stock
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        if product.track_inventory and quantity > available_stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {available_stock} items available in stock."}
            )

        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity.
    """
    quantity = serializers.IntegerField(min_value=1)

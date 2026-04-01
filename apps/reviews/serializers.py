"""
Serializers for the reviews app.
"""
from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Review, ReviewHelpfulness, Wishlist


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_initials = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user_name', 'user_initials', 'rating', 'title',
            'comment', 'images', 'is_verified_purchase', 'is_featured',
            'helpful_count', 'not_helpful_count', 'created_at'
        ]
        read_only_fields = [
            'is_verified_purchase', 'is_featured',
            'helpful_count', 'not_helpful_count'
        ]

    def get_user_initials(self, obj):
        """Get user initials for avatar display."""
        names = obj.user.get_full_name().split()
        if len(names) >= 2:
            return f"{names[0][0]}{names[-1][0]}".upper()
        elif names:
            return names[0][:2].upper()
        return obj.user.email[:2].upper()


class CreateReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.
    """
    class Meta:
        model = Review
        fields = ['product', 'order', 'rating', 'title', 'comment', 'images']

    def validate(self, data):
        """Validate review data."""
        user = self.context['request'].user
        product = data['product']
        
        # Check if user already reviewed this product
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError(
                "You have already reviewed this product."
            )
        
        # Validate order if provided
        order = data.get('order')
        if order:
            if order.user != user:
                raise serializers.ValidationError(
                    "Invalid order for this user."
                )
            if not order.items.filter(product=product).exists():
                raise serializers.ValidationError(
                    "This product is not in the specified order."
                )
        
        return data


class ReviewHelpfulnessSerializer(serializers.ModelSerializer):
    """
    Serializer for review helpfulness votes.
    """
    class Meta:
        model = ReviewHelpfulness
        fields = ['id', 'vote', 'created_at']
        read_only_fields = ['created_at']


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for wishlist items.
    """
    from apps.catalog.serializers import ProductListSerializer
    
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'notes', 'created_at']
        read_only_fields = ['created_at']

    def validate_product_id(self, value):
        """Validate product exists."""
        from apps.catalog.models import Product
        try:
            return Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

    def create(self, validated_data):
        """Create wishlist item."""
        product = validated_data.pop('product_id')
        user = self.context['request'].user
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=user,
            product=product,
            defaults={'notes': validated_data.get('notes', '')}
        )
        
        if not created:
            # Update notes if item already exists
            wishlist_item.notes = validated_data.get('notes', wishlist_item.notes)
            wishlist_item.save()
        
        return wishlist_item

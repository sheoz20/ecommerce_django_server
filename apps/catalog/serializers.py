"""
Serializers for the catalog app.
"""
from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductVariant


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for category tree structure.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            return CategoryTreeSerializer(obj.children.all(), many=True).data
        return []


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for category details.
    """
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'parent_name', 'image', 'is_active', 'created_at'
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'sort_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer for product variants.
    """
    final_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price_adjustment',
            'final_price', 'stock_quantity', 'is_active', 'attributes'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view.
    """
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'short_description',
            'price', 'compare_at_price', 'discount_percentage',
            'primary_image', 'category', 'category_name',
            'average_rating', 'review_count', 'is_featured',
            'status', 'created_at'
        ]

    def get_primary_image(self, obj):
        image = obj.primary_image
        if image:
            return ProductImageSerializer(image).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail view.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description',
            'short_description', 'price', 'compare_at_price',
            'discount_percentage', 'cost_per_item', 'stock_quantity',
            'track_inventory', 'is_in_stock', 'category', 'tags',
            'status', 'is_featured', 'meta_title', 'meta_description',
            'average_rating', 'review_count', 'images', 'variants',
            'created_at', 'updated_at'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products.
    """
    images = ProductImageSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description',
            'short_description', 'price', 'compare_at_price',
            'cost_per_item', 'stock_quantity', 'track_inventory',
            'category', 'tags', 'status', 'is_featured',
            'meta_title', 'meta_description', 'images', 'variants'
        ]
        read_only_fields = ['slug', 'sku']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        
        product = Product.objects.create(**validated_data)
        
        # Create images
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        
        # Create variants
        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
        
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        variants_data = validated_data.pop('variants', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update images if provided
        if images_data is not None:
            instance.images.all().delete()
            for image_data in images_data:
                ProductImage.objects.create(product=instance, **image_data)
        
        # Update variants if provided
        if variants_data is not None:
            instance.variants.all().delete()
            for variant_data in variants_data:
                ProductVariant.objects.create(product=instance, **variant_data)
        
        return instance

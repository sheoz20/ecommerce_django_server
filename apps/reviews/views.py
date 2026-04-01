"""
Views for the reviews app.
"""
from django.db.models import Avg, Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.catalog.models import Product
from apps.users.models import UserActivity

from .models import Review, ReviewHelpfulness, Wishlist
from .serializers import (
    CreateReviewSerializer,
    ReviewHelpfulnessSerializer,
    ReviewSerializer,
    WishlistSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for review operations.
    """
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'vote']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReviewSerializer
        return ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.filter(is_approved=True)
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Filter verified purchases
        verified = self.request.query_params.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified_purchase=True)
        
        return queryset.select_related('user', 'product')

    def perform_create(self, serializer):
        """Create review and log activity."""
        review = serializer.save(user=self.request.user)
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type=UserActivity.ActivityType.REVIEW_ADDED,
            description=f'Review added for {review.product.name}'
        )
        
        return review

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """
        Vote on review helpfulness.
        """
        review = self.get_object()
        vote_type = request.data.get('vote')
        
        if vote_type not in [ReviewHelpfulness.Vote.HELPFUL, ReviewHelpfulness.Vote.NOT_HELPFUL]:
            return Response(
                {'error': 'Invalid vote type. Use "helpful" or "not_helpful".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already voted
        existing_vote = ReviewHelpfulness.objects.filter(
            review=review,
            user=request.user
        ).first()
        
        if existing_vote:
            if existing_vote.vote == vote_type:
                # Remove vote if same type
                existing_vote.delete()
                return Response({'message': 'Vote removed.'})
            else:
                # Change vote type
                existing_vote.vote = vote_type
                existing_vote.save()
                return Response({'message': 'Vote updated.'})
        else:
            # Create new vote
            ReviewHelpfulness.objects.create(
                review=review,
                user=request.user,
                vote=vote_type
            )
            return Response({'message': 'Vote recorded.'})

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        Get current user's reviews.
        """
        reviews = Review.objects.filter(user=request.user)
        page = self.paginate_queryset(reviews)
        
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get review summary for a product.
        """
        product_id = request.query_params.get('product')
        if not product_id:
            return Response(
                {'error': 'product parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = Review.objects.filter(product=product, is_approved=True)
        
        # Calculate rating distribution
        rating_distribution = reviews.values('rating').annotate(
            count=Count('rating')
        ).order_by('-rating')
        
        return Response({
            'average_rating': product.average_rating,
            'total_reviews': product.review_count,
            'rating_distribution': {
                item['rating']: item['count'] for item in rating_distribution
            }
        })


class WishlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for wishlist operations.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggle product in wishlist.
        """
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user,
                product_id=product_id
            )
            wishlist_item.delete()
            return Response({
                'in_wishlist': False,
                'message': 'Product removed from wishlist.'
            })
        except Wishlist.DoesNotExist:
            Wishlist.objects.create(
                user=request.user,
                product_id=product_id,
                notes=request.data.get('notes', '')
            )
            return Response({
                'in_wishlist': True,
                'message': 'Product added to wishlist.'
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Check if products are in wishlist.
        """
        product_ids = request.query_params.getlist('product_ids')
        if not product_ids:
            return Response({})
        
        wishlisted = Wishlist.objects.filter(
            user=request.user,
            product_id__in=product_ids
        ).values_list('product_id', flat=True)
        
        return Response({
            str(pid): pid in wishlisted for pid in product_ids
        })

    @action(detail=False, methods=['post'])
    def move_to_cart(self, request):
        """
        Move wishlist item to cart.
        """
        wishlist_id = request.data.get('wishlist_id')
        if not wishlist_id:
            return Response(
                {'error': 'wishlist_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            wishlist_item = Wishlist.objects.get(
                id=wishlist_id,
                user=request.user
            )
        except Wishlist.DoesNotExist:
            return Response(
                {'error': 'Wishlist item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add to cart
        from apps.cart.models import Cart, CartItem
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=wishlist_item.product,
            variant=None,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Remove from wishlist
        wishlist_item.delete()
        
        return Response({
            'message': 'Product moved to cart.'
        })

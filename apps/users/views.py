"""
Views for the users app.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import UserActivity
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserActivitySerializer,
    UserSerializer,
)
from .utils import send_password_reset_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    API view for user login with JWT.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    API view for user logout (blacklist refresh token).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log logout activity
            UserActivity.objects.create(
                user=request.user,
                activity_type=UserActivity.ActivityType.LOGOUT,
                description='User logged out'
            )
            
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordChangeView(APIView):
    """
    API view for changing password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.ActivityType.PASSWORD_CHANGE,
            description='Password changed successfully'
        )
        
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    """
    API view for requesting password reset.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = str(uuid.uuid4())
        user.reset_password_token = token
        user.reset_password_expire = timezone.now() + timedelta(hours=1)
        user.save()
        
        # Send email
        send_password_reset_email(user, token)
        
        return Response(
            {'message': 'Password reset email sent.'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        user.set_password(serializer.validated_data['new_password'])
        user.reset_password_token = None
        user.reset_password_expire = None
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.ActivityType.PASSWORD_CHANGE,
            description='Password reset completed'
        )
        
        return Response(
            {'message': 'Password reset successful.'},
            status=status.HTTP_200_OK
        )


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user-related operations.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """
        Get or update user profile.
        """
        user = request.user
        
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        
        # Update profile
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['get'])
    def activity(self, request):
        """
        Get user activity history.
        """
        activities = UserActivity.objects.filter(user=request.user)[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Mark user as verified (for admin use or email verification).
        """
        user = request.user
        user.is_verified = True
        user.save()
        return Response({'message': 'User verified successfully.'})

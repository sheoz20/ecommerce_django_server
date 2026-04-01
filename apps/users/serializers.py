"""
Serializers for the users app.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserActivity, UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'profile_picture', 'address_line_1',
            'address_line_2', 'city', 'state', 'postal_code',
            'country', 'newsletter_subscribed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    """
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_verified', 'date_joined', 'profile'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Log user registration activity
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.ActivityType.PROFILE_UPDATE,
            description='User account created'
        )
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = UserSerializer(self.user).data
        
        # Log login activity
        request = self.context.get('request')
        UserActivity.objects.create(
            user=self.user,
            activity_type=UserActivity.ActivityType.LOGIN,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )
        
        return data
    
    def _get_client_ip(self, request):
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        
        # Validate token
        try:
            user = User.objects.get(
                reset_password_token=attrs['token'],
                reset_password_expire__gt=timezone.now()
            )
            self.user = user
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"token": "Invalid or expired token."}
            )
        
        return attrs


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for user activity.
    """
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'description', 'ip_address', 'created_at']
        read_only_fields = ['id', 'ip_address', 'created_at']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        
        # Update profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        # Log activity
        UserActivity.objects.create(
            user=instance,
            activity_type=UserActivity.ActivityType.PROFILE_UPDATE,
            description='Profile information updated'
        )
        
        return instance

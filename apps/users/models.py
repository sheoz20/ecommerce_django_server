"""
User models for the e-commerce application.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the unique identifier.
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        CUSTOMER = 'customer', _('Customer')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    
    # Status fields
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('verified'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    # Password reset fields
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_expire = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    profile_picture = models.ImageField(
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True
    )
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='US')
    
    # Preferences
    newsletter_subscribed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.email}'s Profile"


class UserActivity(models.Model):
    """
    Track user activity for analytics and security.
    """
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        ORDER_PLACED = 'order_placed', _('Order Placed')
        REVIEW_ADDED = 'review_added', _('Review Added')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices
    )
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"

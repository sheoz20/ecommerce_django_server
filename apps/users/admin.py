"""
Admin configuration for the users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserActivity, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for user profile.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin configuration for CustomUser model.
    """
    inlines = (UserProfileInline,)
    
    list_display = [
        'email', 'first_name', 'last_name', 'role',
        'is_active', 'is_verified', 'date_joined'
    ]
    list_filter = ['role', 'is_active', 'is_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserActivity model.
    """
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['user', 'activity_type', 'description', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ['user', 'phone_number', 'city', 'country', 'created_at']
    list_filter = ['country', 'newsletter_subscribed']
    search_fields = ['user__email', 'phone_number', 'city']
    readonly_fields = ['created_at', 'updated_at']

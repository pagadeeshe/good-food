from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with enhanced functionality for managing 10,000+ users.
    """
    
    list_display = ['student_id', 'email', 'get_full_name', 'role', 'is_active', 'last_login', 'created_at']
    list_filter = ['role', 'is_active', 'created_at', 'last_login']
    search_fields = ['email', 'student_id', 'first_name', 'last_name']
    ordering = ['-created_at']
    list_per_page = 50
    
    # Field groupings
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('student_id', 'first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'student_id', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    # Custom methods
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    # Bulk actions
    actions = ['make_active', 'make_inactive', 'promote_to_admin', 'demote_to_user']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    make_active.short_description = "Activate selected users"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    make_inactive.short_description = "Deactivate selected users"
    
    def promote_to_admin(self, request, queryset):
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} users were promoted to admin.')
    promote_to_admin.short_description = "Promote to admin"
    
    def demote_to_user(self, request, queryset):
        updated = queryset.update(role='user')
        self.message_user(request, f'{updated} users were demoted to regular user.')
    demote_to_user.short_description = "Demote to user"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for user profiles.
    """
    
    list_display = ['user', 'total_orders', 'last_order_date', 'created_at']
    list_filter = ['last_order_date', 'created_at']
    search_fields = ['user__email', 'user__student_id', 'user__first_name', 'user__last_name']
    readonly_fields = ['total_orders', 'last_order_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('dietary_preferences', 'notification_preferences')
        }),
        ('Statistics', {
            'fields': ('total_orders', 'last_order_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

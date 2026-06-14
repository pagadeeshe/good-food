from rest_framework import serializers
from django.db.models import Count, Sum
from django.utils import timezone
from .models import User, UserProfile


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (admin view).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    total_orders = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'employee_id', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'is_active', 'last_login', 
            'date_joined', 'total_orders'
        ]
    
    def get_total_orders(self, obj):
        """Get total orders for the user."""
        return obj.orders.filter(status__in=['confirmed', 'completed']).count()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = serializers.SerializerMethodField()
    order_statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'employee_id', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'role', 'is_active', 
            'last_login', 'date_joined', 'profile', 'order_statistics'
        ]
    
    def get_profile(self, obj):
        """Get user profile data."""
        try:
            profile = obj.profile
            return {
                'dietary_preferences': profile.dietary_preferences,
                'notification_preferences': profile.notification_preferences,
                'total_orders': profile.total_orders,
                'last_order_date': profile.last_order_date,
            }
        except UserProfile.DoesNotExist:
            return None
    
    def get_order_statistics(self, obj):
        """Get user order statistics."""
        from apps.orders.models import Order, OrderItem
        from django.db.models import Count, Sum
        
        orders = obj.orders.filter(status__in=['confirmed', 'completed'])
        
        stats = {
            'total_orders': orders.count(),
            'total_items': orders.aggregate(Sum('total_items'))['total_items'] or 0,
            'current_month_orders': orders.filter(
                order_date__year=timezone.now().year,
                order_date__month=timezone.now().month
            ).count()
        }
        
        return stats


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users (admin only).
    """
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'employee_id', 'email', 'first_name', 'last_name', 
            'phone_number', 'role', 'password'
        ]
    
    def validate_employee_id(self, value):
        """Validate employee ID format and uniqueness."""
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError('Employee ID already exists.')
        return value.upper()
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value.lower()
    
    def create(self, validated_data):
        """Create new user with profile."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information (admin only).
    """
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 
            'role', 'is_active'
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for users to update their own profile.
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile details.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'dietary_preferences', 'notification_preferences',
            'total_orders', 'last_order_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_orders', 'last_order_date', 'created_at', 'updated_at']


class BulkUserActionSerializer(serializers.Serializer):
    """
    Serializer for bulk user actions (admin only).
    """
    ACTION_CHOICES = [
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('promote_to_admin', 'Promote to Admin'),
        ('demote_to_user', 'Demote to User'),
    ]
    
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    
    def validate_user_ids(self, value):
        """Validate that all user IDs exist."""
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError('Some user IDs do not exist.')
        return value
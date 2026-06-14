from rest_framework import serializers
from django.utils import timezone
from django.core.cache import cache
from .models import WeeklyMenu, DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer for menu items.
    """
    can_be_ordered = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'category', 'is_available',
            'max_quantity_per_user', 'total_ordered', 'unique_orders',
            'sort_order', 'can_be_ordered'
        ]
        read_only_fields = ['total_ordered', 'unique_orders']


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating menu items.
    """
    
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'category', 'is_available',
            'max_quantity_per_user', 'sort_order'
        ]


class DailyMenuSerializer(serializers.ModelSerializer):
    """
    Serializer for daily menus.
    """
    menu_items = MenuItemSerializer(many=True, read_only=True)
    weekday_name = serializers.CharField(source='get_weekday_display', read_only=True)
    is_ordering_open = serializers.BooleanField(read_only=True)
    orders_closed_reason = serializers.CharField(read_only=True)
    
    class Meta:
        model = DailyMenu
        fields = [
            'id', 'date', 'weekday', 'weekday_name', 'status', 
            'cutoff_time', 'description', 'total_orders', 
            'total_items_ordered', 'is_ordering_open', 
            'orders_closed_reason', 'menu_items', 'created_at'
        ]
        read_only_fields = ['weekday', 'total_orders', 'total_items_ordered']


class DailyMenuCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating daily menus.
    """
    menu_items = MenuItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = DailyMenu
        fields = [
            'date', 'status', 'cutoff_time', 'description', 
            'weekly_menu', 'menu_items'
        ]
    
    def create(self, validated_data):
        menu_items_data = validated_data.pop('menu_items', [])
        validated_data['created_by'] = self.context['request'].user
        
        daily_menu = DailyMenu.objects.create(**validated_data)
        
        # Create menu items
        for item_data in menu_items_data:
            MenuItem.objects.create(daily_menu=daily_menu, **item_data)
        
        return daily_menu


class TodayMenuSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for today's menu (frequently accessed).
    """
    available_items = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyMenu
        fields = [
            'id', 'date', 'status', 'cutoff_time', 'description',
            'is_ordering_open', 'orders_closed_reason', 'available_items'
        ]
    
    def get_available_items(self, obj):
        """Get only available items for ordering."""
        items = obj.menu_items.filter(is_available=True).order_by('sort_order', 'name')
        return MenuItemSerializer(items, many=True).data


class WeeklyMenuSerializer(serializers.ModelSerializer):
    """
    Serializer for weekly menus.
    """
    daily_menus = DailyMenuSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WeeklyMenu
        fields = [
            'id', 'name', 'week_start_date', 'description', 
            'is_active', 'created_by_name', 'created_at',
            'daily_menus'
        ]


class WeeklyMenuCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating weekly menus.
    """
    
    class Meta:
        model = WeeklyMenu
        fields = ['name', 'week_start_date', 'description', 'is_active']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return WeeklyMenu.objects.create(**validated_data)


class MenuTemplateItemSerializer(serializers.ModelSerializer):
    """
    Serializer for menu template items.
    """
    
    class Meta:
        model = MenuTemplateItem
        fields = [
            'id', 'name', 'description', 'category', 
            'max_quantity_per_user', 'sort_order'
        ]


class MenuTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for menu templates.
    """
    template_items = MenuTemplateItemSerializer(many=True, read_only=True)
    weekday_name = serializers.CharField(source='get_weekday_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = MenuTemplate
        fields = [
            'id', 'name', 'description', 'weekday', 'weekday_name',
            'is_active', 'usage_count', 'created_by_name', 
            'template_items', 'created_at'
        ]


class MenuTemplateCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating menu templates.
    """
    template_items = MenuTemplateItemSerializer(many=True, required=False)
    
    class Meta:
        model = MenuTemplate
        fields = [
            'name', 'description', 'weekday', 'is_active', 'template_items'
        ]
    
    def create(self, validated_data):
        template_items_data = validated_data.pop('template_items', [])
        validated_data['created_by'] = self.context['request'].user
        
        template = MenuTemplate.objects.create(**validated_data)
        
        # Create template items
        for item_data in template_items_data:
            MenuTemplateItem.objects.create(template=template, **item_data)
        
        return template


class MenuItemBulkUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk updating menu items.
    """
    ACTION_CHOICES = [
        ('make_available', 'Make Available'),
        ('make_unavailable', 'Make Unavailable'),
        ('update_quantity', 'Update Max Quantity'),
    ]
    
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    max_quantity = serializers.IntegerField(required=False, min_value=1, max_value=20)
    
    def validate(self, attrs):
        action = attrs.get('action')
        max_quantity = attrs.get('max_quantity')
        
        if action == 'update_quantity' and not max_quantity:
            raise serializers.ValidationError(
                'max_quantity is required when action is update_quantity'
            )
        
        return attrs


class DailyMenuFromTemplateSerializer(serializers.Serializer):
    """
    Serializer for creating daily menu from template.
    """
    template_id = serializers.IntegerField()
    date = serializers.DateField()
    cutoff_time = serializers.TimeField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_template_id(self, value):
        """Validate template exists and is active."""
        try:
            template = MenuTemplate.objects.get(id=value, is_active=True)
        except MenuTemplate.DoesNotExist:
            raise serializers.ValidationError('Template not found or inactive.')
        return value
    
    def validate_date(self, value):
        """Validate date is not in the past and doesn't already have a menu."""
        if value < timezone.now().date():
            raise serializers.ValidationError('Cannot create menu for past dates.')
        
        if DailyMenu.objects.filter(date=value).exists():
            raise serializers.ValidationError('Menu already exists for this date.')
        
        return value


class MenuStatisticsSerializer(serializers.Serializer):
    """
    Serializer for menu statistics.
    """
    total_menus = serializers.IntegerField()
    published_menus = serializers.IntegerField()
    draft_menus = serializers.IntegerField()
    total_items = serializers.IntegerField()
    most_popular_items = serializers.ListField()
    recent_menus = serializers.ListField()
    upcoming_menus = serializers.ListField()
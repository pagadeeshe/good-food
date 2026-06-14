from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_name', 'item_category', 'quantity', 'menu_item']


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    meal_type = serializers.CharField(source='daily_menu.meal_type', read_only=True)
    meal_type_display = serializers.CharField(source='daily_menu.get_meal_type_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_date', 'meal_type', 'meal_type_display', 'status', 'total_items',
            'notes', 'created_at', 'updated_at', 'order_items',
        ]


class AdminOrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='user.employee_id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    meal_type = serializers.CharField(source='daily_menu.meal_type', read_only=True)
    meal_type_display = serializers.CharField(source='daily_menu.get_meal_type_display', read_only=True)
    menu_date = serializers.DateField(source='daily_menu.date', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_name', 'employee_id', 'user_email', 'menu_date',
            'order_date', 'meal_type', 'meal_type_display', 'status', 'total_items',
            'notes', 'created_at', 'order_items',
        ]


class PlaceOrderItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class PlaceOrderSerializer(serializers.Serializer):
    meal_type = serializers.ChoiceField(choices=['lunch', 'dinner'], required=False, default='lunch')
    items = PlaceOrderItemSerializer(many=True, allow_empty=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

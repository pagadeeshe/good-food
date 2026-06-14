from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import CanPlaceOrder, CanViewReports, IsOwnerOrAdmin
from apps.authentication.utils import is_authorized_admin
from apps.menu.constants import MEAL_TYPES, is_valid_meal_type
from apps.menu.models import DailyMenu, MenuItem
from apps.menu.services import (
    get_ordering_target_date,
    get_today_published_menu,
    get_today_published_menus,
    parse_meal_type,
    serialize_menu_for_api,
    user_ordering_state,
)

from .models import Order, OrderItem
from .serializers import AdminOrderSerializer, OrderSerializer, PlaceOrderSerializer
from .services import get_daily_order_totals


def _order_for_menu(user, daily_menu):
    if not daily_menu:
        return None
    return (
        Order.objects.filter(user=user, daily_menu=daily_menu)
        .exclude(status='cancelled')
        .prefetch_related('order_items')
        .first()
    )


class TodayOrderView(APIView):
    """Get or place orders for today's lunch and dinner menus."""

    permission_classes = [CanPlaceOrder]

    def get(self, request):
        meal_filter = request.query_params.get('meal')
        if meal_filter:
            if not is_valid_meal_type(meal_filter):
                return Response({'error': 'Invalid meal type. Use lunch or dinner.'}, status=400)
            daily_menu = get_today_published_menu(meal_filter)
            order = _order_for_menu(request.user, daily_menu)
            return Response({
                'menu': serialize_menu_for_api(daily_menu, order),
                'order': OrderSerializer(order).data if order else None,
            })

        menus = get_today_published_menus()
        result = {}
        for meal_type in MEAL_TYPES:
            daily_menu = menus.get(meal_type)
            order = _order_for_menu(request.user, daily_menu)
            result[meal_type] = {
                'menu': serialize_menu_for_api(daily_menu, order),
                'order': OrderSerializer(order).data if order else None,
            }
        return Response(result)

    def post(self, request):
        meal_type = parse_meal_type(request.data.get('meal_type'))
        daily_menu = get_today_published_menu(meal_type)
        if not daily_menu:
            label = 'lunch' if meal_type == 'lunch' else 'dinner'
            target = get_ordering_target_date()
            return Response(
                {
                    'error': (
                        f'No published {label} menu for '
                        f'{target.strftime("%A, %d %b")}.'
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        existing = _order_for_menu(request.user, daily_menu)
        can_order, closed_reason, user_has_ordered = user_ordering_state(daily_menu, existing)
        if user_has_ordered:
            meal_label = daily_menu.get_meal_type_display().lower()
            return Response(
                {
                    'error': (
                        f'You already placed your {meal_label} order for this menu. '
                        'You can order again when the next menu is published.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not can_order:
            return Response(
                {'error': closed_reason or 'Ordering is closed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data['items']
        notes = serializer.validated_data.get('notes', '')
        today = timezone.localdate()

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                daily_menu=daily_menu,
                order_date=today,
                status='confirmed',
                notes=notes,
            )
            total = 0
            for row in items_data:
                menu_item = get_object_or_404(
                    MenuItem, id=row['menu_item_id'], daily_menu=daily_menu, is_available=True,
                )
                if row['quantity'] > menu_item.max_quantity_per_user:
                    return Response(
                        {'error': f'Maximum {menu_item.max_quantity_per_user} allowed for {menu_item.name}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    item_name=menu_item.name,
                    item_category=menu_item.category,
                    quantity=row['quantity'],
                )
                total += row['quantity']

            order.total_items = total
            order.notes = notes
            order.status = 'confirmed'
            order.save(update_fields=['total_items', 'notes', 'status', 'updated_at'])

        order.refresh_from_db()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class AdminOrdersListView(generics.ListAPIView):
    """List all student orders with names and item quantities (admin only)."""

    serializer_class = AdminOrderSerializer
    permission_classes = [CanViewReports]

    def get_queryset(self):
        qs = (
            Order.objects.exclude(status='cancelled')
            .select_related('user', 'daily_menu')
            .prefetch_related('order_items')
        )

        meal_type = self.request.query_params.get('meal')
        if meal_type and is_valid_meal_type(meal_type):
            qs = qs.filter(daily_menu__meal_type=meal_type)

        if self.request.query_params.get('all') == '1':
            return qs.order_by('-daily_menu__date', 'daily_menu__meal_type', 'user__first_name')

        date_param = self.request.query_params.get('date')
        if date_param:
            try:
                menu_date = timezone.datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                menu_date = get_ordering_target_date()
        else:
            menu_date = get_ordering_target_date()

        return qs.filter(daily_menu__date=menu_date).order_by(
            'daily_menu__meal_type', 'user__first_name', 'user__last_name',
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        menu_date = request.query_params.get('date')
        if request.query_params.get('all') != '1' and not menu_date:
            menu_date = get_ordering_target_date().isoformat()
        return Response({
            'menu_date': menu_date,
            'show_all': request.query_params.get('all') == '1',
            'count': len(serializer.data),
            'orders': serializer.data,
        })


class MyOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .exclude(status='cancelled')
            .select_related('daily_menu')
            .prefetch_related('order_items')
            .order_by('-order_date', 'daily_menu__meal_type')
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        qs = Order.objects.prefetch_related('order_items').select_related('daily_menu')
        if is_authorized_admin(self.request.user):
            return qs
        return qs.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([CanViewReports])
def daily_order_totals(request, year, month, day):
    report_date = timezone.datetime(year, month, day).date()
    meal_type = request.query_params.get('meal')
    if meal_type and not is_valid_meal_type(meal_type):
        return Response({'error': 'Invalid meal type. Use lunch or dinner.'}, status=400)

    totals = get_daily_order_totals(report_date, meal_type=meal_type)
    daily_menu = None
    if meal_type:
        daily_menu = DailyMenu.objects.filter(date=report_date, meal_type=meal_type).first()
    return Response({
        'date': report_date,
        'meal_type': meal_type,
        'daily_menu_status': daily_menu.status if daily_menu else None,
        **totals,
    })


@api_view(['GET'])
@permission_classes([CanViewReports])
def today_order_totals(request):
    meal_type = request.query_params.get('meal')
    if meal_type and not is_valid_meal_type(meal_type):
        return Response({'error': 'Invalid meal type. Use lunch or dinner.'}, status=400)

    today = timezone.localdate()
    ordering_for = get_ordering_target_date()
    if meal_type:
        return daily_order_totals(request, ordering_for.year, ordering_for.month, ordering_for.day)

    return Response({
        'date': ordering_for,
        'ordering_for_date': ordering_for,
        'lunch': get_daily_order_totals(ordering_for, meal_type='lunch'),
        'dinner': get_daily_order_totals(ordering_for, meal_type='dinner'),
    })

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import CanPlaceOrder, CanViewReports, IsOwnerOrAdmin
from apps.authentication.utils import is_authorized_admin
from apps.menu.models import DailyMenu, MenuItem
from apps.menu.services import get_today_published_menu

from .models import Order, OrderItem
from .serializers import OrderSerializer, PlaceOrderSerializer
from .services import get_daily_order_totals


class TodayOrderView(APIView):
    """Get or place the user's order for today's published menu."""

    permission_classes = [CanPlaceOrder]

    def get(self, request):
        daily_menu = get_today_published_menu()
        if not daily_menu:
            return Response({'menu': None, 'order': None})

        order = (
            Order.objects.filter(user=request.user, daily_menu=daily_menu)
            .exclude(status='cancelled')
            .prefetch_related('order_items')
            .first()
        )
        return Response({
            'menu': {
                'id': daily_menu.id,
                'date': daily_menu.date,
                'is_ordering_open': daily_menu.is_ordering_open,
                'orders_closed_reason': daily_menu.orders_closed_reason,
                'items': [
                    {
                        'id': item.id,
                        'name': item.name,
                        'category': item.category,
                        'max_quantity_per_user': item.max_quantity_per_user,
                        'quantity': next(
                            (oi.quantity for oi in order.order_items.all()
                             if order and oi.menu_item_id == item.id),
                            0,
                        ) if order else 0,
                    }
                    for item in daily_menu.menu_items.filter(is_available=True).order_by('sort_order', 'name')
                ],
            },
            'order': OrderSerializer(order).data if order else None,
        })

    def post(self, request):
        daily_menu = get_today_published_menu()
        if not daily_menu:
            return Response({'error': 'No published menu for today.'}, status=status.HTTP_404_NOT_FOUND)
        if not daily_menu.is_ordering_open:
            return Response(
                {'error': daily_menu.orders_closed_reason or 'Ordering is closed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data['items']
        notes = serializer.validated_data.get('notes', '')
        today = timezone.localdate()

        with transaction.atomic():
            order, _ = Order.objects.get_or_create(
                user=request.user,
                daily_menu=daily_menu,
                defaults={'order_date': today, 'status': 'confirmed', 'notes': notes},
            )
            if order.status == 'cancelled':
                order.status = 'confirmed'

            order.order_items.all().delete()
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


class MyOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .exclude(status='cancelled')
            .select_related('daily_menu')
            .prefetch_related('order_items')
            .order_by('-order_date')
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        qs = Order.objects.prefetch_related('order_items')
        if is_authorized_admin(self.request.user):
            return qs
        return qs.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([CanViewReports])
def daily_order_totals(request, year, month, day):
    """Kitchen report: item quantities only (no user names)."""
    report_date = timezone.datetime(year, month, day).date()
    totals = get_daily_order_totals(report_date)
    daily_menu = DailyMenu.objects.filter(date=report_date).first()
    return Response({
        'date': report_date,
        'daily_menu_status': daily_menu.status if daily_menu else None,
        **totals,
    })


@api_view(['GET'])
@permission_classes([CanViewReports])
def today_order_totals(request):
    return daily_order_totals(request, *timezone.localdate().timetuple()[:3])

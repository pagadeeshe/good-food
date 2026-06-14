from django.db.models import Sum

from .models import Order, OrderItem


def get_daily_order_totals(menu_date):
    """
    Aggregate today's orders for kitchen prep.
    Returns quantities per item only — no user names.
    """
    active_statuses = ['confirmed', 'completed', 'pending']

    orders = Order.objects.filter(
        order_date=menu_date,
        status__in=active_statuses,
    )

    item_rows = (
        OrderItem.objects.filter(
            order__order_date=menu_date,
            order__status__in=active_statuses,
        )
        .values('item_name', 'item_category')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity', 'item_name')
    )

    total_items = sum(row['total_quantity'] for row in item_rows)
    total_users = orders.values('user').distinct().count()
    total_orders = orders.count()

    return {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_items': total_items,
        'items': list(item_rows),
    }

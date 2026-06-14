from django.db.models import Sum

from .models import Order, OrderItem


def get_daily_order_totals(menu_date, meal_type=None):
    """
    Aggregate orders for kitchen prep (quantities only — no user names).
    Optionally filter by lunch or dinner.
    """
    active_statuses = ['confirmed', 'completed', 'pending']

    orders = Order.objects.filter(
        daily_menu__date=menu_date,
        status__in=active_statuses,
    )
    if meal_type:
        orders = orders.filter(daily_menu__meal_type=meal_type)

    item_rows = (
        OrderItem.objects.filter(
            order__daily_menu__date=menu_date,
            order__status__in=active_statuses,
        )
        .values('item_name', 'item_category')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity', 'item_name')
    )
    if meal_type:
        item_rows = item_rows.filter(order__daily_menu__meal_type=meal_type)

    item_list = list(item_rows)
    total_items = sum(row['total_quantity'] for row in item_list)
    total_users = orders.values('user').distinct().count()
    total_orders = orders.count()

    return {
        'meal_type': meal_type,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_items': total_items,
        'items': item_list,
    }

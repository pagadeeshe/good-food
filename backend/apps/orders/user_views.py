from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.authentication.utils import is_authorized_admin
from apps.menu.models import DailyMenu, MenuItem
from apps.menu.services import get_today_published_menu

from .models import Order, OrderItem


@login_required
def today_menu_view(request):
    """Show today's published menu and allow ordering."""
    if is_authorized_admin(request.user):
        return redirect('admin_portal')

    today = timezone.localdate()
    daily_menu = get_today_published_menu()

    existing_order = None
    order_items = {}
    if daily_menu:
        existing_order = Order.objects.filter(
            user=request.user,
            daily_menu=daily_menu,
        ).exclude(status='cancelled').prefetch_related('order_items').first()
        if existing_order:
            for oi in existing_order.order_items.all():
                order_items[oi.menu_item_id] = oi.quantity

    if request.method == 'POST' and daily_menu:
        if not daily_menu.is_ordering_open:
            messages.error(request, daily_menu.orders_closed_reason or 'Ordering is closed.')
            return redirect('today_menu')

        quantities = {}
        for item in daily_menu.menu_items.filter(is_available=True):
            raw = request.POST.get(f'qty_{item.id}', '0')
            try:
                qty = max(0, int(raw))
            except ValueError:
                qty = 0
            if qty > item.max_quantity_per_user:
                messages.error(
                    request,
                    f'Maximum {item.max_quantity_per_user} allowed for {item.name}.',
                )
                return redirect('today_menu')
            if qty > 0:
                quantities[item.id] = qty

        if not quantities:
            messages.error(request, 'Please select at least one item.')
            return redirect('today_menu')

        notes = request.POST.get('notes', '').strip()

        with transaction.atomic():
            order, _ = Order.objects.get_or_create(
                user=request.user,
                daily_menu=daily_menu,
                defaults={
                    'order_date': today,
                    'status': 'confirmed',
                    'notes': notes,
                },
            )
            if order.status == 'cancelled':
                order.status = 'confirmed'
                order.notes = notes
                order.save(update_fields=['status', 'notes', 'updated_at'])

            order.order_items.all().delete()
            total = 0
            for item_id, qty in quantities.items():
                menu_item = get_object_or_404(MenuItem, id=item_id, daily_menu=daily_menu)
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=qty,
                )
                total += qty

            order.total_items = total
            order.notes = notes
            order.status = 'confirmed'
            order.save(update_fields=['total_items', 'notes', 'status', 'updated_at'])

        messages.success(request, 'Your order has been placed successfully!')
        return redirect('today_menu')

    menu_items = []
    if daily_menu:
        for item in daily_menu.menu_items.filter(is_available=True).order_by('sort_order', 'name'):
            item.current_qty = order_items.get(item.id, 0)
            menu_items.append(item)

    return render(request, 'user/today_menu.html', {
        'today': today,
        'daily_menu': daily_menu,
        'menu_items': menu_items,
        'existing_order': existing_order,
        'order_items': order_items,
        'ordering_open': daily_menu.is_ordering_open if daily_menu else False,
        'closed_reason': daily_menu.orders_closed_reason if daily_menu else None,
    })


@login_required
def my_orders_view(request):
    if is_authorized_admin(request.user):
        return redirect('admin_portal')

    orders = (
        Order.objects.filter(user=request.user)
        .exclude(status='cancelled')
        .select_related('daily_menu')
        .prefetch_related('order_items')
        .order_by('-order_date')[:30]
    )

    return render(request, 'user/my_orders.html', {'orders': orders})

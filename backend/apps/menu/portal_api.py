"""Admin portal REST endpoints (replaces HTML admin views)."""

from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.authentication.permissions import IsPortalAdmin
from apps.orders.services import get_daily_order_totals

from .models import DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem
from .serializers import DailyMenuSerializer, MenuTemplateSerializer
from .services import (
    WEEKDAYS,
    apply_standard_menu,
    daily_menu_for_date,
    ensure_weekly_templates,
    get_weekday_template,
    menu_preview_for_date,
    seed_sample_weekly_menus,
    template_items_list,
    upcoming_dates,
)


@api_view(['GET'])
@permission_classes([IsPortalAdmin])
def admin_dashboard(request):
    ensure_weekly_templates(request.user)
    seed_sample_weekly_menus(request.user)
    today = timezone.localdate()
    today_menu, today_items, source = menu_preview_for_date(today)
    return Response({
        'today': today,
        'today_menu': DailyMenuSerializer(today_menu).data if today_menu else None,
        'today_items': [
            {'name': i.name, 'category': getattr(i, 'category', 'main')}
            for i in today_items
        ],
        'today_source': source,
        'order_totals': get_daily_order_totals(today),
        'weekday_count': MenuTemplate.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
@permission_classes([IsPortalAdmin])
def weekly_templates(request):
    ensure_weekly_templates(request.user)
    data = []
    for weekday, day_name in WEEKDAYS:
        template = get_weekday_template(weekday)
        items = template_items_list(template)
        data.append({
            'weekday': weekday,
            'day_name': day_name,
            'template': MenuTemplateSerializer(template).data if template else None,
            'item_count': len(items),
        })
    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsPortalAdmin])
def weekday_template_detail(request, weekday):
    if weekday < 0 or weekday > 6:
        return Response({'error': 'Invalid weekday'}, status=status.HTTP_400_BAD_REQUEST)

    ensure_weekly_templates(request.user)
    template = get_object_or_404(MenuTemplate, weekday=weekday, is_active=True)

    if request.method == 'GET':
        return Response(MenuTemplateSerializer(template).data)

    action = request.data.get('action')
    if action == 'add_item':
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'error': 'Item name is required'}, status=status.HTTP_400_BAD_REQUEST)
        max_sort = template.template_items.order_by('-sort_order').first()
        MenuTemplateItem.objects.create(
            template=template,
            name=name,
            category=request.data.get('category', 'main'),
            sort_order=(max_sort.sort_order + 1) if max_sort else 0,
        )
    elif action == 'delete_item':
        item = template.template_items.filter(id=request.data.get('item_id')).first()
        if item:
            item.delete()
    elif action == 'update_description':
        template.description = (request.data.get('description') or '').strip()
        template.save(update_fields=['description', 'updated_at'])

    template.refresh_from_db()
    return Response(MenuTemplateSerializer(template).data)


@api_view(['GET'])
@permission_classes([IsPortalAdmin])
def upcoming_daily_menus(request):
    ensure_weekly_templates(request.user)
    days = []
    for menu_date in upcoming_dates(14):
        daily, items, source = menu_preview_for_date(menu_date)
        days.append({
            'date': menu_date,
            'day_name': menu_date.strftime('%A'),
            'daily_menu': DailyMenuSerializer(daily).data if daily else None,
            'item_count': len(items),
            'source': source,
        })
    return Response(days)


@api_view(['GET', 'POST'])
@permission_classes([IsPortalAdmin])
def daily_menu_detail(request, year, month, day):
    menu_date = date(year, month, day)
    day_name = menu_date.strftime('%A')

    if request.method == 'GET':
        daily_menu = daily_menu_for_date(menu_date)
        custom_items = list(daily_menu.menu_items.order_by('sort_order', 'name')) if daily_menu else []
        template = get_weekday_template(menu_date.weekday())
        standard_items = template_items_list(template)
        return Response({
            'menu_date': menu_date,
            'day_name': day_name,
            'daily_menu': DailyMenuSerializer(daily_menu).data if daily_menu else None,
            'custom_items': [
                {'id': i.id, 'name': i.name, 'category': i.category, 'sort_order': i.sort_order}
                for i in custom_items
            ],
            'standard_items': [
                {'name': i.name, 'category': i.category}
                for i in standard_items
            ],
            'using_standard': not custom_items and bool(standard_items),
        })

    action = request.data.get('action')
    daily_menu = daily_menu_for_date(menu_date)
    template = get_weekday_template(menu_date.weekday())
    standard_items = template_items_list(template)

    if action == 'add_item':
        if not daily_menu:
            daily_menu, err = apply_standard_menu(menu_date, request.user, publish=False)
            if err and not daily_menu:
                daily_menu = DailyMenu.objects.create(
                    date=menu_date, created_by=request.user, status='draft',
                    description=f'Custom menu for {day_name}',
                )
        name = (request.data.get('name') or '').strip()
        if name:
            MenuItem.objects.create(
                daily_menu=daily_menu,
                name=name,
                category=request.data.get('category', 'main'),
                sort_order=daily_menu.menu_items.count(),
            )

    elif action == 'delete_item':
        if daily_menu:
            item = daily_menu.menu_items.filter(id=request.data.get('item_id')).first()
            if item:
                item.delete()

    elif action == 'publish':
        if not daily_menu:
            daily_menu, err = apply_standard_menu(menu_date, request.user, publish=True)
            if err:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not daily_menu.menu_items.exists() and not standard_items:
                return Response({'error': 'No menu items to publish.'}, status=status.HTTP_400_BAD_REQUEST)
            daily_menu.status = 'published'
            daily_menu.save(update_fields=['status', 'updated_at'])

    elif action == 'unpublish':
        if daily_menu:
            daily_menu.status = 'draft'
            daily_menu.save(update_fields=['status', 'updated_at'])

    elif action == 'reset_to_standard':
        if template and template.template_items.exists():
            if not daily_menu:
                daily_menu, _ = apply_standard_menu(menu_date, request.user, publish=False)
            else:
                from .services import copy_template_items_to_daily_menu
                copy_template_items_to_daily_menu(template, daily_menu)
                daily_menu.description = f'Standard {day_name} menu'
                daily_menu.status = 'draft'
                daily_menu.save(update_fields=['description', 'status', 'updated_at'])

    daily_menu = daily_menu_for_date(menu_date)
    return Response({
        'daily_menu': DailyMenuSerializer(daily_menu).data if daily_menu else None,
        'message': f'Action {action} completed',
    })

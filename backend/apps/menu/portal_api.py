"""Admin portal REST endpoints."""

from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.authentication.permissions import IsPortalAdmin
from apps.menu.constants import MEAL_DINNER, MEAL_LUNCH, MEAL_TYPES, is_valid_meal_type
from apps.orders.services import get_daily_order_totals

from .models import DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem
from .serializers import DailyMenuSerializer, MenuTemplateSerializer
from .services import (
    WEEKDAYS,
    apply_standard_menu,
    daily_menu_for_date,
    ensure_weekly_templates,
    get_ordering_target_date,
    get_weekday_template,
    menu_preview_for_date,
    publish_daily_menu,
    seed_sample_weekly_menus,
    template_items_list,
    unpublish_daily_menu,
    upcoming_dates,
)


def _validate_meal(meal_type):
    if not is_valid_meal_type(meal_type):
        return Response({'error': 'Invalid meal type. Use lunch or dinner.'}, status=400)
    return None


@api_view(['GET'])
@permission_classes([IsPortalAdmin])
def admin_dashboard(request):
    ensure_weekly_templates(request.user)
    seed_sample_weekly_menus(request.user)
    today = timezone.localdate()
    ordering_for = get_ordering_target_date()
    menus = {}
    for meal_type in MEAL_TYPES:
        daily, items, source = menu_preview_for_date(ordering_for, meal_type)
        menus[meal_type] = {
            'daily_menu': DailyMenuSerializer(daily).data if daily else None,
            'items': [{'name': i.name, 'category': getattr(i, 'category', 'main')} for i in items],
            'source': source,
            'order_totals': get_daily_order_totals(ordering_for, meal_type=meal_type),
        }
    return Response({
        'today': today,
        'ordering_for_date': ordering_for,
        'menus': menus,
        'weekday_count': MenuTemplate.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
@permission_classes([IsPortalAdmin])
def weekly_templates(request):
    ensure_weekly_templates(request.user)
    data = []
    for weekday, day_name in WEEKDAYS:
        for meal_type in MEAL_TYPES:
            template = get_weekday_template(weekday, meal_type)
            items = template_items_list(template)
            data.append({
                'weekday': weekday,
                'day_name': day_name,
                'meal_type': meal_type,
                'template': MenuTemplateSerializer(template).data if template else None,
                'item_count': len(items),
            })
    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsPortalAdmin])
def weekday_template_detail(request, weekday, meal_type):
    err = _validate_meal(meal_type)
    if err:
        return err
    if weekday < 0 or weekday > 6:
        return Response({'error': 'Invalid weekday'}, status=status.HTTP_400_BAD_REQUEST)

    ensure_weekly_templates(request.user)
    template = get_object_or_404(MenuTemplate, weekday=weekday, meal_type=meal_type, is_active=True)

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
    ordering_for = get_ordering_target_date()
    days = []
    for menu_date in upcoming_dates(14):
        for meal_type in MEAL_TYPES:
            daily, items, source = menu_preview_for_date(menu_date, meal_type)
            days.append({
                'date': menu_date,
                'day_name': menu_date.strftime('%A'),
                'meal_type': meal_type,
                'daily_menu': DailyMenuSerializer(daily).data if daily else None,
                'item_count': len(items),
                'source': source,
                'is_ordering_target': menu_date == ordering_for,
            })
    return Response({
        'ordering_for_date': ordering_for,
        'days': days,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsPortalAdmin])
def daily_menu_detail(request, year, month, day, meal_type):
    err = _validate_meal(meal_type)
    if err:
        return err

    menu_date = date(year, month, day)
    day_name = menu_date.strftime('%A')
    meal_label = 'Lunch' if meal_type == MEAL_LUNCH else 'Dinner'

    if request.method == 'GET':
        daily_menu = daily_menu_for_date(menu_date, meal_type)
        custom_items = list(daily_menu.menu_items.order_by('sort_order', 'name')) if daily_menu else []
        template = get_weekday_template(menu_date.weekday(), meal_type)
        standard_items = template_items_list(template)
        return Response({
            'menu_date': menu_date,
            'day_name': day_name,
            'meal_type': meal_type,
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
    daily_menu = daily_menu_for_date(menu_date, meal_type)
    template = get_weekday_template(menu_date.weekday(), meal_type)
    standard_items = template_items_list(template)

    if action == 'add_item':
        if not daily_menu:
            daily_menu, err_msg = apply_standard_menu(menu_date, request.user, meal_type, publish=False)
            if err_msg and not daily_menu:
                daily_menu = DailyMenu.objects.create(
                    date=menu_date,
                    meal_type=meal_type,
                    created_by=request.user,
                    status='draft',
                    description=f'Custom {meal_label} menu for {day_name}',
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
            daily_menu, err_msg = apply_standard_menu(menu_date, request.user, meal_type, publish=True)
            if err_msg:
                return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not daily_menu.menu_items.exists() and not standard_items:
                return Response({'error': 'No menu items to publish.'}, status=status.HTTP_400_BAD_REQUEST)
            if not daily_menu.menu_items.exists() and standard_items:
                from .services import copy_template_items_to_daily_menu
                copy_template_items_to_daily_menu(template, daily_menu)
            publish_daily_menu(daily_menu)

    elif action == 'unpublish':
        if daily_menu:
            unpublish_daily_menu(daily_menu)

    elif action == 'reset_to_standard':
        if template and template.template_items.exists():
            if not daily_menu:
                daily_menu, _ = apply_standard_menu(menu_date, request.user, meal_type, publish=False)
            else:
                from .services import copy_template_items_to_daily_menu
                copy_template_items_to_daily_menu(template, daily_menu)
                daily_menu.description = f'Standard {meal_label} — {day_name}'
                daily_menu.save(update_fields=['description', 'updated_at'])
                unpublish_daily_menu(daily_menu)

    daily_menu = daily_menu_for_date(menu_date, meal_type)
    return Response({
        'daily_menu': DailyMenuSerializer(daily_menu).data if daily_menu else None,
        'message': f'Action {action} completed',
    })

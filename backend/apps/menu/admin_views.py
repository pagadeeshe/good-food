from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.orders.services import get_daily_order_totals

from .decorators import admin_required
from .models import DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem
from .services import (
    WEEKDAYS,
    apply_standard_menu,
    daily_menu_for_date,
    ensure_weekly_templates,
    get_weekday_template,
    seed_sample_weekly_menus,
    menu_preview_for_date,
    template_items_list,
    upcoming_dates,
)


@admin_required
def admin_dashboard(request):
    ensure_weekly_templates(request.user)
    seed_sample_weekly_menus(request.user)
    today = timezone.localdate()
    today_menu, today_items, source = menu_preview_for_date(today)
    order_totals = get_daily_order_totals(today)

    return render(request, 'admin_portal/dashboard.html', {
        'today': today,
        'today_menu': today_menu,
        'today_items': today_items,
        'today_source': source,
        'weekday_count': MenuTemplate.objects.filter(is_active=True).count(),
        'order_totals': order_totals,
    })


@admin_required
def weekly_menu_list(request):
    ensure_weekly_templates(request.user)
    templates = []
    for weekday, day_name in WEEKDAYS:
        template = get_weekday_template(weekday)
        items = template_items_list(template)
        templates.append({
            'weekday': weekday,
            'day_name': day_name,
            'template': template,
            'items': items,
            'item_count': len(items),
        })

    return render(request, 'admin_portal/weekly_menu.html', {'templates': templates})


@admin_required
def edit_weekday_menu(request, weekday):
    if weekday < 0 or weekday > 6:
        return redirect('admin_weekly_menu')

    ensure_weekly_templates(request.user)
    template = get_object_or_404(MenuTemplate, weekday=weekday, is_active=True)
    day_name = dict(WEEKDAYS)[weekday]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_item':
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', 'main')
            if name:
                max_sort = template.template_items.order_by('-sort_order').first()
                next_order = (max_sort.sort_order + 1) if max_sort else 0
                MenuTemplateItem.objects.create(
                    template=template,
                    name=name,
                    category=category,
                    sort_order=next_order,
                )
                messages.success(request, f'Added "{name}" to {day_name} menu.')
            else:
                messages.error(request, 'Item name is required.')

        elif action == 'delete_item':
            item_id = request.POST.get('item_id')
            item = template.template_items.filter(id=item_id).first()
            if item:
                item_name = item.name
                item.delete()
                messages.success(request, f'Removed "{item_name}" from {day_name} menu.')

        elif action == 'update_description':
            template.description = request.POST.get('description', '').strip()
            template.save(update_fields=['description', 'updated_at'])
            messages.success(request, f'Updated {day_name} menu notes.')

        return redirect('admin_edit_weekday', weekday=weekday)

    return render(request, 'admin_portal/edit_weekday.html', {
        'template': template,
        'day_name': day_name,
        'weekday': weekday,
        'items': template_items_list(template),
        'categories': MenuItem.CATEGORY_CHOICES,
    })


@admin_required
def daily_menu_list(request):
    ensure_weekly_templates(request.user)
    days = []
    for menu_date in upcoming_dates(14):
        daily, items, source = menu_preview_for_date(menu_date)
        days.append({
            'date': menu_date,
            'day_name': menu_date.strftime('%A'),
            'daily_menu': daily,
            'items': items,
            'source': source,
            'is_today': menu_date == timezone.localdate(),
            'status': daily.status if daily else 'not_set',
        })

    return render(request, 'admin_portal/daily_menus.html', {'days': days})


@admin_required
def edit_daily_menu(request, year, month, day):
    menu_date = date(year, month, day)
    day_name = menu_date.strftime('%A')
    template = get_weekday_template(menu_date.weekday())
    standard_items = template_items_list(template)

    daily_menu = daily_menu_for_date(menu_date)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'use_standard':
            daily_menu, error = apply_standard_menu(menu_date, request.user, publish=False)
            if error:
                messages.error(request, error)
            else:
                messages.success(request, f'Applied standard {day_name} menu for {menu_date}.')

        elif action == 'add_item':
            if not daily_menu:
                daily_menu = DailyMenu.objects.create(
                    date=menu_date,
                    created_by=request.user,
                    description=f'Custom menu for {menu_date}',
                    status='draft',
                )
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', 'main')
            if name:
                max_sort = daily_menu.menu_items.order_by('-sort_order').first()
                next_order = (max_sort.sort_order + 1) if max_sort else 0
                MenuItem.objects.create(
                    daily_menu=daily_menu,
                    name=name,
                    category=category,
                    sort_order=next_order,
                )
                daily_menu.description = f'Custom menu for {menu_date}'
                daily_menu.save(update_fields=['description', 'updated_at'])
                messages.success(request, f'Added "{name}" to {menu_date} menu.')
            else:
                messages.error(request, 'Item name is required.')

        elif action == 'delete_item':
            if daily_menu:
                item_id = request.POST.get('item_id')
                item = daily_menu.menu_items.filter(id=item_id).first()
                if item:
                    item_name = item.name
                    item.delete()
                    messages.success(request, f'Removed "{item_name}".')

        elif action == 'publish':
            if not daily_menu or not daily_menu.menu_items.exists():
                # Try applying standard first if no custom items
                if not daily_menu:
                    daily_menu, error = apply_standard_menu(menu_date, request.user, publish=True)
                    if error:
                        messages.error(request, error)
                        return redirect('admin_edit_daily', year=year, month=month, day=day)
                elif not daily_menu.menu_items.exists():
                    messages.error(request, 'Add at least one menu item before publishing.')
                    return redirect('admin_edit_daily', year=year, month=month, day=day)
            if daily_menu and daily_menu.menu_items.exists():
                daily_menu.status = 'published'
                daily_menu.save(update_fields=['status', 'updated_at'])
                messages.success(request, f'Menu for {menu_date} is now live for users.')

        elif action == 'unpublish':
            if daily_menu:
                daily_menu.status = 'draft'
                daily_menu.save(update_fields=['status', 'updated_at'])
                messages.success(request, f'Menu for {menu_date} moved back to draft.')

        elif action == 'reset_to_standard':
            if not daily_menu:
                daily_menu, error = apply_standard_menu(menu_date, request.user, publish=False)
                if error:
                    messages.error(request, error)
            elif template and template.template_items.exists():
                from .services import copy_template_items_to_daily_menu
                copy_template_items_to_daily_menu(template, daily_menu)
                daily_menu.description = f'Standard {day_name} menu'
                daily_menu.status = 'draft'
                daily_menu.save(update_fields=['description', 'status', 'updated_at'])
                messages.success(request, f'Reset to standard {day_name} menu.')
            else:
                messages.error(request, f'No standard items set for {day_name}.')

        return redirect('admin_edit_daily', year=year, month=month, day=day)

    daily_menu = daily_menu_for_date(menu_date)
    custom_items = list(daily_menu.menu_items.order_by('sort_order', 'name')) if daily_menu else []
    using_standard = not custom_items and bool(standard_items)

    return render(request, 'admin_portal/edit_daily.html', {
        'menu_date': menu_date,
        'day_name': day_name,
        'daily_menu': daily_menu,
        'custom_items': custom_items,
        'standard_items': standard_items,
        'using_standard': using_standard,
        'categories': MenuItem.CATEGORY_CHOICES,
    })


@admin_required
def daily_orders_report(request, year=None, month=None, day=None):
    """Kitchen report: how many users ordered and item quantities (no names)."""
    if year and month and day:
        report_date = date(year, month, day)
    else:
        report_date = timezone.localdate()

    daily_menu = daily_menu_for_date(report_date)
    order_totals = get_daily_order_totals(report_date)

    return render(request, 'admin_portal/daily_orders.html', {
        'report_date': report_date,
        'daily_menu': daily_menu,
        'totals': order_totals,
        'is_today': report_date == timezone.localdate(),
    })

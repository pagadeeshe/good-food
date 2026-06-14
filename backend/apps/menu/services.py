from datetime import date, timedelta

from django.utils import timezone

from .constants import (
    MEAL_DINNER,
    MEAL_LUNCH,
    MEAL_TYPES,
    MENU_LOCKED_MESSAGE,
    ORDER_DEADLINE_DISPLAY,
    WEEKDAY_TEMPLATE_LOCKED_MESSAGE,
    is_valid_meal_type,
)
from .models import DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem


WEEKDAYS = DailyMenu.WEEKDAY_CHOICES


def ensure_weekly_templates(user):
    """Create lunch + dinner standard menu templates per weekday if missing."""
    templates = []
    for weekday, day_name in WEEKDAYS:
        for meal_type in MEAL_TYPES:
            meal_label = 'Lunch' if meal_type == MEAL_LUNCH else 'Dinner'
            template, _ = MenuTemplate.objects.get_or_create(
                weekday=weekday,
                meal_type=meal_type,
                defaults={
                    'name': f'{day_name} {meal_label} Menu',
                    'description': f'Default {meal_label.lower()} menu for every {day_name}',
                    'created_by': user,
                    'is_active': True,
                },
            )
            templates.append(template)
    return templates


def get_weekday_template(weekday, meal_type=MEAL_LUNCH):
    return MenuTemplate.objects.filter(
        weekday=weekday, meal_type=meal_type, is_active=True,
    ).first()


def template_items_list(template):
    if not template:
        return []
    return list(template.template_items.order_by('sort_order', 'name'))


def daily_menu_for_date(menu_date, meal_type=MEAL_LUNCH):
    return (
        DailyMenu.objects.filter(date=menu_date, meal_type=meal_type)
        .prefetch_related('menu_items')
        .first()
    )


def copy_template_items_to_daily_menu(template, daily_menu):
    daily_menu.menu_items.all().delete()
    items = []
    for template_item in template.template_items.order_by('sort_order', 'name'):
        items.append(MenuItem(
            daily_menu=daily_menu,
            name=template_item.name,
            description=template_item.description,
            category=template_item.category,
            max_quantity_per_user=template_item.max_quantity_per_user,
            sort_order=template_item.sort_order,
        ))
    if items:
        MenuItem.objects.bulk_create(items)


def apply_standard_menu(menu_date, user, meal_type=MEAL_LUNCH, publish=False):
    template = get_weekday_template(menu_date.weekday(), meal_type)
    if not template or not template.template_items.exists():
        meal_label = 'lunch' if meal_type == MEAL_LUNCH else 'dinner'
        return None, f'No standard {meal_label} menu items configured for this weekday.'

    meal_name = 'Lunch' if meal_type == MEAL_LUNCH else 'Dinner'
    daily_menu, created = DailyMenu.objects.get_or_create(
        date=menu_date,
        meal_type=meal_type,
        defaults={
            'created_by': user,
            'description': f'Standard {meal_name} — {menu_date.strftime("%A")}',
            'status': 'draft',
        },
    )

    if not created:
        daily_menu.description = f'Standard {meal_name} — {menu_date.strftime("%A")}'
        daily_menu.save(update_fields=['description', 'updated_at'])

    copy_template_items_to_daily_menu(template, daily_menu)
    if publish:
        publish_daily_menu(daily_menu)
    return daily_menu, None


def is_weekday_template_locked(weekday, meal_type):
    """Lock template edits when the active ordering menu for this weekday is published."""
    ordering_for = get_ordering_target_date()
    if ordering_for.weekday() != weekday:
        return False
    return DailyMenu.objects.filter(
        date=ordering_for,
        meal_type=meal_type,
        status__in=['published', 'closed'],
    ).exists()


def ensure_weekday_template_editable(weekday, meal_type):
    if is_weekday_template_locked(weekday, meal_type):
        from rest_framework.exceptions import ValidationError
        raise ValidationError(WEEKDAY_TEMPLATE_LOCKED_MESSAGE)


def ensure_menu_editable(daily_menu):
    """Raise ValidationError if the menu is published or closed."""
    if daily_menu and daily_menu.status != 'draft':
        from rest_framework.exceptions import ValidationError
        raise ValidationError(MENU_LOCKED_MESSAGE)


def upcoming_dates(days=14):
    today = timezone.localdate()
    return [today + timedelta(days=i) for i in range(days)]


def get_ordering_target_date():
    """Users always order today for tomorrow's menu (Sun→Mon, Mon→Tue, etc.)."""
    return timezone.localdate() + timedelta(days=1)


def publish_daily_menu(daily_menu):
    daily_menu.status = 'published'
    daily_menu.published_at = timezone.now()
    daily_menu.save(update_fields=['status', 'published_at', 'updated_at'])


def unpublish_daily_menu(daily_menu):
    daily_menu.status = 'draft'
    daily_menu.published_at = None
    daily_menu.save(update_fields=['status', 'published_at', 'updated_at'])


def seed_sample_weekly_menus(user):
    """Populate example lunch + dinner items if weekly templates are empty."""
    lunch_samples = {
        0: ['Egg Curry', 'White Rice', 'Sambar', 'Banana'],
        1: ['Chicken Curry', 'Rice', 'Rasam', 'Curd'],
        2: ['Veg Meals', 'Curd', 'Pickle', 'Dal'],
        3: ['Fish Curry', 'Rice', 'Dal', 'Poriyal'],
        4: ['Egg Fried Rice', 'Manchurian', 'Salad'],
        5: ['Veg Biryani', 'Raita', 'Boiled Egg'],
        6: ['Chicken Biryani', 'Raita', 'Salad'],
    }
    dinner_samples = {
        0: ['Chapati', 'Paneer Butter Masala', 'Dal', 'Milk'],
        1: ['Roti', 'Chicken Masala', 'Salad', 'Curd'],
        2: ['Veg Fried Rice', 'Gobi Manchurian', 'Soup'],
        3: ['Paratha', 'Egg Curry', 'Curd'],
        4: ['Veg Noodles', 'Spring Roll', 'Boiled Egg'],
        5: ['Dosa', 'Chutney', 'Sambar', 'Milk'],
        6: ['Pulao', 'Raita', 'Papad', 'Banana'],
    }
    ensure_weekly_templates(user)
    for weekday, items in lunch_samples.items():
        template = get_weekday_template(weekday, MEAL_LUNCH)
        if template and not template.template_items.exists():
            for i, name in enumerate(items):
                MenuTemplateItem.objects.create(
                    template=template,
                    name=name,
                    category='main',
                    sort_order=i,
                )
    for weekday, items in dinner_samples.items():
        template = get_weekday_template(weekday, MEAL_DINNER)
        if template and not template.template_items.exists():
            for i, name in enumerate(items):
                MenuTemplateItem.objects.create(
                    template=template,
                    name=name,
                    category='main',
                    sort_order=i,
                )


def get_today_published_menu(meal_type=MEAL_LUNCH):
    """Published menu for tomorrow — what users order today."""
    target = get_ordering_target_date()
    return (
        DailyMenu.objects.filter(date=target, meal_type=meal_type, status='published')
        .prefetch_related('menu_items')
        .first()
    )


def get_today_published_menus():
    return {
        meal_type: get_today_published_menu(meal_type)
        for meal_type in MEAL_TYPES
    }


def menu_preview_for_date(menu_date, meal_type=MEAL_LUNCH):
    daily = daily_menu_for_date(menu_date, meal_type)
    if daily and daily.menu_items.exists():
        return daily, list(daily.menu_items.order_by('sort_order', 'name')), 'custom'
    template = get_weekday_template(menu_date.weekday(), meal_type)
    return daily, template_items_list(template), 'standard'


def user_ordering_state(daily_menu, order=None):
    """Per-user ordering: one lunch and one dinner order per menu; no changes after placing."""
    if not daily_menu:
        return False, None, False

    user_has_ordered = bool(
        order
        and order.status != 'cancelled'
        and order.order_items.exists()
    )

    if daily_menu.status != 'published':
        return False, daily_menu.orders_closed_reason, user_has_ordered

    if not daily_menu.is_ordering_open:
        return False, daily_menu.orders_closed_reason, user_has_ordered

    if user_has_ordered:
        meal = daily_menu.get_meal_type_display().lower()
        return False, (
            f'You already placed your {meal} order for this menu. '
            'You can order again when the next menu is published.'
        ), True

    return True, None, False


def serialize_menu_for_api(daily_menu, order=None):
    """Build menu payload for order API responses."""
    if not daily_menu:
        return None
    deadline = daily_menu.ordering_deadline_at
    can_order, closed_reason, user_has_ordered = user_ordering_state(daily_menu, order)
    return {
        'id': daily_menu.id,
        'date': daily_menu.date,
        'ordering_for_date': daily_menu.date,
        'meal_type': daily_menu.meal_type,
        'meal_type_display': daily_menu.get_meal_type_display(),
        'published_at': daily_menu.published_at.isoformat() if daily_menu.published_at else None,
        'expires_at': deadline.isoformat() if deadline else None,
        'expires_at_display': daily_menu.expires_at_display,
        'order_deadline_display': ORDER_DEADLINE_DISPLAY,
        'ordering_deadline_message': daily_menu.ordering_deadline_message,
        'is_ordering_open': can_order,
        'user_has_ordered': user_has_ordered,
        'orders_closed_reason': closed_reason,
        'status': daily_menu.status,
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
    }


def parse_meal_type(value, default=MEAL_LUNCH):
    if value and is_valid_meal_type(value):
        return value
    return default

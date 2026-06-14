from datetime import date, timedelta

from django.utils import timezone

from .models import DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem


WEEKDAYS = DailyMenu.WEEKDAY_CHOICES


def ensure_weekly_templates(user):
    """Create one standard menu template per weekday if missing."""
    templates = []
    for weekday, day_name in WEEKDAYS:
        template, _ = MenuTemplate.objects.get_or_create(
            weekday=weekday,
            defaults={
                'name': f'{day_name} Standard Menu',
                'description': f'Default menu for every {day_name}',
                'created_by': user,
                'is_active': True,
            },
        )
        templates.append(template)
    return templates


def get_weekday_template(weekday):
    return MenuTemplate.objects.filter(weekday=weekday, is_active=True).first()


def template_items_list(template):
    if not template:
        return []
    return list(template.template_items.order_by('sort_order', 'name'))


def daily_menu_for_date(menu_date):
    return DailyMenu.objects.filter(date=menu_date).prefetch_related('menu_items').first()


def copy_template_items_to_daily_menu(template, daily_menu):
    """Replace daily menu items with items from the weekday template."""
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


def apply_standard_menu(menu_date, user, publish=False):
    """Create or refresh a daily menu from the weekday standard template."""
    template = get_weekday_template(menu_date.weekday())
    if not template or not template.template_items.exists():
        return None, 'No standard menu items configured for this weekday.'

    daily_menu, created = DailyMenu.objects.get_or_create(
        date=menu_date,
        defaults={
            'created_by': user,
            'description': f'Standard {menu_date.strftime("%A")} menu',
            'status': 'published' if publish else 'draft',
        },
    )

    if not created:
        daily_menu.description = f'Standard {menu_date.strftime("%A")} menu'
        if publish:
            daily_menu.status = 'published'
        daily_menu.save(update_fields=['description', 'status', 'updated_at'])

    copy_template_items_to_daily_menu(template, daily_menu)
    return daily_menu, None


def upcoming_dates(days=14):
    today = timezone.localdate()
    return [today + timedelta(days=i) for i in range(days)]


def seed_sample_weekly_menus(user):
    """Populate example items if weekly templates are empty."""
    samples = {
        0: ['Egg Curry', 'White Rice', 'Sambar'],
        1: ['Chicken Curry', 'Rice', 'Rasam'],
        2: ['Veg Meals', 'Curd', 'Pickle'],
        3: ['Fish Curry', 'Rice', 'Dal'],
        4: ['Egg Fried Rice', 'Manchurian'],
        5: ['Veg Biryani', 'Raita'],
        6: ['Chicken Biryani', 'Raita', 'Salad'],
    }
    ensure_weekly_templates(user)
    for weekday, items in samples.items():
        template = get_weekday_template(weekday)
        if template and not template.template_items.exists():
            for i, name in enumerate(items):
                MenuTemplateItem.objects.create(
                    template=template,
                    name=name,
                    category='main' if 'Rice' not in name and 'Raita' not in name else 'rice',
                    sort_order=i,
                )


def get_today_published_menu():
    """Return today's published menu for users, or None."""
    today = timezone.localdate()
    return (
        DailyMenu.objects.filter(date=today, status='published')
        .prefetch_related('menu_items')
        .first()
    )


def menu_preview_for_date(menu_date):
    """Return items shown to users: custom daily menu or standard template."""
    daily = daily_menu_for_date(menu_date)
    if daily and daily.menu_items.exists():
        return daily, list(daily.menu_items.order_by('sort_order', 'name')), 'custom'
    template = get_weekday_template(menu_date.weekday())
    return daily, template_items_list(template), 'standard'

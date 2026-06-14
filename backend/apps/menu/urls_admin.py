from django.urls import path

from . import admin_views

urlpatterns = [
    path('', admin_views.admin_dashboard, name='admin_portal'),
    path('orders/', admin_views.daily_orders_report, name='admin_daily_orders'),
    path('orders/<int:year>/<int:month>/<int:day>/', admin_views.daily_orders_report, name='admin_daily_orders_date'),
    path('weekly-menu/', admin_views.weekly_menu_list, name='admin_weekly_menu'),
    path('weekly-menu/<int:weekday>/', admin_views.edit_weekday_menu, name='admin_edit_weekday'),
    path('daily-menu/', admin_views.daily_menu_list, name='admin_daily_menus'),
    path('daily-menu/<int:year>/<int:month>/<int:day>/', admin_views.edit_daily_menu, name='admin_edit_daily'),
]

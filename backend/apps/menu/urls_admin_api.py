from django.urls import path

from . import portal_api

urlpatterns = [
    path('dashboard/', portal_api.admin_dashboard, name='admin_dashboard'),
    path('weekly/', portal_api.weekly_templates, name='weekly_templates'),
    path('weekly/<int:weekday>/<str:meal_type>/', portal_api.weekday_template_detail, name='weekday_template'),
    path('daily/', portal_api.upcoming_daily_menus, name='upcoming_daily'),
    path(
        'daily/<int:year>/<int:month>/<int:day>/<str:meal_type>/',
        portal_api.daily_menu_detail,
        name='daily_menu_detail',
    ),
]

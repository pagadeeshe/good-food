"""
Production URL configuration — portal + full JWT API for React (Vercel).
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from apps.authentication.web_views import (
    AppLoginView,
    AppLogoutView,
    dashboard_view,
    health_view,
    home_redirect,
)

from apps.orders import user_views as order_user_views

urlpatterns = [
    path('health/', health_view, name='health'),
    path('', home_redirect, name='home'),
    path('login/', AppLoginView.as_view(), name='login'),
    path('logout/', AppLogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('today-menu/', order_user_views.today_menu_view, name='today_menu'),
    path('my-orders/', order_user_views.my_orders_view, name='my_orders'),
    path('manage/', include('apps.menu.urls_admin')),
    path('admin/', RedirectView.as_view(url='/manage/', permanent=False)),
    path('django-admin/', admin.site.urls),
    path('api/', TemplateView.as_view(template_name='api/index.html'), name='api_index'),
    # Full JWT API for React frontend
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

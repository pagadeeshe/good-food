"""
Simplified URL configuration for local development
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    # App login (user-facing)
    path('', home_redirect, name='home'),
    path('login/', AppLoginView.as_view(), name='login'),
    path('logout/', AppLogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # User portal (ordering)
    path('today-menu/', order_user_views.today_menu_view, name='today_menu'),
    path('my-orders/', order_user_views.my_orders_view, name='my_orders'),

    # Admin portal (menu management)
    path('manage/', include('apps.menu.urls_admin')),
    # Old /admin/ link → app admin portal (avoids 404 / confusion)
    path('admin/', RedirectView.as_view(url='/manage/', permanent=False)),

    # Django database admin (advanced — requires is_staff account)
    path('django-admin/', admin.site.urls),

    # API documentation placeholder
    path('api/', TemplateView.as_view(template_name='api/index.html'), name='api_index'),

    # API routes (simplified for local dev; production uses urls_production)
    path('api/auth/', include('apps.authentication.urls_simple')),
    path('api/users/', include('apps.users.urls_simple')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
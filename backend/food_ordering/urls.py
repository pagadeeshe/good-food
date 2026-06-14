from django.urls import path, include
from django.contrib import admin

from apps.authentication.health import health_view

urlpatterns = [
    path('health/', health_view, name='health'),
    path('django-admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/admin/', include('apps.menu.urls_admin_api')),
]

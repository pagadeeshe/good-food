from django.urls import path

from . import user_views

urlpatterns = [
    path('today-menu/', user_views.today_menu_view, name='today_menu'),
    path('my-orders/', user_views.my_orders_view, name='my_orders'),
]

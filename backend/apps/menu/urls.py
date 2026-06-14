from django.urls import path

from . import portal_api, views

app_name = 'menu'

urlpatterns = [
    path('today/', views.TodayMenuView.as_view(), name='today_menu'),
    path('daily/', views.DailyMenuListView.as_view(), name='daily_menu_list'),
    path('daily/<int:pk>/', views.DailyMenuDetailView.as_view(), name='daily_menu_detail'),
    path('daily/<int:daily_menu_id>/items/', views.MenuItemListCreateView.as_view(), name='menu_item_list'),
    path('daily/<int:daily_menu_id>/items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menu_item_detail'),
    path('daily/<int:daily_menu_id>/items/bulk/', views.MenuItemBulkUpdateView.as_view(), name='menu_item_bulk'),
    path('daily/<int:daily_menu_id>/publish/', views.publish_menu, name='publish_menu'),
    path('daily/<int:daily_menu_id>/close/', views.close_menu, name='close_menu'),
    path('templates/', views.MenuTemplateListView.as_view(), name='template_list'),
    path('templates/<int:pk>/', views.MenuTemplateDetailView.as_view(), name='template_detail'),
    path('from-template/', views.CreateMenuFromTemplateView.as_view(), name='from_template'),
    path('statistics/', views.menu_statistics, name='menu_statistics'),
]

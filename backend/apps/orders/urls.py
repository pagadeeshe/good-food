from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('today/', views.TodayOrderView.as_view(), name='today_order'),
    path('my/', views.MyOrdersListView.as_view(), name='my_orders'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('reports/today/', views.today_order_totals, name='today_totals'),
    path('reports/<int:year>/<int:month>/<int:day>/', views.daily_order_totals, name='daily_totals'),
]

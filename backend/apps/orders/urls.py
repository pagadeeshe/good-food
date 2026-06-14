from django.urls import path
from django.views.generic import TemplateView

app_name = 'orders'

urlpatterns = [
    # Simple placeholder URLs for development
    path('', TemplateView.as_view(template_name='orders/index.html'), name='index'),
]
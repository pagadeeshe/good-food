from django.urls import path
from django.views.generic import TemplateView

app_name = 'menu'

urlpatterns = [
    # Simple placeholder URLs for development
    path('', TemplateView.as_view(template_name='menu/index.html'), name='index'),
]
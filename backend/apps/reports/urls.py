from django.urls import path
from django.views.generic import TemplateView

app_name = 'reports'

urlpatterns = [
    # Simple placeholder URLs for development
    path('', TemplateView.as_view(template_name='reports/index.html'), name='index'),
]
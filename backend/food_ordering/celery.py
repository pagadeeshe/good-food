"""
Celery configuration for food_ordering project.
Broker/result backend: Upstash Redis (REDIS_URL / CELERY_BROKER_URL).
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings_production')

app = Celery('food_ordering')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'generate-daily-reports': {
        'task': 'apps.orders.tasks.generate_daily_order_reports',
        'schedule': 3600.0,
    },
    'finalize-daily-menu-reports': {
        'task': 'apps.orders.tasks.finalize_daily_menu_reports',
        'schedule': 900.0,
    },
    'cleanup-cancelled-orders': {
        'task': 'apps.orders.tasks.cleanup_cancelled_orders',
        'schedule': crontab(hour=2, minute=0),
    },
}

app.conf.timezone = 'Asia/Kolkata'

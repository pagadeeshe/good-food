"""Shared Redis / Upstash connection helpers for cache and Celery."""

import ssl
from typing import Dict, Optional


def is_tls_redis(url: str) -> bool:
    return url.startswith('rediss://')


def django_redis_options(url: str) -> Dict:
    options = {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    }
    if is_tls_redis(url):
        options['CONNECTION_POOL_KWARGS'] = {
            'ssl_cert_reqs': ssl.CERT_REQUIRED,
        }
    return options


def celery_ssl_options(url: str) -> Optional[Dict]:
    if is_tls_redis(url):
        return {'ssl_cert_reqs': ssl.CERT_REQUIRED}
    return None

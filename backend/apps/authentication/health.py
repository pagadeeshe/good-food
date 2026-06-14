from django.db import connection
from django.http import JsonResponse


def health_view(request):
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({'status': 'ok' if db_ok else 'degraded', 'database': db_ok}, status=status)

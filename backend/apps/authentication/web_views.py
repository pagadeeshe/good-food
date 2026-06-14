from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect

from .forms import EmailAuthenticationForm
from .utils import get_admin_email, is_authorized_admin


class AppLoginView(LoginView):
    template_name = 'authentication/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin_email'] = get_admin_email()
        return context


class AppLogoutView(LogoutView):
    next_page = 'login'


@login_required
def dashboard_view(request):
    if is_authorized_admin(request.user):
        return redirect('admin_portal')
    return redirect('today_menu')


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def health_view(request):
    """Lightweight health check for Railway, Docker, and load balancers."""
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({'status': 'ok' if db_ok else 'degraded', 'database': db_ok}, status=status)

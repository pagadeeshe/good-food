from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from apps.authentication.utils import is_authorized_admin


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_authorized_admin(request.user):
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

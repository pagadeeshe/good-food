from django.conf import settings


def get_admin_email():
    return getattr(settings, 'ADMIN_EMAIL', 'admin@foodordering.com').strip().lower()


def is_authorized_admin(user):
    """Only the configured ADMIN_EMAIL may access the admin portal."""
    if not user or not user.is_authenticated:
        return False
    return (
        user.role == 'admin'
        and user.email.strip().lower() == get_admin_email()
        and user.is_active
    )

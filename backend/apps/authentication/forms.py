from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .utils import get_admin_email, is_authorized_admin


class EmailAuthenticationForm(AuthenticationForm):
    """Login form that uses email instead of username."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': 'you@company.com',
            'class': 'form-input',
        }),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-input',
        }),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role == 'admin' and not is_authorized_admin(user):
            raise forms.ValidationError(
                'Admin access is restricted to the authorized admin account.',
                code='invalid_admin',
            )

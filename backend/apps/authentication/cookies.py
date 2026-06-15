"""HttpOnly cookie helpers for JWT tokens."""

from django.conf import settings


def _base_cookie_kwargs():
    return {
        'httponly': True,
        'secure': settings.JWT_COOKIE_SECURE,
        'samesite': settings.JWT_COOKIE_SAMESITE,
    }


def _refresh_cookie_kwargs():
    return {
        **_base_cookie_kwargs(),
        'max_age': int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        'path': settings.JWT_REFRESH_COOKIE_PATH,
    }


def _access_cookie_kwargs():
    return {
        **_base_cookie_kwargs(),
        'max_age': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        'path': settings.JWT_ACCESS_COOKIE_PATH,
    }


def set_refresh_token_cookie(response, token: str) -> None:
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        token,
        **_refresh_cookie_kwargs(),
    )


def set_access_token_cookie(response, token: str) -> None:
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        token,
        **_access_cookie_kwargs(),
    )


def clear_refresh_token_cookie(response) -> None:
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )


def clear_access_token_cookie(response) -> None:
    response.delete_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        path=settings.JWT_ACCESS_COOKIE_PATH,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )


def clear_auth_cookies(response) -> None:
    clear_access_token_cookie(response)
    clear_refresh_token_cookie(response)

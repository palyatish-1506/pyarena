"""Auth cookie helpers. Only the REFRESH token lives in a cookie now —
the access token is returned in response bodies (spec: access in body,
refresh in httpOnly cookie). Legacy access cookies are still cleared."""

from django.conf import settings
from django.http import HttpResponse


def set_refresh_cookie(response: HttpResponse, refresh: str) -> HttpResponse:
    ttl = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        refresh,
        httponly=True,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        max_age=ttl,
        path="/",
    )
    return response


def clear_auth_cookies(response: HttpResponse) -> HttpResponse:
    for name in (settings.JWT_AUTH_COOKIE, settings.JWT_AUTH_REFRESH_COOKIE):
        response.delete_cookie(name, path="/")
    return response

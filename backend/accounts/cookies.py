"""Helpers for setting/clearing the JWT auth cookies.

Cookie attributes come from settings (env-driven):
  JWT_AUTH_COOKIE / JWT_AUTH_REFRESH_COOKIE — names
  JWT_AUTH_COOKIE_SAMESITE — "Lax" (dev) or "None" (prod, cross-site)
  JWT_AUTH_COOKIE_SECURE   — Secure flag (required when SameSite=None)
"""

from django.conf import settings
from django.http import HttpResponse


def _cookie_kwargs(max_age: int) -> dict:
    return {
        "httponly": True,
        "secure": settings.JWT_AUTH_COOKIE_SECURE,
        "samesite": settings.JWT_AUTH_COOKIE_SAMESITE,
        "max_age": max_age,
        "path": "/",
    }


def set_auth_cookies(response: HttpResponse, access: str, refresh: str) -> HttpResponse:
    access_ttl = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_ttl = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(settings.JWT_AUTH_COOKIE, access, **_cookie_kwargs(access_ttl))
    response.set_cookie(settings.JWT_AUTH_REFRESH_COOKIE, refresh, **_cookie_kwargs(refresh_ttl))
    return response


def clear_auth_cookies(response: HttpResponse) -> HttpResponse:
    for name in (settings.JWT_AUTH_COOKIE, settings.JWT_AUTH_REFRESH_COOKIE):
        response.delete_cookie(name, path="/")
    return response

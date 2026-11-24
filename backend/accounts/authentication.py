"""DRF authentication that reads the JWT from an httpOnly cookie.

DRF's built-in JWTAuthentication only looks at the Authorization header and
returns None early when it's absent — so we override authenticate() to pull
the raw token from request.COOKIES instead (ADR-0002).
"""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token.encode())
        return self.get_user(validated_token), validated_token

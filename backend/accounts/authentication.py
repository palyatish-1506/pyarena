"""DRF authentication: Bearer header first, httpOnly cookie fallback.

M1-final spec: access token travels in the Authorization header (kept in
memory by the frontend); refresh token stays in an httpOnly cookie.
The cookie path remains so older sessions/tokens keep working.
"""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1) Standard Bearer header (spec-compliant path).
        result = super().authenticate(request)
        if result is not None:
            return result
        # 2) Fallback: access_token cookie (legacy/compat path).
        raw = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if raw is None:
            return None
        validated = self.get_validated_token(raw.encode())
        return self.get_user(validated), validated

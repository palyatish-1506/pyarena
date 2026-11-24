"""Auth endpoints — all under /api/v1/auth/.

Cookie-based JWT (ADR-0002): tokens are set as httpOnly cookies and never
appear in response bodies. DRF's CookieJWTAuthentication reads the access
cookie on subsequent requests.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import clear_auth_cookies, set_auth_cookies
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — create account, log in immediately."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return set_auth_cookies(response, str(refresh.access_token), str(refresh))


class LoginView(APIView):
    """POST /api/v1/auth/login/ — email + password -> auth cookies."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"  # strict rate limit per spec

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]
        # TokenObtainPairSerializer returns tokens only — decode the access
        # token's user_id claim to load the user for the response payload.
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import AccessToken

        user = get_user_model().objects.get(pk=AccessToken(access)["user_id"])

        response = Response(UserSerializer(user).data)
        return set_auth_cookies(response, access, refresh)


class RefreshView(APIView):
    """POST /api/v1/auth/refresh/ — rotate tokens from the refresh cookie."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        raw = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not raw:
            return Response({"detail": "No refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={"refresh": raw})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]
        # ROTATE_REFRESH_TOKENS=True means a new refresh token comes back too.
        new_refresh = serializer.validated_data.get("refresh", raw)
        response = Response({"status": "ok"})
        return set_auth_cookies(response, access, new_refresh)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — clear auth cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"status": "ok"})
        return clear_auth_cookies(response)


class MeView(APIView):
    """GET /api/v1/auth/me/ — current user; proves cookie auth works."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

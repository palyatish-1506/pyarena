"""Auth endpoints under /api/v1/auth/ + admin senior-approval endpoints.

Token model (final M1 spec): access token returned in the response BODY;
refresh token lives ONLY in an httpOnly cookie. DRF auth accepts Bearer
header first, cookie as fallback.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import clear_auth_cookies, set_refresh_cookie
from .permissions import IsAdmin
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def _user_payload(user):
    return {"user": UserSerializer(user).data}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"  # 10/hour per spec

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {**_user_payload(user), "access": str(refresh.access_token)},
            status=status.HTTP_201_CREATED,
        )
        return set_refresh_cookie(response, str(refresh))


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"  # 5/min per spec

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]
        from rest_framework_simplejwt.tokens import AccessToken

        user = User.objects.get(pk=AccessToken(access)["user_id"])
        response = Response({**_user_payload(user), "access": access})
        return set_refresh_cookie(response, refresh)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        raw = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not raw:
            return Response({"detail": "No refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={"refresh": raw})
        serializer.is_valid(raise_exception=True)
        response = Response({"access": serializer.validated_data["access"]})
        if "refresh" in serializer.validated_data:  # rotation enabled
            response = set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Blacklist the refresh token so it can't be reused (spec).
        raw = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except Exception:
                pass
        return clear_auth_cookies(Response({"status": "ok"}))


class MeView(APIView):
    """GET + PATCH /api/v1/me — profile read and edit."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_user_payload(request.user))

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(_user_payload(request.user))


class RequestSeniorView(APIView):
    """POST /api/v1/auth/request-senior — student asks for senior access."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role == "student":
            request.user.senior_requested = True
            request.user.save(update_fields=["senior_requested"])
        return Response(_user_payload(request.user))


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — emails a reset link.
    Always returns 200 (don't leak which emails exist)."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        email = request.data.get("email", "")
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                "PyArena password reset",
                f"Reset your password: {reset_url}\n\n"
                "This link expires soon. If you didn't request it, ignore this email.",
                None,
                [user.email],
                fail_silently=True,
            )
        return Response({"detail": "If that email exists, a reset link was sent."})


class _ResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        s = _ResetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(s.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)
        if not PasswordResetTokenGenerator().check_token(user, s.validated_data["token"]):
            return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated. You can log in now."})


# ---------- Admin: senior approval ----------


class PendingSeniorsView(generics.ListAPIView):
    """GET /api/v1/admin/seniors/ — students who requested senior access."""

    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(senior_requested=True, role=User.Role.STUDENT)


class ApproveSeniorView(APIView):
    """POST /api/v1/admin/seniors/{id}/approve/ — grant senior role."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        user.role = User.Role.SENIOR
        user.senior_approved = True
        user.senior_requested = False
        user.save(update_fields=["role", "senior_approved", "senior_requested"])
        return Response(_user_payload(user))

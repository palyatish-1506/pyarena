"""Production settings: hardened, served by gunicorn + whitenoise."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Cross-site cookies (vercel.app -> onrender.com) require SameSite=None + Secure.
JWT_AUTH_COOKIE_SAMESITE = "None"  # noqa: F405
JWT_AUTH_COOKIE_SECURE = True  # noqa: F405
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# drf-spectacular can't infer serializers for function-based views —
# cosmetic schema warnings only, not security issues.
SILENCED_SYSTEM_CHECKS = ["drf_spectacular.W002"]

# Sentry — disabled unless SENTRY_DSN is set (ACTION NEEDED: create project).
SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment="production",
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# Require a real SECRET_KEY in production — refuse to boot with the dev default.
if SECRET_KEY == "dev-insecure-change-me":  # noqa: F405
    raise ImproperlyConfigured("SECRET_KEY must be set via environment variable in production.")

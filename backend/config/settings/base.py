"""Base settings shared by every environment.

Environment-specific values (DATABASE_URL, SECRET_KEY, DEBUG, ALLOWED_HOSTS,
CORS origins, JWT keys...) come from environment variables via django-environ.
See .env.example at the repo root for the full list.
"""

import datetime
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS") or ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    # PyArena apps
    "accounts",
    "questions",
    "submissions",
    "leaderboard",
    "gamification",
    "community",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://pyarena:pyarena@localhost:5432/pyarena",
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
# Spec: display times in IST; USE_TZ=True means the DB always stores UTC.
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    # Cookie-based JWT auth (ADR-0002) — reads access_token cookie.
    "DEFAULT_AUTHENTICATION_CLASSES": ("accounts.authentication.CookieJWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Spec: rate-limit login/submit endpoints (throttle classes wired per-view).
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON_RATE", default="100/hour"),
        "user": env("THROTTLE_USER_RATE", default="1000/hour"),
        "login": env("THROTTLE_LOGIN_RATE", default="5/min"),
        "register": env("THROTTLE_REGISTER_RATE", default="10/hour"),
        "submit": env("THROTTLE_SUBMIT_RATE", default="30/min"),
    },
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# College roll-number format — configurable until the real format is confirmed.
# College identifiers: 9-digit enrollment number (e.g. 250002061) OR a
# division+roll format like BX123 / BY7 / BZ100 (division code + roll 1-100).
import re  # noqa: E402

ROLL_NO_REGEX = re.compile(env("ROLL_NO_REGEX", default=r"^(\d{9}|[A-Za-z]{2}\d{1,3})$"))

# Public frontend origin — used to build password-reset links.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(
        seconds=env.int("JWT_ACCESS_TOKEN_LIFETIME", default=15 * 60)
    ),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(
        seconds=env.int("JWT_REFRESH_TOKEN_LIFETIME", default=7 * 24 * 3600)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PyArena API",
    "DESCRIPTION": "API for the PyArena Python learning and quiz platform.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# --- Auth cookies (ADR-0002) ---
JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"
JWT_AUTH_COOKIE_SAMESITE = env("JWT_COOKIE_SAMESITE", default="Lax")
JWT_AUTH_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=False)

# --- Email ---
# Dev default: console backend (links print to runserver logs).
# Prod (Resend SMTP): set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# plus EMAIL_HOST=smtp.resend.com, EMAIL_PORT=587, EMAIL_HOST_USER=resend,
# EMAIL_HOST_PASSWORD=<resend api key>, EMAIL_USE_TLS=True.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)

# Anymail (HTTPS API providers — works where SMTP ports are blocked).
# Prod: EMAIL_BACKEND=anymail.backends.brevo.EmailBackend + ANYMAIL_API_KEY.
ANYMAIL = {
    "BREVO_API_KEY": env("ANYMAIL_API_KEY", default=""),
}

# Profanity filter for comments — comma-separated, extend via env.
COMMENT_BAD_WORDS = [w.strip() for w in env("COMMENT_BAD_WORDS", default="").split(",") if w.strip()]
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="PyArena <noreply@pyarena.local>")

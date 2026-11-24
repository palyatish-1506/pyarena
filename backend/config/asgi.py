"""ASGI entrypoint — used if we ever need websockets/async (config.settings.prod)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()

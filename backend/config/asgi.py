"""ASGI entrypoint — HTTP + WebSockets (live quiz).

Order matters: get_asgi_application() runs django.setup(), so the
websocket URLconf (which imports models) must be imported AFTER it.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402

http_app = get_asgi_application()  # django.setup() happens here

from livequiz.routing import websocket_urlpatterns  # noqa: E402  (after setup)

application = ProtocolTypeRouter(
    {
        "http": http_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from apps.chat import routing as chat_routing
from apps.notification import routing as notification_routing
from apps.chat.middleware import JWTAuthMiddleware
all_websocket_patterns = chat_routing.websocket_urlpatterns + notification_routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(URLRouter(all_websocket_patterns)),
})
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from Chats.consumers import ChatConsumer
from Communities.routing import websocket_urlpatterns as community_ws_urls
from Chats.routing import websocket_urlpatterns as chat_ws_urls
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MindMates.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_ws_urls + community_ws_urls 
            # path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi()),
        )
    ),
})
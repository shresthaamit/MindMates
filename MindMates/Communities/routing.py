from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/community/<int:pk>/', consumers.CommunityChatConsumer.as_asgi()),
]
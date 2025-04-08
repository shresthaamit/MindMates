from . import views
from django.urls import path, include
from .routing import websocket_urlpatterns

urlpatterns = [
    path('start/',views.create_conversation, name="start-conversation"),
    path('start/<int:convo_id>/',views.get_conversation,name="get_conversation"),
    path('', views.conversations, name="conversations"),
    path('messages/<int:message_id>/read/', views.mark_message_read),
  
]

from . import views
from django.urls import path, include
from .routing import websocket_urlpatterns

urlpatterns = [
    path('start/',views.create_conversation, name="start-conversation"),
    path('start/<int:convo_id>/',views.get_conversation,name="get_conversation"),
    path('users/', views.all_users_for_chat, name='all-users-for-chat'),
    path('', views.conversations, name="conversations"),
    path('messages/<int:message_id>/read/', views.mark_message_read),
    path('messages/<int:message_id>/edit/', views.edit_message),
    path('messages/<int:message_id>/delete/', views.delete_message),
    path('<int:conversation_id>/messages/upload/', 
         views.upload_private_file, 
         name='upload-private-file'),
    
    path('<int:conversation_id>/messages/<int:message_id>/like/', views.toggle_like, name='toggle-like'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:pk>/messages/', views.MessageListView.as_view(), name='message-list'),

]
  

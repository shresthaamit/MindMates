from . import views
from django.urls import path

urlpatterns = [
    path('start/',views.create_conversation, name="start-conversation"),
    path('<int:convo_id>/',views.get_conversation,name="get_conversation"),
    path('', views.conversations, name="conversations"),
]

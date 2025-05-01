from django.urls import path
from . import views
urlpatterns = [
    path('', views.CommunityListCreate.as_view(),name='create-community'),
    path('<int:pk>/', views.CommunityDetail.as_view(),name='community-detail'),
    path('<int:pk>/join/', views.JoinCommunity.as_view(), name='join-community'),
    path('<int:pk>/leave/', views.LeaveCommunity.as_view(),name='leave-community'),
    path('<int:pk>/remove/',views.RemoveMember.as_view(), name='remove-member'),
    path('<int:pk>/messages/', views.CommunityMessageListCreate.as_view(), name='community-messages'),
    path('<int:community_id>/upload/', views.upload_file, name='file-upload'),
    path('<int:community_id>/debug/', views.debug_community, name='file-upload'),
]

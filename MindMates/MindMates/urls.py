"""
URL configuration for MindMates project.
"""

from django.contrib import admin
from django.urls import path, include
from Users import routers as users_urls
from QueryMate import routers as querymate_urls
from django.conf import settings
from Chats import routing 
from Users.views import EmailTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
auth_api_urls = [
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')), 
]

if settings.DEBUG:
    auth_api_urls.append(path('verify/', include('rest_framework.urls')))  

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("accounts/", include(users_urls.router.urls)), 
    path("querymate/", include("QueryMate.urls")),  # QueryMate URLs
    # path('chats/', include('Chats.routing')),
    path("chats/", include("Chats.urls")),
    path("communities/",include("Communities.urls")),
    *auth_api_urls,  # OAuth2 URLs
]

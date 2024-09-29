"""
URL configuration for MindMates project.
"""

from django.contrib import admin
from django.urls import path, include
from Users import routers as users_urls
from django.conf import settings

auth_api_urls = [
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),  # OAuth2 provider URLs
]

if settings.DEBUG:
    auth_api_urls.append(path('verify/', include('rest_framework.urls')))  # Debug verification URLs

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(users_urls.router.urls)),  # Custom user accounts API
    *auth_api_urls,  # OAuth2 URLs
]

"""
URL configuration for MindMates project.
"""

from django.contrib import admin
from django.urls import path, include
from Users import routers as users_urls
from QueryMate import routers as querymate_urls
from django.conf import settings

auth_api_urls = [
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')), 
]

if settings.DEBUG:
    auth_api_urls.append(path('verify/', include('rest_framework.urls')))  

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(users_urls.router.urls)), 
    path("querymate/", include(querymate_urls.router.urls)),  # QueryMate URLs
    *auth_api_urls,  # OAuth2 URLs
]

from django.urls import path, include
from .routers import urlpatterns as router_urls  # Import the urlpatterns from routers.py

app_name = "queryMate"

urlpatterns = [
    path('', include(router_urls)),  # Include the router URLs
]
from rest_framework import routers
from .views import UserViewSet
app_name ="Users"
router = routers.DefaultRouter()
router.register("users", UserViewSet)

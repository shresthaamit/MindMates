from rest_framework import routers
from .views import UserViewSet, UserProfileViewSet
app_name ="Users"
router = routers.DefaultRouter()
router.register("users", UserViewSet)
router.register("profile", UserProfileViewSet)

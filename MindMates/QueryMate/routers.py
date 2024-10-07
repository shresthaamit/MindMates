from .views import TagViewset
from rest_framework import routers
app_name = "queryMate"
router = routers.DefaultRouter()
router.register("tags", TagViewset, basename="tags")
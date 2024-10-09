from .views import TagViewset,QuestionViewset
from rest_framework import routers
app_name = "queryMate"
router = routers.DefaultRouter()
router.register("tags", TagViewset, basename="tags")
router.register("questions", QuestionViewset, basename="questions")


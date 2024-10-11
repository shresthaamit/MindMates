from .views import TagViewset,QuestionViewset,AnswerViewset
from rest_framework import routers
from django.urls import path, include
app_name = "queryMate"
router = routers.DefaultRouter()
router.register("tags", TagViewset, basename="tags")
router.register("questions", QuestionViewset, basename="questions")


urlpatterns = [
    path('', include(router.urls)),
    path('questions/<int:question_id>/answers/', AnswerViewset.as_view({'get': 'list', 'post': 'create'}), name='question-answers'),
    path('answers/<int:pk>/', AnswerViewset.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='answer-detail'),
]
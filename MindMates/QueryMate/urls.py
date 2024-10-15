# from .views import TagViewset,QuestionViewset,AnswerViewset
# from rest_framework import routers
# from django.urls import path, include
# from rest_framework_nested.routers import NestedSimpleRouter
# app_name = "queryMate"
# router = routers.DefaultRouter()
# router.register("tags", TagViewset, basename="tags")
# router.register("questions", QuestionViewset, basename="questions")
# questions_router = NestedSimpleRouter(router, 'questions', lookup='question')
# questions_router.register('answers', AnswerViewset, basename='question-answers')

# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include(questions_router.urls)),
#     # path('questions/<int:question_id>/answers/', AnswerViewset.as_view({'get': 'list', 'post': 'create'}), name='question-answers'),
#     # path('answers/<int:pk>/', AnswerViewset.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='answer-detail'),
# ]
from rest_framework import routers
from django.urls import path, include
from rest_framework_nested.routers import NestedSimpleRouter
from .views import TagViewset, QuestionViewset, AnswerViewset,ReviewCreate,ReviewList,ReviewDetail

# Main router
from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers
from .views import TagViewset, QuestionViewset, AnswerViewset

router = routers.DefaultRouter()
router.register("tags", TagViewset, basename="tags")
router.register("questions", QuestionViewset, basename="questions")
router.register("answers", AnswerViewset, basename="answers")

# Nested router for answers
questions_router = nested_routers.NestedSimpleRouter(router, 'questions', lookup='question')
questions_router.register('answers', AnswerViewset, basename='question-answers')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(questions_router.urls)),
    path('answers/<int:pk>/review-create/',ReviewCreate.as_view(), name='review-create'),
    path('answers/<int:pk>/review/',ReviewList.as_view(), name='review-list'),
    path('answers/review/<int:pk>/',ReviewDetail.as_view(), name='review-detail'),
    
]

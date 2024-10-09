# from django.shortcuts import render
# from rest_framework import viewsets
# from .models import Tag, Question
# from .serializers import TagSerializer,QuestionSerializer
# from .permissions import IsAdminOrStaffOtherReadOnly, IsAuthenticated,IsOwner
# # Create your views here.
# class TagViewset(viewsets.ModelViewSet):
#     queryset = Tag.objects.all()
#     serializer_class = TagSerializer
#     permission_classes= [IsAdminOrStaffOtherReadOnly] 
    
# class QuestionViewset(viewsets.ModelViewSet):
#     queryset = Question.objects.all()
#     serializer_class = QuestionSerializer
#     permission_classes =[IsAuthenticated]
#     def get_permissions(self):
#         if self.action == 'create':
#             return [IsAuthenticated()]
#         elif self.action in ['update', 'partial_update', 'delete']:  # Use lowercase 'delete'
#             return [IsOwner()]
#         return super().get_permissions()

#     def upvote(self, request, pk=None):
#         question = self.get_object()
#         question.upvotes.add(request.user)  # Use .add() for many-to-many
#         return Response({'status': 'question upvoted'})

#     # Example method to downvote a question
#     def downvote(self, request, pk=None):
#         question = self.get_object()
#         question.downvotes.add(request.user)  # Use .add() for many-to-many
#         return Response({'status': 'question downvoted'})
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Tag, Question
from .serializers import TagSerializer, QuestionSerializer, VoteSerializer
from .permissions import IsAuthenticated, IsOwner,IsAdminOrStaffOtherReadOnly
from rest_framework.authentication import SessionAuthentication



class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrStaffOtherReadOnly]

class QuestionViewset(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        question = self.get_object()
        message = question.toggle_upvote(request.user)
        return Response({'status': message, 'upvote_count': question.upvote_count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def downvote(self, request, pk=None):
        question = self.get_object()
        message = question.toggle_downvote(request.user)
        return Response({'status': message, 'downvote_count': question.downvote_count}, status=status.HTTP_200_OK)
# class DownvoteViewset(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]

#     def create(self, request, pk=None):
#         question = self.get_object(pk)
#         question.add_downvote(request.user)
#         return Response({'status': 'question downvoted'}, status=status.HTTP_200_OK)

#     def get_object(self, pk):
#         return Question.objects.get(pk=pk)

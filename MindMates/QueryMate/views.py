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
from django.forms import ValidationError
from rest_framework import viewsets, status,permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Tag, Question,Answer
from .serializers import TagSerializer, QuestionSerializer, VoteSerializer,AnswerSerializer
from .permissions import IsAuthenticated, IsOwner,IsAdminOrStaffOtherReadOnly
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound


class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrStaffOtherReadOnly]

class QuestionViewset(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]
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

class AnswerViewset(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [permissions.AllowAny]
    # lookup_field = 'id'
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwner()]
        return super().get_permissions()
    
    
    def get_queryset(self):
        question_id = self.kwargs.get('question_pk')
        if question_id:
            return self.queryset.filter(question_id = question_id)
        return self.queryset
    def perform_create(self, serializer):
        question_id = self.kwargs.get('question_pk')
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise NotFound("Question not found.")
        existing_answer = Answer.objects.filter(user=self.request.user, question=question).first()
        if existing_answer:
        # Update the existing answer
            serializer = self.get_serializer(existing_answer, data=serializer.validated_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        serializer.save(user=self.request.user, question=question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # def perform_create(self, serializer):
    #     question_id = self.kwargs.get('question_pk')
    #     try:
    #         question = Question.objects.get(id=question_id)
    #     except Question.DoesNotExist:
    #         raise NotFound("Question not found.")
    #     if Answer.objects.filter(user=self.request.user, question=question).exists():
    #         return Response({"detail": "You have already answered this question."}, status=status.HTTP_400_BAD_REQUEST)
    #         # raise ValidationError("You have already answered this question.")
    #     serializer.save(user=self.request.user, question=question)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
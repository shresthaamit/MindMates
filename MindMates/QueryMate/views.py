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
from .models import Tag, Question,Answer,Review
from .serializers import TagSerializer, QuestionSerializer, VoteSerializer,AnswerSerializer,ReviewSerializer
from .permissions import IsAuthenticated, IsOwner,IsAdminOrStaffOtherReadOnly,IsReviewOwner
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import NotFound
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrStaffOtherReadOnly]

class QuestionViewset(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    # permission_classes = [permissions.AllowAny]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            # No authentication required for safe methods (GET)
            return [AllowAny()]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only authenticated owners can update/delete
            return [IsAuthenticated(), IsOwner()]
        else:
            # For POST and other unsafe methods, just require authentication
            return [IsAuthenticated()]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def total_count(self, request):
        total = Question.objects.count()
        return Response({'total_questions': total})
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        question = self.get_object()
        result = question.toggle_upvote(request.user)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def downvote(self, request, pk=None):
        question = self.get_object()
        result = question.toggle_downvote(request.user)
        return Response(result, status=status.HTTP_200_OK)


class AnswerViewset(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    # permission_classes = [permissions.AllowAny]
    authentication_classes = [JWTAuthentication]
    # lookup_field = 'id'
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwner()]
        return [AllowAny()]
        # return super().get_permissions()
    
    
    def get_queryset(self):
        question_id = self.kwargs.get('question_pk')
        if question_id:
            return self.queryset.filter(question_id = question_id)
        return self.queryset
    def create(self, request, *args, **kwargs):
        question_id = self.kwargs.get('question_pk')
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise NotFound("Question not found.")

        existing_answer = Answer.objects.filter(user=request.user, question=question).first()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if existing_answer:
            # Update existing answer
            serializer = self.get_serializer(existing_answer, data=serializer.validated_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If no existing answer, call perform_create to save new answer
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    def perform_create(self, serializer):
        question_id = self.kwargs.get('question_pk')
        question = Question.objects.get(id=question_id)
        serializer.save(user=self.request.user, question=question)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None, question_pk=None):
        print("pk:", pk)
        print("Upvotequestion_pk:", question_pk)
        try:
            answer = Answer.objects.get(pk=pk, question_id=question_pk)
        except Answer.DoesNotExist:
            return Response({'detail': 'Answer not found for this question.'}, status=status.HTTP_404_NOT_FOUND)

        message = answer.toggle_upvote(request.user)
        return Response({
            'status': message,
            'upvote_count': answer.upvote_count,
            'downvote_count': answer.downvote_count
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def downvote(self, request, pk=None, question_pk=None):
        print("pk:", pk)
        print("downvotequestion_pk:", question_pk)
        try:
            answer = Answer.objects.get(pk=pk, question_id=question_pk)
        except Answer.DoesNotExist:
            return Response({'detail': 'Answer not found for this question.'}, status=status.HTTP_404_NOT_FOUND)

        message = answer.toggle_downvote(request.user)
        return Response({
            'status': message,
            'upvote_count': answer.upvote_count,
            'downvote_count': answer.downvote_count
        }, status=status.HTTP_200_OK)
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
class ReviewViewset(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwner]

    def get_queryset(self):
        question_pk = self.kwargs.get('question_pk')
        answer_pk = self.kwargs.get('answer_pk')

            # Check answer exists and belongs to question
        if not Answer.objects.filter(pk=answer_pk, question_id=question_pk).exists():
            raise NotFound("Answer does not belong to the specified question.")

        return Review.objects.filter(answer_id=answer_pk)

    def perform_create(self, serializer):
        question_pk = self.kwargs.get('question_pk')
        answer_pk = self.kwargs.get('answer_pk')

        try:
            answer = Answer.objects.get(pk=answer_pk, question_id=question_pk)
        except Answer.DoesNotExist:
            raise NotFound("Answer not found for this question.")

        # Check if this user already reviewed this answer
        if Review.objects.filter(answer=answer, user=self.request.user).exists():
            raise ValidationError({"detail": "You have already reviewed this answer."})
            print("AAAA")
        serializer.save(answer=answer, user=self.request.user)
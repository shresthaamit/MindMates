from django.shortcuts import render
from rest_framework import viewsets
from .models import Tag, Question
from .serializers import TagSerializer,QuestionSerializer
from .permissions import IsAdminOrStaffOtherReadOnly, IsAuthenticated,IsOwner
# Create your views here.
class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes= [IsAdminOrStaffOtherReadOnly] 
    
class QuestionViewset(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes =[IsAuthenticated]
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action == 'update' or self.action == 'partial_update' or self.action == 'Delete':
            return [IsOwner()]
        return super().get_permissions()
    
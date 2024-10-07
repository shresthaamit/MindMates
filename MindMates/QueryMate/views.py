from django.shortcuts import render
from rest_framework import viewsets
from .models import Tag, Question
from .serializers import TagSerializer
from .permissions import IsAdminOrStaffOtherReadOnly
# Create your views here.
class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes= [IsAdminOrStaffOtherReadOnly] 
    
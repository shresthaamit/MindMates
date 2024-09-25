from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth.models import User
from .serializers import UserSerializer
from .permissions import IsOwnerOrReadOnlyAndGetPost
# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnlyAndGetPost]
    queryset = User.objects.all()
    serializer_class = UserSerializer



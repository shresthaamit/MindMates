from django.shortcuts import render
from rest_framework import viewsets,mixins
from django.contrib.auth.models import User
from .serializers import UserSerializer,UserProfileSerializer
from .permissions import IsOwnerOrReadOnlyAndGetPost,IsProfileUserOrReadOnly
from .models import UserProfile
# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnlyAndGetPost]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserProfileViewSet(viewsets.GenericViewSet,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,mixins.ListModelMixin):
    permission_classes =[IsProfileUserOrReadOnly]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

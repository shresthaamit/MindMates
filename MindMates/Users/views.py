from django.shortcuts import render
from rest_framework import viewsets,mixins
from django.contrib.auth.models import User
from .serializers import UserSerializer,UserProfileSerializer,EmailTokenObtainSerializer
from .permissions import IsOwnerOrReadOnlyAndGetPost,IsProfileUserOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import UserProfile
# Create your views here.
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainSerializer
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnlyAndGetPost]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserProfileViewSet(viewsets.GenericViewSet,mixins.RetrieveModelMixin,mixins.UpdateModelMixin):
    permission_classes =[IsProfileUserOrReadOnly]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

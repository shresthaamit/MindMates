from django.shortcuts import render
from rest_framework import viewsets,mixins
from django.contrib.auth.models import User
from .serializers import UserSerializer,UserProfileSerializer,EmailTokenObtainSerializer
from .permissions import IsOwnerOrReadOnlyAndGetPost,IsProfileUserOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response


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
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = self.get_serializer(user_profile)
        return Response(serializer.data)

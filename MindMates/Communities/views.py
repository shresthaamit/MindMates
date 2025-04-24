from django.shortcuts import render
from rest_framework import generics,permissions,status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import  Response
from django.core.exceptions import PermissionDenied
from .models import *
from .serializers import *
# Create your views here.
class CommunityListCreate(generics.ListCreateAPIView):
    queryset = Community.objects.all()
    permission_classes =[permissions.IsAuthenticated]
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommunitySerializer
        return CommunityDetailSerializer
    def get_queryset(self):
        return self.request.user.communities.all()
            
    
class CommunityDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunityDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_destroy(self, instance):
        if instance.creaters == self.request.User:
            instance.delete()
        else:
            raise PermissionDenied("only community creators can delete")

class JoinCommunity(APIView):
    permission_classes =[permissions.IsAuthenticated]
    def post(self, request,pk):
        community = get_object_or_404(Community,pk)
        community.members.add(request.user)
        return Response({'status':'successfully joined'}, status=status.HTTP_200_OK)
    
class LeaveCommunity(APIView):
    permission_classes =[permissions.IsAuthenticated]
    def post(self, request,pk):
        community = get_object_or_404(Community, pk=pk)
        community.members.remove(request.user)
        return Response({'status':'Memeber Left successfully'}, status=status.HTTP_200_OK)
    
class RemoveMember(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        community = get_object_or_404(Community,pk=pk)
        serializer = JoinLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if community.creaters != request.user:
            return Response({'error':'Only creator can remove member'},status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=serializer.validated_data['user_id'])
        community.members.remove(user)
        return Response({'status': 'member removed'}, status=status.HTTP_200_OK)
        
        
class CommunityMessageListCreate(generics.ListCreateAPIView):
    serializer_class = CommunityMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        community_id = self.kwargs['pk']
        return CommunityMessage.objects.filter(community__id=community_id, is_deleted=False)
    def perform_create(self, serializer):
        community_id = self.kwargs['pk']
        community = get_object_or_404(Community, pk=community_id)

        # Only allow posting if user is a member
        if self.request.user not in community.members.all():
            raise PermissionDenied("You are not a member of this community")

        serializer.save(
            sender=self.request.user,
            community=community
        )
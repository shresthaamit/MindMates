import re
from django.shortcuts import render
from rest_framework import generics,permissions,status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import  Response
from django.core.exceptions import PermissionDenied
from .models import *
from .serializers import *

from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
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
    def post(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        
        # Check if user is already a member
        if community.members.filter(id=request.user.id).exists():
            return Response(
                {'status': 'User is already a member'}, 
                status=status.HTTP_400_BAD_REQUEST
            )    
        community.members.add(request.user)
        return Response(
            {'status': 'successfully joined'}, 
            status=status.HTTP_200_OK
        )
    # def post(self, request,pk):
    #     community = get_object_or_404(Community,pk=pk)
    #     community.members.add(request.user)
    #     return Response({'status':'successfully joined'}, status=status.HTTP_200_OK)
    
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
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        community_id = self.kwargs['pk']
        return CommunityMessage.objects.filter(community__id=community_id, is_deleted=False)
    def perform_create(self, serializer):
        community_id = self.kwargs['pk']
        community = get_object_or_404(Community, pk=community_id)

        # Only allow posting if user is a member
        if self.request.user not in community.members.all():
            raise PermissionDenied("You are not a member of this community")
        file = self.request.FILES.get('file')
        if file:
            serializer.save(
                sender= self.request.user,
                community  = community,
                file = file,
                file_name = file.name,
                file_size = file.size
                )
        else:
            serializer.save(
                sender=self.request.user,
                community=community
            )

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request, community_id):
    """Handle actual file uploads via HTTP"""
    file = request.FILES.get('file')
    if not file:
        return Response({"error": "No file provided"}, status=400)
    
    # Validate community membership
    community = get_object_or_404(Community, pk=community_id)
    if request.user not in community.members.all():
        return Response({"error": "Not a member of this community"}, status=403)
    
    # Validate file size
    if file.size > 10 * 1024 * 1024:  # 10MB
        return Response({"error": "File too large (max 10MB)"}, status=413)
    
    # Validate file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx']
    file_ext = '.' + file.name.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        return Response({"error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"}, status=415)
    
    # Sanitize filename
    safe_name = re.sub(r'[^\w\-_. ]', '', file.name)
    
    # Save file
    message = CommunityMessage.objects.create(
        community=community,
        sender=request.user,
        file=file,
        file_name=safe_name,
        file_size=file.size
    )
    
    return Response({
        "type": "file_upload_success",
        "message_id": message.id,
        "file_url": message.file.url,  # URL to access the file
        "file_name": message.file_name,
        "file_size": message.file_size
    })
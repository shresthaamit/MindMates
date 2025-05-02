import re
from django.shortcuts import render
from rest_framework import generics,permissions,status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import  Response
from django.core.exceptions import PermissionDenied
from .models import *
from django.core.exceptions import ImproperlyConfigured
from .serializers import *
from rest_framework.renderers import JSONRenderer,BrowsableAPIRenderer
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes, renderer_classes
from rest_framework.parsers import MultiPartParser, FormParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import authentication_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
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
@authentication_classes([JWTAuthentication]) 
@parser_classes([MultiPartParser, FormParser])
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def upload_file(request, community_id):
    """Handles both file uploads and text messages"""
    try:
        community = Community.objects.get(id=community_id)
        print(f"Authenticated user: {request.user} (ID: {request.user.id})") 
        
        # Verify membership
        if not community.members.filter(id=request.user.id).exists():
            return Response(
                {"error": "You must be a member to post"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message_data = {
            'community': community,
            'sender': request.user,
            'content': serializer.validated_data.get('content', '')
        }
        
        if 'file' in serializer.validated_data:
            uploaded_file = serializer.validated_data['file']
            
            # File validation
            if uploaded_file.size > 10 * 1024 * 1024:
                return Response(
                    {"error": "File too large (max 10MB)"}, 
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )
                
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx','.txt']
            file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {"error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"},
                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )
            
            message_data.update({
                'file': uploaded_file,
                'file_name': re.sub(r'[^\w\-_. ]', '', uploaded_file.name),
                'file_size': uploaded_file.size
            })

        message = CommunityMessage.objects.create(**message_data)
        
        # WebSocket broadcast (simplified)
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"community_{community_id}",
                {
                    "type": "chat.message",
                    "message": {
                        "id": message.id,
                        "content": message.content,
                        "file_url": message.file.url if message.file else None,
                        "sender": {
                            "id": request.user.id,
                            "username": request.user.username
                        },
                        "timestamp": message.created_at.isoformat()
                    }
                }
            )
        except Exception as e:
            print(f"WebSocket error (non-critical): {e}")

        return Response({
            "status": "success",
            "message_id": message.id,
            "content": message.content,
            "file_url": message.file.url if message.file else None
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def debug_community(request, community_id):
    community = Community.objects.get(id=community_id)
    return Response({
        'community': community.name,
        'members': list(community.members.values_list('id', flat=True)),
        'current_user': request.user.id
    })
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
def toggle_like(request, community_id, message_id):
    try:
        # Verify message belongs to community
        message = CommunityMessage.objects.select_related('community').get(
            id=message_id,
            community_id=community_id
        )
        
        # Verify user is community member
        if not message.community.members.filter(id=request.user.id).exists():
            return Response(
                {"error": "Not a community member"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Like toggle logic...
        user = request.user
        with transaction.atomic():
            if user in message.likes.all():
                message.likes.remove(user)
                liked = False
            else:
                message.likes.add(user)
                liked = True
            message.update_like_count()
        
        return Response({
            "status": "success",
            "liked": liked,
            "like_count": message.like_count
        })
        
    except CommunityMessage.DoesNotExist:
        return Response(
            {"error": "Message not found in this community"},
            status=status.HTTP_404_NOT_FOUND
        )
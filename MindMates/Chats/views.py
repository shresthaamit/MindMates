from datetime import timezone
from django.shortcuts import render
from .models import Conversation,Message
from rest_framework import generics,permissions,status
from rest_framework.decorators import api_view,permission_classes,parser_classes
from rest_framework.response import Response
from Users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer,MessageSerializer,FileUploadSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect, reverse
from rest_framework.parsers import MultiPartParser, FormParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import authentication_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    data = request.data
    receiver_username = data.get("receiver", {}).get("username")


    if not receiver_username:
        return Response({"message": "Receiver username is required."}, status=400)

    try:
        receiver = User.objects.get(username=receiver_username)
    except User.DoesNotExist:
        return Response({"message": "You can only chat with existed user."}, status=400)

    initiator = request.user

    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        initiator=initiator, receiver=receiver
    ).first() or Conversation.objects.filter(
        initiator=receiver, receiver=initiator
    ).first()

    if conversation:
        print ("Conversation already exists.")
        return Response({"message": "Conversation already exists."})

    # Create new conversation
    conversation = Conversation.objects.create(initiator=initiator, receiver=receiver)
    return Response({
        "message": "Conversation started successfully.",
        "conversation_id": conversation.id
    })

    
@api_view(['GET'])
def get_conversation(request, convo_id):
    conversation = Conversation.objects.filter(id=convo_id)
    if not conversation.exists():
        return Response({'message': 'Conversation does not exist'})
    
    serializer = ConversationSerializer(conversation[0], context={'request': request})  
    return Response(serializer.data)

@api_view(['GET'])
def conversations(request):
    conversationlist = Conversation.objects.filter(Q(initiator=request.user) | Q(receiver=request.user))
    serializer = ConversationSerializer(instance=conversationlist, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['PATCH'])
def mark_message_read(request, message_id):
    try:
        message = Message.objects.get(
            id=message_id,
            conversation__receiver=request.user  # Only receiver can mark read
        )
        message.is_read = True
        message.save()
        print("MArked as read")
        return Response({"status": "marked as read"})
    
    except Message.DoesNotExist:
        return Response({"error": "Message not found"}, status=404)
    

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_message(request, message_id):
    try:
        message = Message.objects.get(
            id=message_id,
            sender=request.user,  # Only sender can edit
            is_deleted=False      # Can't edit deleted messages
        )
        serializer = MessageSerializer(message, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(is_edited=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    except Message.DoesNotExist:
        return Response({"error": "Message not found or unauthorized"}, status=404)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    try:
        message = Message.objects.get(
            id=message_id,
            sender=request.user  # Only sender can delete
        )
        message.is_deleted = True
        message.delete()
        return Response({"status": "message deleted"})
    except Message.DoesNotExist:
        return Response({"error": "Message not found"}, status=404)
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@parser_classes([MultiPartParser, FormParser])
def upload_private_file(request, conversation_id):
    """Handles file uploads for private messages"""
    try:
        # Verify conversation exists and user is participant
        conversation = Conversation.objects.filter(
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        ).first()
        
        if not conversation:
            return Response(
                {"error": "Conversation not found or access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # File processing
        uploaded_file = None
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

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data.get('content', ''),
            file=uploaded_file
        )
        
        # WebSocket broadcast
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation_id}",
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
                        "timestamp": message.created_at.isoformat(),
                        "is_read": False
                    }
                }
            )
        except Exception as e:
            print(f"WebSocket error: {e}")

        return Response({
            "status": "success",
            "message_id": message.id,
            "content": message.content,
            "file_url": message.file.url if message.file else None
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
def toggle_like(request, conversation_id, message_id):
    try:
        # Get message with conversation verification
        message = Message.objects.select_related('conversation').get(
            id=message_id,
            conversation_id=conversation_id
        )
        user = request.user
        
        # Verify participant
        if user not in [message.conversation.initiator, message.conversation.receiver]:
            return Response(
                {"error": "Not a conversation participant"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle like
        with transaction.atomic():
            if user in message.likes.all():
                message.likes.remove(user)
                action = "unliked"
            else:
                message.likes.add(user)
                action = "liked"
            message.update_like_count()
        
        # WebSocket broadcast
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation_id}",
                {
                    "type": "message.liked",
                    "message_id": message_id,
                    "user_id": user.id,
                    "action": action,
                    "like_count": message.like_count
                }
            )
        except Exception as e:
            print(f"WebSocket error: {e}")

        return Response({
            "status": "success",
            "action": action,
            "like_count": message.like_count,
            "is_liked": action == "liked"
        })

    except Message.DoesNotExist:
        return Response(
            {"error": "Message not found in this conversation"},
            status=status.HTTP_404_NOT_FOUND
        )
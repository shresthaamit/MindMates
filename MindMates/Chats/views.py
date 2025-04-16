from datetime import timezone
from django.shortcuts import render
from .models import Conversation,Message
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from Users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer,MessageSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect, reverse

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
        # print ("Conversation already exists.")
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
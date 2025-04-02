from django.shortcuts import render
from .models import Conversation
from rest_framework.decorators import api_view
from rest_framework.response import Response
from Users.models import User
from .serializers import ConversationListSerializer, ConversationSerializer
from django.db.models import Q
from django.shortcuts import redirect, reverse

# Create your views here.
@api_view(['POST'])
def create_conversation(request):
    data = request.data
    username = data.pop('username')
    try:
        participate = User.objects.get(username=username)
        
    except User.DoesNotExist:
        return Response({"message": "You can only chat with existed user."})
    
    conversation = Conversation.objects.filter(Q(initiator= request.user,receiver=participate)|Q(initiator=participate,receiver=request.user))
    if conversation.exists():
        return redirect(reverse('get_conversation',args=(conversation[0].id,)))
    else :  
        conversation = Conversation.objects.create(initiator=request.user,receiver=participate)
        return Response(ConversationSerializer(instance=conversation).data)
    
@api_view(['GET'])
def get_conversation(request, convo_id):
    conversation = Conversation.objects.filter(id = convo_id)
    if not conversation.exists():
        return Response({'message': 'Conversation doesnot exist'})
    
    else:
        serializer = ConversationSerializer(instance=conversation[0])
        return Response(serializer.data)

@api_view(['GET'])
def conversations(request):
    conversationlist  = Conversation.objects.filter(Q(initiator=request.user)|Q(receiver=request.user))
    serializer  = ConversationSerializer(instance=conversationlist, many=True)
    return Response(serializer.data)
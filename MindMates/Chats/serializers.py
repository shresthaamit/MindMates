from .models import Conversation, Message
from Users.serializers import UserSerializer
from rest_framework import serializers

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        exclude = ['conversation']
        
        
        
class ConversationListSerializer(serializers.ModelSerializer):
    initiator = UserSerializer()
    receiver = UserSerializer()
    last_message = serializers.SerializerMethodField()
    class Meta:
        model = Conversation
        fields = ['initiator', 'created_at', 'last_message']

    def get_last_message(self,instance):
        message =   instance.message_set.first()
        return MessageSerializer(message).data


class ConversationSerializer(serializers.ModelSerializer):
    initiator = UserSerializer()
    receiver = UserSerializer()
    message_set = MessageSerializer(many=True, source='messages') 
    
    class Meta:
        model = Conversation
        fields = ['initiator', 'receiver','message_set']
    
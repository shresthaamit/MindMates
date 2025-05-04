from .models import Conversation, Message
from Users.serializers import UserSerializer
from rest_framework import serializers

class MessageSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'file', 'file_url', 'created_at', 'is_read']
        read_only_fields = ['sender', 'created_at', 'is_read']
        
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
        
        
        
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
        
class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False)
    content = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Message
        fields = ['content', 'file']
    
class MessageLikeSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'like_count', 'is_liked']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        return request and request.user in obj.likes.all()
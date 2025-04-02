import base64
import json
import secrets
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.files.base import ContentFile
from Users.models import User
from .models import Conversation,Message
from .serializers import MessageSerializer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print("Connecting")
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
        
    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        chat_type = {'type':'chat_message'}
        return_dict ={**chat_type, **text_data_json}
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, return_dict,
        )
        
    def chat_message(self, event):
        text_data_json = event.copy()
        text_data_json.pop("type")
        message,attachment = (
            text_data_json.get("attachment"),
            text_data_json['message']
        )
        conversation = Conversation.objects.get(id=int(self.room_name))
        sender = self.scope['user']
        if attachment:
            file_str, file_ext = attachment['data'],attachment['format']
            
            file_data  = ContentFile(
                base64.b64encode(file_str),name=f"{secrets.token_hex(8)}.file{file_ext}"
            )
            _message = Message.objects.create(
                sender =sender,
                text = message,
                conversation_id = conversation
                
            )
            
        else:
            _message = Message.objects.create(
                sender=sender,
                text=message,
                conversation_id=conversation,
            )
            
        serializer = MessageSerializer(instance=_message)
        self.send(
            text_data=json.dumps(serializer.data)
        )
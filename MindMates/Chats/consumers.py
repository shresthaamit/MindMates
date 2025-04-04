import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import Conversation, Message
from Users.models import User
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Verify user has permission to access this conversation
        if not await self.verify_conversation_access():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    @database_sync_to_async
    def verify_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            user = self.scope["user"]
            return user == conversation.initiator or user == conversation.receiver
        except Conversation.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']

        # Save message to database
        message_obj = await self.save_message(message, sender_id)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'timestamp': str(message_obj.created_at)
            }
        )

    @database_sync_to_async
    def save_message(self, message_content, sender_id):
        conversation = Conversation.objects.get(id=self.conversation_id)
        sender = User.objects.get(id=sender_id)
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=message_content
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))
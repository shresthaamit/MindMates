from datetime import timezone
import json
import base64
import uuid
from django.core.files.base import ContentFile
from django.db import transaction
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Conversation, Message
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.serializers.json import DjangoJSONEncoder

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.awaiting_auth = True
        print("\n=== New connection attempt ===")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            if self.awaiting_auth:
                if data.get('type') == 'auth':
                    if await self.authenticate_token(data['token']):
                        await self.complete_connection()
                        return
                await self.close(code=4001)
                return
            
            if data.get('type') == 'chat_message':
                await self.process_chat_message(data)
                
            if data.get('type') == 'mark_read':
                await self.mark_message_as_read(data['message_id'])
            if data.get('type') == 'edit_message':
                await self.handle_edit_message(data)
                
            if data.get('type') == 'delete_message':
                await self.handle_delete_message(data)
            if data.get('type') == 'file_upload':
                await self.handle_file_upload(
                data.get('file_data'),
                data.get('content', '')
                )
            if data.get('type') == 'like_message':
                await self.handle_like(data['message_id'])
                
                
        except Exception as e:
            print(f"Error: {str(e)}")
            await self.close(code=4000)

    async def process_chat_message(self, data):
        message_content = data.get('message', '').strip()
        file_data = data.get('file')    
        if not message_content and not file_data:
            return
            
        # Get conversation info and save message
        conversation, saved_message = await self.save_message(message_content,file_data)
        
        if not conversation:
            await self.close(code=4003)
            return
            
        # Prepare response
        response = {
            'type': 'chat_message',
            'message_id': saved_message.id,
            'content': message_content,
            'file_url': saved_message.file.url if saved_message.file else None,
            'sender': await self.get_user_data(self.user),
            'receiver': await self.get_other_user_data(conversation),
            'timestamp': saved_message.created_at.isoformat(),
            'is_read': False
        }
        
        # Broadcast message
        await self.broadcast_message(response)
        
    @database_sync_to_async
    def save_message(self, content, file_data=None):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message(conversation=conversation, sender=self.user, content=content)
            
            if file_data:
                # Handle base64 file upload
                format, file_str = file_data.split(';base64,')
                ext = format.split('/')[-1]
                file = ContentFile(base64.b64decode(file_str), name=f'{uuid.uuid4()}.{ext}')
                message.file = file
            
            message.save()
            return conversation, message
        except Exception:
            print(f"Error saving message: {e}")
            return None, None

    @database_sync_to_async
    def get_conversation_and_save_message(self, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            return conversation, message
        except Exception:
            return None, None

    @database_sync_to_async
    def get_user_data(self, user):
        return {
            'id': user.id,
            'username': user.username
        }

    @database_sync_to_async
    def get_other_user_data(self, conversation):
        other_user = conversation.receiver if self.user == conversation.initiator else conversation.initiator
        return {
            'id': other_user.id,
            'username': other_user.username
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data'], cls=DjangoJSONEncoder))

    @database_sync_to_async
    def authenticate_token(self, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            self.user = jwt_auth.get_user(validated_token)
            self.scope['user'] = self.user
            return True
        except Exception:
            return False

    async def complete_connection(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        if await self.verify_conversation_access():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            self.awaiting_auth = False
            print(f"User {self.user.username} connected successfully")
        else:
            await self.close(code=4003)

    @database_sync_to_async
    def verify_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in [conversation.initiator, conversation.receiver]
        except Conversation.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"User disconnected with code {close_code}")
        
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        Message.objects.filter(
        id=message_id,
        conversation_id=self.conversation_id,
        is_read=False
         ).update(is_read=True)
        
# start  edit delete
    async def handle_edit_message(self, data):
        success = await self.edit_message_db(
            data['message_id'],
            data['new_content']
        )
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message.edited',
                    'message_id': data['message_id'],
                    'new_content': data['new_content'],
                    'edited_at': timezone.now().isoformat()
                }
            )

    async def handle_delete_message(self, data):
        success = await self.delete_message_db(data['message_id'])
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message.deleted',
                    'message_id': data['message_id']
                }
            )

    @database_sync_to_async
    def edit_message_db(self, message_id, new_content):
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.scope['user'],
                is_deleted=False
            )
            message.content = new_content
            message.is_edited = True
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async 
    def delete_message_db(self, message_id):
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.scope['user']
            )
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save()
            return True
        except Message.DoesNotExist:
            return False
    @database_sync_to_async
    def handle_file_upload(self, file_data, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            
            # Process base64 file
            format, file_str = file_data.split(';base64,')
            ext = format.split('/')[-1]
            file = ContentFile(
                base64.b64decode(file_str),
                name=f'{uuid.uuid4()}.{ext}'
            )
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content,
                file=file,
                file_name=file.name
            )
            
            return {
                'type': 'file_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'file_url': message.file.url,
                    'sender': {
                        'id': self.user.id,
                        'username': self.user.username
                    },
                    'timestamp': message.created_at.isoformat()
                }
            }
        except Exception as e:
            print(f"File upload error: {str(e)}")
            return None
    @database_sync_to_async
    def handle_like(self, message_id):
        message = Message.objects.get(id=message_id)
        user = self.user
        
        with transaction.atomic():
            if user in message.likes.all():
                message.likes.remove(user)
                action = "unliked"
            else:
                message.likes.add(user)
                action = "liked"
            message.update_like_count()
        
        return {
            'type': 'message.liked',
            'message_id': message_id,
            'user_id': user.id,
            'action': action,
            'like_count': message.like_count
        }
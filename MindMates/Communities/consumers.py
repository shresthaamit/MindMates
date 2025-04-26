import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Community, CommunityMessage
from rest_framework_simplejwt.authentication import JWTAuthentication

class CommunityChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.awaiting_auth = True
        self.community_id = self.scope['url_route']['kwargs']['pk']
        print(f"\n=== New community connection attempt for community {self.community_id} ===")

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
                await self.process_community_message(data)
                
            if data.get('type') == 'edit_message':
                await self.handle_edit_message(data)
                
            if data.get('type') == 'delete_message':
                await self.handle_delete_message(data)
                
        except Exception as e:
            print(f"Error: {str(e)}")
            await self.close(code=4000)

    async def process_community_message(self, data):
        message_content = data.get('message', '').strip()
        if not message_content:
            return
            
        # Save message to database
        saved_message = await self.save_community_message(message_content)
        if not saved_message:
            await self.close(code=4003)
            return
            
        # Prepare response
        response = {
            'type': 'chat_message',
            'message_id': saved_message.id,
            'content': message_content,
            'sender': await self.get_user_data(self.user),
            'timestamp': saved_message.created_at.isoformat(),
            'is_edited': False
        }
        
        # Broadcast message to community group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'data': response
            }
        )

    @database_sync_to_async
    def save_community_message(self, content):
        try:
            community = Community.objects.get(id=self.community_id)
            message = CommunityMessage.objects.create(
                community=community,
                sender=self.user,
                content=content
            )
            return message
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def get_user_data(self, user):
        return {
            'id': user.id,
            'username': user.username
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def authenticate_token(self, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            self.user = jwt_auth.get_user(validated_token)
            self.scope['user'] = self.user
            return True
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False

    async def complete_connection(self):
        self.room_group_name = f'community_{self.community_id}'
        
        if await self.verify_community_membership():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            self.awaiting_auth = False
            print(f"User {self.user.username} connected to community {self.community_id}")
        else:
            await self.close(code=4003)

    @database_sync_to_async
    def verify_community_membership(self):
        try:
            community = Community.objects.get(id=self.community_id)
            return community.members.filter(id=self.user.id).exists()
        except Community.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"User disconnected from community chat with code {close_code}")
        
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
            message = CommunityMessage.objects.get(
                id=message_id,
                sender=self.user,
                is_deleted=False
            )
            message.content = new_content
            message.is_edited = True
            message.save()
            return True
        except CommunityMessage.DoesNotExist:
            return False

    @database_sync_to_async 
    def delete_message_db(self, message_id):
        try:
            message = CommunityMessage.objects.get(
                id=message_id,
                sender=self.user
            )
            message.is_deleted = True
            message.save()
            return True
        except CommunityMessage.DoesNotExist:
            return False
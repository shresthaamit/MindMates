import json
import re
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Community, CommunityMessage
from rest_framework_simplejwt.authentication import JWTAuthentication

class CommunityChatConsumer(AsyncWebsocketConsumer):
    WS_CLOSE_CODES = {
        400: 4000,  # Bad Request
        401: 4001,  # Unauthorized
        403: 4003,  # Forbidden
        404: 4004,  # Not Found
        413: 4009,  # Payload Too Large
        415: 4010,  # Unsupported Media Type
        500: 4500   # Internal Server Error
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024 
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx']
    
    async def connect(self):
        await self.accept()
        self.awaiting_auth = True 
        self.connected = True
        self.authenticated = False
        self.close_code = None
        self.community_id = self.scope['url_route']['kwargs']['pk']
        print(f"\n=== New community connection attempt for community {self.community_id} ===")

    async def receive(self, text_data):
        try:
            if not hasattr(self, 'awaiting_auth'):
                self.awaiting_auth = True
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
            
            if data.get('type') == 'file_share':
                await self.process_file_share(data)
                
            if data.get('type') == 'edit_message':
                await self.handle_edit_message(data)
                
            if data.get('type') == 'delete_message':
                await self.handle_delete_message(data)
                
            else:
                await self.send_error("Invalid message type", status=400)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            await self.send_error("Internal server error", status=500)
    async def send_error(self, message, status=400):
        """Safe error sending that handles closed connections"""
        if not self.connected or hasattr(self, 'close_code'):
            return
            
        error_response = {
            'type': 'error',
            'message': message,
            'status': status,
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            await self.send(text_data=json.dumps(error_response))
        except Exception as e:
            print(f"Could not send error message: {str(e)}")
            return
            
        ws_code = self.WS_CLOSE_CODES.get(status, 4000)
        try:
            await self.close(code=ws_code)
            self.close_code = ws_code
            self.connected = False
        except Exception as e:
            print(f"Could not close connection cleanly: {str(e)}")
    async def send_recent_messages(self):
        """Send last 20 messages when user connects"""
        messages = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'message_history',
            'messages': messages
        }))

    @database_sync_to_async
    def get_recent_messages(self):
        return list(CommunityMessage.objects.filter(
            community_id=self.community_id,
            is_deleted=False
        ).order_by('-created_at')[:20].values(
            'id', 'content', 'file', 'file_name', 'sender__username', 'created_at'
        ))
    async def process_community_message(self, data):
        message_content = data.get('message', '').strip()
        if not message_content:
            await self.send_error("Message cannot be empty", status=400)
            return
            
        # Save message to database
        saved_message = await self.save_community_message(message_content)
        if not saved_message:
            await self.send_error("Failed to save message", status=500)
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
        await self.broadcast_message(response)
    async def process_file_share(self, data):
        """Handles both direct uploads (Base64) and URL shares"""
        file_name = data.get('file_name')
        message = data.get('message', '')
        
        # Case 1: Direct file upload (Base64)
        if 'file_data' in data:
            try:
                import base64
                from django.core.files.base import ContentFile
                
                # Extract Base64 data (handle data: URLs)
                header, encoded_data = data['file_data'].split(',', 1)
                file_bytes = base64.b64decode(encoded_data)
                file_size = len(file_bytes)
                
                # Validate size
                if file_size > self.MAX_FILE_SIZE:
                    await self.send_error(f"File too large (max {self.MAX_FILE_SIZE//(1024*1024)}MB)", 413)
                    return
                    
                # Create Django file object
                file_content = ContentFile(file_bytes, name=file_name)
                
                # Save to DB
                saved_message = await self.save_file_message(
                    file=file_content,  # Store in FileField
                    file_name=file_name,
                    file_size=file_size,
                    content=message
                )
                
            except Exception as e:
                await self.send_error(f"Upload failed: {str(e)}", 500)
                return

        # Case 2: URL sharing (existing functionality)
        elif 'file_url' in data:
            file_url = data['file_url']
            file_size = data.get('file_size', 0)
            
            if not file_url.startswith(('http://', 'https://')):
                await self.send_error("Invalid URL (must start with http:// or https://)", 400)
                return

            saved_message = await self.save_file_message(
                file_url=file_url,
                file_name=file_name,
                file_size=file_size,
                content=message
            )

        else:
            await self.send_error("Provide either 'file_data' (Base64) or 'file_url'", 400)
            return

        # Broadcast to all clients
        await self.broadcast_message({
            'type': 'file_message',
            'message_id': saved_message.id,
            'file_url': saved_message.file.url if saved_message.file else saved_message.file_url,
            'file_name': saved_message.file_name,
            'file_size': saved_message.file_size,
            'sender': await self.get_user_data(self.user),
            'timestamp': saved_message.created_at.isoformat()
        })
        # Broadcast message to community group
    async def broadcast_message(self, response):
        await self.channel_layer.group_send(
        self.room_group_name,
        {
            'type': 'chat.message',
            'data': response
        }
        )
    @database_sync_to_async
    def save_file_message(self, file=None, file_url=None, file_name=None, file_size=None, content=''):
        """Handles both file types in one method"""
        try:
            community = Community.objects.get(id=self.community_id)
            return CommunityMessage.objects.create(
                community=community,
                sender=self.user,
                content=content,
                file=file,       # For direct uploads
                file_url=file_url,  # For URL shares
                file_name=file_name,
                file_size=file_size
            )
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return None

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
            self.authenticated = True
            await self.add_user_to_community_online_list()
            print(f"User {self.user.username} connected")
            print(f"User {self.user.username} connected to community {self.community_id}")
        else:
            await self.close(code=4003)
    @database_sync_to_async
    def add_user_to_community_online_list(self):
        community = Community.objects.get(id=self.community_id)
        community.online_members.add(self.user)
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
            message.deleted_at = timezone.now() 
            message.save()
            return True
        except CommunityMessage.DoesNotExist:
            return False
    
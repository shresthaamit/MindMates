import json
import re
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Community, CommunityMessage
from rest_framework_simplejwt.authentication import JWTAuthentication

class CommunityChatConsumer(AsyncWebsocketConsumer):
    
    MAX_FILE_SIZE = 10 * 1024 * 1024 
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx']
    
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
    async def send_error(self, message, http_code=400):
        """Send error message and close connection with proper WebSocket code"""
        error_response = {
            'type': 'error',
            'message': message,
            'http_code': http_code,
            'timestamp': timezone.now().isoformat()
        }
        await self.send(text_data=json.dumps(error_response))
        
        # Convert HTTP code to valid WebSocket close code
        ws_code = self.WS_CLOSE_CODES.get(http_code, 4000)
        await self.close(code=ws_code)
    # async def send_error(self, message, status=400):
    #     error_response = {
    #         'type': 'error',
    #         'message': message,
    #         'status': status,
    #         'timestamp': timezone.now().isoformat()
    #     }
    #     await self.send(text_data=json.dumps(error_response))
    #     if status >= 400:
    #         await self.close(code=status)
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
        """Handle file sharing with complete validation"""
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        message = data.get('message', '')
        
        # Validate required fields
        if not all([file_url, file_name, file_size]):
            await self.send_error("Missing file data (url, name, or size)", status=400)
            return

        # Validate file size
        try:
            file_size = int(file_size)
            if file_size > self.MAX_FILE_SIZE:
                await self.send_error(
                    f"File too large (max {self.MAX_FILE_SIZE//(1024*1024)}MB)", 
                    status=413
                )
                return
            if file_size <= 0:
                await self.send_error("Invalid file size", status=400)
                return
        except (ValueError, TypeError):
            await self.send_error("Invalid file size format", status=400)
            return

        # Validate file type
        file_ext = '.' + file_url.split('.')[-1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            await self.send_error(
                f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
                status=415
            )
            return

        # Sanitize filename
        safe_name = re.sub(r'[^\w\-_. ]', '', file_name)
        if safe_name != file_name:
            await self.send(json.dumps({
                'type': 'warning',
                'message': 'Filename was sanitized for security',
                'original_name': file_name,
                'safe_name': safe_name
            }))
            file_name = safe_name

        # Save to database
        saved_message = await self.save_file_message(
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            content=message
        )
        
        if not saved_message:
            await self.send_error("Failed to save file metadata", status=500)
            return

        # Broadcast to group
        response = {
            'type': 'file_message',
            'message_id': saved_message.id,
            'file_url': file_url,
            'file_name': file_name,
            'file_size': file_size,
            'message': message,
            'sender': await self.get_user_data(self.user),
            'timestamp': saved_message.created_at.isoformat()
        }
        await self.broadcast_message(response)
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
    def save_file_message(self, file_url, file_name, file_size, content):
        try:
            if CommunityMessage.objects.filter(file_url=file_url).exists():
                return None 
            community = Community.objects.get(id=self.community_id)
            message = CommunityMessage.objects.create(
                community=community,
                sender=self.user,
                content=content,
                file_url=file_url,
                file_name=file_name,
                file_size=file_size
            )
            return message
        except Exception as e:
            print(f"Error saving file message: {str(e)}")
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
    
import json
import base64
import uuid
from datetime import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.db import transaction
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Conversation, Message
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept connection immediately
        await self.accept()
        self.awaiting_auth = True
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        self.user = None
        print(f"New WebSocket connection for conversation: {self.conversation_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # --- Authentication ---
            if self.awaiting_auth:
                if data.get("type") == "auth" and await self.authenticate_token(data.get("token")):
                    if await self.verify_conversation_access():
                        self.room_group_name = f"chat_{self.conversation_id}"
                        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                        self.awaiting_auth = False
                        print(f"User {self.user.username} connected successfully")
                        return
                    else:
                        print("Permission denied for conversation")
                        await self.close(code=4003)  # 4003 = permission denied
                        return
                else:
                    print("Authentication failed")
                    await self.close(code=4001)  # 4001 = auth failed
                    return
            
            # --- Chat message ---
            if data.get("type") == "chat_message":
                await self.process_chat_message(data)
            
            # --- Other actions ---
            if data.get("type") == "mark_read":
                await self.mark_message_as_read(data['message_id'])
            if data.get("type") == "edit_message":
                await self.handle_edit_message(data)
            if data.get("type") == "delete_message":
                await self.handle_delete_message(data)
            if data.get("type") == "file_upload":
                saved_msg = await self.handle_file_upload(data.get("file_data"), data.get("content", ""))
                if saved_msg:
                    await self.broadcast_message(saved_msg)
            if data.get("type") == "like_message":
                await self.handle_like(data['message_id'])
        
        except Exception as e:
            print(f"Error in receive: {e}")
            await self.close(code=4000)

    # --- Message processing ---
    async def process_chat_message(self, data):
        content = data.get("message", "").strip()
        file_data = data.get("file")
        if not content and not file_data:
            return
        
        conversation, saved_message = await self.save_message(content, file_data)
        if not conversation:
            await self.close(code=4003)
            return
        
        message_data = {
            "type": "chat_message",
            "message_id": saved_message.id,
            "content": saved_message.content,
            "file_url": saved_message.file.url if saved_message.file else None,
            "sender": await self.get_user_data(self.user),
            "receiver": await self.get_other_user_data(conversation),
            "timestamp": saved_message.created_at.isoformat(),
            "is_read": False
        }
        await self.broadcast_message(message_data)

    async def broadcast_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "data": message}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["data"], cls=DjangoJSONEncoder))

    # --- JWT Auth ---
    @database_sync_to_async
    def authenticate_token(self, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            self.user = jwt_auth.get_user(validated_token)
            self.scope["user"] = self.user
            return True
        except Exception:
            return False

    # --- Conversation access ---
    @database_sync_to_async
    def verify_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in [conversation.initiator, conversation.receiver]
        except Conversation.DoesNotExist:
            return False

    # --- Save message ---
    @database_sync_to_async
    def save_message(self, content, file_data=None):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message(conversation=conversation, sender=self.user, content=content)
            
            if file_data:
                fmt, file_str = file_data.split(';base64,')
                ext = fmt.split('/')[-1]
                message.file = ContentFile(base64.b64decode(file_str), name=f"{uuid.uuid4()}.{ext}")
            
            message.save()
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=["updated_at"])
            return conversation, message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None, None

    async def message_edited(self, event):
        """Send edited message data to connected clients."""
        await self.send(text_data=json.dumps({
            "type": "message_edited",
            "message_id": event["message_id"],
            "new_content": event["new_content"],
            "edited_at": event["edited_at"],
        }))

    async def message_deleted(self, event):
        """Notify clients that a message was deleted."""
        await self.send(text_data=json.dumps({
            "type": "message_deleted",
            "message_id": event["message_id"],
        }))
    @database_sync_to_async
    def get_user_data(self, user):
        return {"id": user.id, "username": user.username}

    @database_sync_to_async
    def get_other_user_data(self, conversation):
        other = conversation.receiver if self.user == conversation.initiator else conversation.initiator
        return {"id": other.id, "username": other.username}

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.select_related("conversation").get(
                id=message_id, conversation_id=self.conversation_id
            )
            if message.conversation.receiver_id == self.user.id:
                message.is_read = True
                message.save()
                return True
            return False
        except Message.DoesNotExist:
            return False

  
    async def handle_edit_message(self, data):
        success = await self.edit_message_db(data["message_id"], data["new_content"])
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message.edited",
                    "message_id": data["message_id"],
                    "new_content": data["new_content"],
                    "edited_at": timezone.now().isoformat()
                }
            )

    async def handle_delete_message(self, data):
        success = await self.delete_message_db(data["message_id"])
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "message.deleted", "message_id": data["message_id"]}
            )

    @database_sync_to_async
    def edit_message_db(self, message_id, new_content):
        try:
            msg = Message.objects.get(id=message_id, sender=self.user, is_deleted=False)
            msg.content = new_content
            msg.is_edited = True
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_message_db(self, message_id):
        try:
            msg = Message.objects.get(id=message_id, sender=self.user)
            msg.is_deleted = True
            msg.deleted_at = timezone.now()
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def handle_file_upload(self, file_data, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            fmt, file_str = file_data.split(';base64,')
            ext = fmt.split('/')[-1]
            file = ContentFile(base64.b64decode(file_str), name=f"{uuid.uuid4()}.{ext}")
            message = Message.objects.create(conversation=conversation, sender=self.user, content=content, file=file)
            return {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "file_url": message.file.url,
                    "sender": {"id": self.user.id, "username": self.user.username},
                    "timestamp": message.created_at.isoformat(),
                }
            }
        except Exception as e:
            print(f"File upload error: {e}")
            return None

    @database_sync_to_async
    def handle_like(self, message_id):
        try:
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
                "type": "message.liked",
                "message_id": message_id,
                "user_id": user.id,
                "action": action,
                "like_count": message.like_count
            }
        except Exception as e:
            print(f"Like error: {e}")
            return None

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"User disconnected with code {close_code}")

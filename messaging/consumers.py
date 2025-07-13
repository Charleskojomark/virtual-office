import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Conversation, Message
from settings.models import Profile
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
            
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Verify conversation and mark user as online
        if await self.verify_conversation():
            await self.mark_user_online(True)
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notify others in conversation about online status
            await self.notify_presence(True)
        else:
            await self.close(code=4004)  # Not found

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.mark_user_online(False)
            await self.notify_presence(False)

    @sync_to_async
    def verify_conversation(self):
        try:
            return Conversation.objects.filter(
                id=self.conversation_id,
                participants=self.user
            ).exists()
        except Exception as e:
            print(f"Conversation verification error: {e}")
            return False

    @sync_to_async
    def mark_user_online(self, status):
        """Update user's online status in database"""
        try:
            profile = Profile.objects.get(user=self.user)
            profile.is_online = status
            profile.last_seen = timezone.now()
            profile.save()
        except ObjectDoesNotExist:
            # Create profile if it doesn't exist
            Profile.objects.create(user=self.user, is_online=status)
        except Exception as e:
            print(f"Error updating online status: {e}")

    async def notify_presence(self, is_online):
        """Notify conversation participants about status change"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence.update',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online' if is_online else 'offline',
                'timestamp': timezone.now().isoformat()
            }
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            # Handle different message types
            if data.get('type') == 'heartbeat':
                await self.handle_heartbeat()
            elif 'message' in data:
                await self.handle_message(data['message'])
            else:
                await self.send_error("Invalid message format")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            print(f"WebSocket receive error: {e}")
            await self.send_error("Internal server error")

    async def handle_heartbeat(self):
        """Update last_seen timestamp for active connection"""
        await self.mark_user_online(True)

    async def handle_message(self, message_text):
        """Process and broadcast chat messages"""
        if not message_text.strip():
            return

        message_obj = await self.save_message(message_text)
        if not message_obj:
            return

        await self.broadcast_message(message_obj)

    @sync_to_async
    def save_message(self, message_text):
        """Save message to database and update conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                text=message_text
            )
            
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return {
                'id': message.id,
                'text': message.text,
                'timestamp': message.timestamp.isoformat(),
                'sender_id': self.user.id,
                'sender_username': self.user.username
            }
        except Exception as e:
            print(f"Message save error: {e}")
            return None

    async def broadcast_message(self, message_obj):
        """Send message to all conversation participants"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message_obj['text'],
                'sender_id': message_obj['sender_id'],
                'sender_username': message_obj['sender_username'],
                'timestamp': message_obj['timestamp'],
                'message_id': message_obj['id'],
                'is_sent': False,
                'user': {
                    'name': self.user.username,
                    'avatar': await self.get_user_avatar(),
                    'initials': self.user.username[:2].upper(),
                    'status': 'online'  # Assume sender is online when sending
                }
            }
        )

    @sync_to_async
    def get_user_avatar(self):
        """Get user avatar URL with fallback"""
        try:
            return self.user.profile.profile_picture.url
        except:
            return '/static/default-avatar.png'

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Handler for chat messages
    async def chat_message(self, event):
        """Receive broadcasted chat messages"""
        if event['sender_id'] != self.user.id:  # Don't echo to sender
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                **event
            }))

    # Handler for presence updates
    async def presence_update(self, event):
        """Handle online/offline status notifications"""
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
        
        
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
    async def disconnect(self, close_code):
        pass
        
    async def receive(self, text_data):
        pass
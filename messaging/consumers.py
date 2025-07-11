import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Conversation, Message
from asgiref.sync import sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
            
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Verify conversation exists and user is a participant
        if await self.verify_conversation():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    @sync_to_async
    def verify_conversation(self):
        try:
            return Conversation.objects.filter(
                id=self.conversation_id,
                participants=self.user
            ).exists()
        except:
            return False

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            if not message.strip():
                return

            # Save message to database
            message_obj = await self.save_message(message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_obj['text'],
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'timestamp': message_obj['timestamp'],
                    'message_id': message_obj['id'],
                    'is_sent': True,
                    'user': {
                        'name': self.user.username,
                        'avatar': getattr(self.user, 'avatar', '/static/default-avatar.png'),
                        'initials': self.user.username[:2].upper()
                    }
                }
            )
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error in receive: {e}")

    @sync_to_async
    def save_message(self, message_text):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                text=message_text
            )
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return {
                'id': message.id,
                'text': message.text,
                'timestamp': message.timestamp.isoformat(),
            }
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    async def chat_message(self, event):
        # Don't send message back to sender
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'text': event['message'],
                'sender_id': event['sender_id'],
                'sender_username': event['sender_username'],
                'timestamp': event['timestamp'],
                'message_id': event['message_id'],
                'is_sent': False,
                'user': event['user']
            }))
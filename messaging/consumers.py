import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Conversation
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.group_name = f'chat_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        conversation_id = data.get('conversation_id')  # Assume passed from frontend
        conversation = Conversation.objects.get(id=conversation_id)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=message
        )
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': {'initials': self.user.username[:2].upper()},
                'is_sent': True
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'text': event['message'],
            'user': event['user'],
            'is_sent': event['is_sent']
        }))
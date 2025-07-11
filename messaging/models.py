# messaging/models.py
from django.db import models
from django.contrib.auth.models import User
from tasks.models import Notification

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} with {', '.join([p.username for p in self.participants.all()])}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Create notifications for all participants except sender
            for participant in self.conversation.participants.exclude(id=self.sender.id):
                Notification.objects.create(
                    user=participant,
                    message=f"New message from {self.sender.username}",
                    notification_type='chat',
                    related_id=self.conversation.id
                )

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.http import JsonResponse
from django.db.models import Q

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from dashboard.models import Activity
from .models import Message, Conversation
from django.contrib.auth.models import User
import json

@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        recipient = User.objects.get(id=data['recipient_id'])
        # Find or create conversation
        conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=data['text']
        )
        Activity.objects.create(
            user=request.user,
            action_type='MESSAGE_SENT',
            description=f"Sent message to {recipient.username}"
        )
        return JsonResponse({'status': 'success', 'id': message.id})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def messaging(request):
    # Filter conversations where the current user is a participant
    conversations = Conversation.objects.filter(participants=request.user).order_by('-created_at')
    
    # Get the active conversation (based on query parameter or default to first)
    conversation_id = request.GET.get('chat')
    active_conversation = None
    messages = []
    
    if conversation_id:
        try:
            active_conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
            messages = Message.objects.filter(conversation=active_conversation).order_by('timestamp')
        except Conversation.DoesNotExist:
            active_conversation = conversations.first() if conversations.exists() else None
    else:
        active_conversation = conversations.first() if conversations.exists() else None
    
    if active_conversation:
        messages = Message.objects.filter(conversation=active_conversation).order_by('timestamp')
    
    # Prepare conversation data for the template
    conversation_data = []
    for conv in conversations:
        # Get the other participant (not the current user)
        other_participant = conv.participants.exclude(id=request.user.id).first()
        if not other_participant:
            continue  # Skip if no other participant (edge case)
        
        # Get the last message for preview and timestamp
        last_message = Message.objects.filter(conversation=conv).order_by('-timestamp').first()
        
        conversation_data.append({
            'id': conv.id,
            'participant_name': other_participant.username,
            'participant_avatar': getattr(other_participant, 'avatar', '/static/default-avatar.png'),
            'participant_initials': other_participant.username[:2].upper(),
            'last_message_preview': last_message.text[:50] + '...' if last_message else '',
            'last_message_time': last_message.timestamp if last_message else conv.created_at,
            'unread_count': Message.objects.filter(conversation=conv, read=False).exclude(sender=request.user).count(),
        })
    
    # Prepare active conversation data
    active_chat_data = None
    if active_conversation:
        other_participant = active_conversation.participants.exclude(id=request.user.id).first()
        if other_participant:
            active_chat_data = {
                'id': active_conversation.id,
                'participant_name': other_participant.username,
                'participant_avatar': getattr(other_participant, 'avatar', '/static/default-avatar.png'),
                'participant_initials': other_participant.username[:2].upper(),
                'status': 'Online',  # You may need to implement actual status logic
            }
    
    # Prepare messages data
    messages_data = [
        {
            'sender': {
                'name': message.sender.username,
                'avatar': getattr(message.sender, 'avatar', '/static/default-avatar.png'),
                'initials': message.sender.username[:2].upper(),
            },
            'content': message.text,
            'timestamp': message.timestamp,
            'status': '✓' if message.read else '✓✓',  # Example status logic
            'attachment': None,  # Add attachment logic if needed
        } for message in messages
    ]
    
    context = {
        'chats': conversation_data,
        'active_chat': active_chat_data,
        'messages': messages_data,
        'notifications': {'count': 0},  # Placeholder; implement notification logic if needed
        'user': request.user,  # Pass the current user for sender comparison
    }
    
    return render(request, 'messaging/messaging.html', context)

@login_required
def messages_api(request, conversation_id):
    messages = Message.objects.filter(conversation_id=conversation_id).values('id', 'sender__username', 'text', 'timestamp')
    return JsonResponse({'messages': list(messages)})
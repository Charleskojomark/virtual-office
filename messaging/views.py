from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .models import Conversation, Message
from tasks.models import Notification
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

class MessageForm(forms.Form):
    recipient_id = forms.IntegerField()
    message = forms.CharField(max_length=1000, required=False)
    conversation_id = forms.IntegerField(required=False)
    attachment = forms.FileField(required=False)

@login_required
def messaging(request):
    # Get all conversations for the user, ordered by most recent activity
    conversations = Conversation.objects.filter(participants=request.user)\
                                       .order_by('-updated_at')\
                                       .prefetch_related('participants', 'messages')
    
    # Handle active conversation
    conversation_id = request.GET.get('chat')
    recipient_id = request.GET.get('recipient')
    active_conversation = None
    messages = []

    # Check if we're starting a new conversation
    if recipient_id and not conversation_id:
        try:
            recipient = User.objects.get(id=recipient_id)
            # Find existing conversation or create new one
            active_conversation = Conversation.objects.filter(participants=request.user)\
                                                    .filter(participants=recipient)\
                                                    .first()
            if not active_conversation:
                active_conversation = Conversation.objects.create()
                active_conversation.participants.add(request.user, recipient)
            conversation_id = active_conversation.id
        except User.DoesNotExist:
            pass

    # Get active conversation if specified
    if conversation_id:
        try:
            active_conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            messages = active_conversation.messages.order_by('timestamp')
            
            # Mark chat notifications as read (those containing conversation ID in message)
            Notification.objects.filter(
                user=request.user,
                is_read=False,
                message__contains=f"conversation:{conversation_id}"
            ).update(is_read=True)
            
            # Mark messages as read
            active_conversation.messages.filter(read=False)\
                                      .exclude(sender=request.user)\
                                      .update(read=True)
        except Conversation.DoesNotExist:
            active_conversation = conversations.first() if conversations.exists() else None
    else:
        active_conversation = conversations.first() if conversations.exists() else None

    # Prepare conversation list data
    conversation_data = []
    for conv in conversations:
        other_participant = conv.participants.exclude(id=request.user.id).first()
        if not other_participant:
            continue
            
        last_message = conv.messages.order_by('-timestamp').first()
        unread_count = conv.messages.filter(read=False)\
                                   .exclude(sender=request.user)\
                                   .count()
        
        conversation_data.append({
            'id': conv.id,
            'participant_name': other_participant.username,
            'participant_avatar': getattr(other_participant, 'avatar', '/static/default-avatar.png'),
            'participant_initials': other_participant.username[:2].upper(),
            'last_message_preview': last_message.text[:50] + '...' if last_message else '',
            'last_message_time': last_message.timestamp if last_message else conv.created_at,
            'unread_count': unread_count,
        })

    # Prepare active chat data
    active_chat_data = None
    if active_conversation:
        other_participant = active_conversation.participants.exclude(id=request.user.id).first()
        if other_participant:
            active_chat_data = {
    'id': active_conversation.id,
    'participant_id': other_participant.id,
    'participant_name': other_participant.username,
    'participant_avatar': getattr(other_participant, 'avatar', '/static/default-avatar.png'),
    'participant_initials': other_participant.username[:2].upper(),
    'status': 'Online' if other_participant.last_login and 
              (timezone.now() - other_participant.last_login).total_seconds() < 300 else 'Offline',
}

    # Paginate messages
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page', 1)
    messages_page = paginator.get_page(page_number)

    # Get all unread notifications
    all_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    # Separate chat and general notifications
    chat_notifications = []
    general_notifications = []
    
    for notification in all_notifications:
        if "conversation:" in notification.message:
            chat_notifications.append(notification)
        else:
            general_notifications.append(notification)

    # Prepare messages data for template
    messages_data = []
    for message in messages_page:
        messages_data.append({
            'sender': {
                'id': message.sender.id,
                'name': message.sender.username,
                'avatar': getattr(message.sender, 'avatar', '/static/default-avatar.png'),
                'initials': message.sender.username[:2].upper(),
            },
            'content': message.text,
            'timestamp': message.timestamp,
            'status': '✓✓' if message.read else '✓',
            'attachment': message.attachment,
            'is_sent': message.sender.id == request.user.id
        })

    context = {
        'chats': conversation_data,
        'active_chat': active_chat_data,
        'messages': messages_data,
        'chat_notifications': {
            'count': len(chat_notifications),
            'list': chat_notifications[:5]  # Only show 5 most recent
        },
        'general_notifications': {
            'count': len(general_notifications),
            'list': general_notifications[:5]  # Only show 5 most recent
        },
        'page_obj': messages_page,
        'all_users': User.objects.exclude(id=request.user.id)
    }

    return render(request, 'messaging/messaging.html', context)

@login_required
def send_message(request):
    logger.info(f"Received {request.method} request to /messaging/send/")
    
    if request.method != 'POST':
        logger.error("Invalid request method")
        return JsonResponse({
            'status': 'error',
            'error': 'Only POST requests are allowed'
        }, status=405)
    
    logger.info(f"POST data: {request.POST}, FILES: {request.FILES}")
    form = MessageForm(request.POST, request.FILES)
    
    if not form.is_valid():
        error_details = {
            'errors': form.errors.get_json_data(),
            'received_data': {
                'recipient_id': request.POST.get('recipient_id'),
                'message': request.POST.get('message'),
                'conversation_id': request.POST.get('conversation_id'),
                'has_attachment': bool(request.FILES.get('attachment'))
            }
        }
        logger.error(f"Form validation failed: {error_details}")
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid form data',
            'details': error_details
        }, status=400)
    
    try:
        recipient = User.objects.get(id=form.cleaned_data['recipient_id'])
        if recipient == request.user:
            raise ValueError("Cannot send message to yourself")
    except User.DoesNotExist:
        logger.error(f"Recipient not found: ID {form.cleaned_data['recipient_id']}")
        return JsonResponse({
            'status': 'error',
            'error': 'Recipient not found'
        }, status=404)
    except ValueError as e:
        logger.error(f"Invalid recipient: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

    try:
        conversation_id = form.cleaned_data.get('conversation_id')
        if conversation_id:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
            if not conversation.participants.filter(id=recipient.id).exists():
                raise ValueError("Recipient not in specified conversation")
        else:
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, recipient)
                logger.info(f"Created new conversation: {conversation.id}")
    except Conversation.DoesNotExist:
        logger.error(f"Conversation not found: ID {conversation_id}")
        return JsonResponse({
            'status': 'error',
            'error': 'Conversation not found'
        }, status=404)
    except ValueError as e:
        logger.error(f"Conversation error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

    try:
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=form.cleaned_data.get('message', ''),
            attachment=form.cleaned_data.get('attachment')
        )
        
        conversation.updated_at = timezone.now()
        conversation.save()
        
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"messaging_{conversation.id}",
                {
                    'type': 'chat.message',
                    'message': {
                        'id': message.id,
                        'text': message.text,
                        'timestamp': message.timestamp.isoformat(),
                        'is_sent': False,
                        'sender_id': request.user.id,
                        'user': {
                            'name': request.user.username,
                            'avatar': getattr(request.user, 'avatar', '/static/default-avatar.png'),
                            'initials': request.user.username[:2].upper()
                        },
                        'attachment': {
                            'url': message.attachment.url if message.attachment else None,
                            'name': message.attachment.name if message.attachment else None
                        }
                    }
                }
            )
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")

        # Create notification - use only fields that exist in your model
        Notification.objects.create(
            user=recipient,
            message=f"New message from {request.user.username} in conversation:{conversation.id}",
            related_url=f"/messaging/?chat={conversation.id}"
            # Remove notification_type and related_id if they don't exist in your model
        )

        logger.info(f"Message successfully sent: ID {message.id}")
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'conversation_id': conversation.id,
            'timestamp': message.timestamp.isoformat()
        })
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': 'Failed to send message',
            'details': str(e)
        }, status=500)

@login_required
def messages_api(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
        messages = conversation.messages.order_by('timestamp')
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'sender': {
                    'username': message.sender.username,
                    'avatar': getattr(message.sender, 'avatar', '/static/default-avatar.png'),
                },
                'text': message.text,
                'timestamp': message.timestamp,
                'read': message.read,
                'is_sent': message.sender.id == request.user.id,
                'attachment': {
                    'url': message.attachment.url if message.attachment else None,
                    'name': message.attachment.name if message.attachment else None
                },
            })

        return JsonResponse({'messages': messages_data})
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

@login_required
def mark_messages_read(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
        conversation.messages.filter(read=False)\
                           .exclude(sender=request.user)\
                           .update(read=True)
        return JsonResponse({'status': 'success'})
    except Conversation.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Conversation not found'}, status=404)

@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        # Get updated counts
        all_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        chat_count = sum(1 for n in all_notifications if "conversation:" in n.message)
        general_count = sum(1 for n in all_notifications if "conversation:" not in n.message)
        
        return JsonResponse({
            'status': 'success',
            'chat_count': chat_count,
            'general_count': general_count
        })
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Notification not found'}, status=404)
    
@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_notifications_count(request):
    if request.method == 'GET':
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'status': 'error'}, status=400)
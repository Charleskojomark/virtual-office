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
from django.db import transaction

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
    if recipient_id:
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
            
            # Mark chat notifications as read using notification_type and related_id
            Notification.objects.filter(
                user=request.user,
                is_read=False,
                notification_type='chat',
                related_id=conversation_id
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
        profile_picture = None
        if hasattr(other_participant, 'profile') and other_participant.profile.profile_picture:
            profile_picture = other_participant.profile.profile_picture.url
        conversation_data.append({
    'id': conv.id,
    'participant_id': other_participant.id,
    'participant_name': other_participant.username,
    'participant_avatar': profile_picture or '/static/default-avatar.png',
    'participant_initials': other_participant.username[:2].upper(),
    'last_message_preview': last_message.text[:50] + '...' if last_message else '',
    'last_message_time': last_message.timestamp if last_message else conv.created_at,
    'unread_count': unread_count,
    'status': (
        'Online' if (
            getattr(other_participant, 'profile', None) and 
            other_participant.profile.show_online_status and
            (other_participant.profile.is_online or 
             (timezone.now() - other_participant.profile.last_seen).total_seconds() < 300)
        ) else 'Offline'
    )
})

    # Prepare active chat data
    active_chat_data = None
    if active_conversation:
        other_participant = active_conversation.participants.exclude(id=request.user.id).first()
        if other_participant:
            profile_picture = None
            if hasattr(other_participant, 'profile') and other_participant.profile.profile_picture:
                profile_picture = other_participant.profile.profile_picture.url
                
            active_chat_data = {
                'id': active_conversation.id,
                'participant_id': other_participant.id,
                'participant_name': other_participant.username,
                'participant_avatar': profile_picture or '/static/default-avatar.png',
                'participant_initials': other_participant.username[:2].upper(),
                'status': (
                    'Online' if (
                        getattr(other_participant, 'profile', None) and 
                        other_participant.profile.show_online_status and
                        (other_participant.profile.is_online or 
                        (timezone.now() - other_participant.profile.last_seen).total_seconds() < 300)
                    ) else 'Offline'
                )
            }

    # Paginate messages
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page', 1)
    messages_page = paginator.get_page(page_number)

    # Get all unread notifications and separate by type
    all_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    # Efficiently separate notifications using the type field
    chat_notifications = all_notifications.filter(notification_type='chat')
    general_notifications = all_notifications.exclude(notification_type='chat')

    # Prepare messages data for template
    messages_data = []
    for message in messages_page:
        messages_data.append({
            'sender': {
                'id': message.sender.id,
                'name': message.sender.username,
                'avatar': getattr(message.sender.profile, 'profile_picture', '/static/default-avatar.png'),
                'initials': message.sender.username[:2].upper(),
            },
            'content': message.text,
            'timestamp': message.timestamp,
            'status': '✓✓' if message.read else '✓',
            'attachment': {
                'url': message.attachment.url if message.attachment else None,
                'name': message.attachment.name if message.attachment else None
            },
            'is_sent': message.sender.id == request.user.id
        })

    context = {
        'chats': conversation_data,
        'active_chat': active_chat_data,
        'messages': messages_data,
        'chat_notifications': {
            'count': chat_notifications.count(),
            'list': chat_notifications[:5]  # Only show 5 most recent
        },
        'general_notifications': {
            'count': general_notifications.count(),
            'list': general_notifications[:5]  # Only show 5 most recent
        },
        'page_obj': messages_page,
        'all_users': User.objects.exclude(id=request.user.id).select_related('profile')
    }

    return render(request, 'messaging/messaging.html', context)

@login_required
@transaction.atomic
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
        is_new_conversation = False
        
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
                with transaction.atomic():
                    conversation = Conversation.objects.create()
                    conversation.participants.add(request.user, recipient)
                    is_new_conversation = True
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
        with transaction.atomic():
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=form.cleaned_data.get('message', ''),
                attachment=form.cleaned_data.get('attachment')
            )
            
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Get recipient profile data for the response
            recipient_profile = getattr(recipient, 'profile', None)
            recipient_avatar = (
                recipient_profile.profile_picture.url 
                if recipient_profile and recipient_profile.profile_picture 
                else '/static/default-avatar.png'
            )
            
            # Prepare response data
            response_data = {
                'status': 'success',
                'message_id': message.id,
                'conversation_id': conversation.id,
                'timestamp': message.timestamp.isoformat(),
                'is_new_conversation': is_new_conversation,
            }
            
            # Add conversation data if this is a new conversation
            if is_new_conversation:
                response_data['conversation_data'] = {
                    'id': conversation.id,
                    'participant_id': recipient.id,
                    'participant_name': recipient.username,
                    'participant_avatar': recipient_avatar,
                    'participant_initials': recipient.username[:2].upper(),
                    'last_message_preview': message.text[:50] + ('...' if len(message.text) > 50 else ''),
                    'last_message_time': message.timestamp,
                    'unread_count': 0,
                    'status': (
                        'Online' if (
                            recipient_profile and 
                            (recipient_profile.is_online or 
                            (timezone.now() - recipient_profile.last_seen).total_seconds() < 300)
                        ) else 'Offline'
                    )
                }

            # Send WebSocket message
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
                # Even if WebSocket fails, we still return success since message is saved
                pass

            Notification.objects.create(
                user=recipient,
                message=f"New message from {request.user.username}",
                notification_type='chat',
                related_url=f"/messaging/?chat={conversation.id}",
                related_id=conversation.id
            )

            logger.info(f"Message successfully sent: ID {message.id}")
            return JsonResponse(response_data)
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
        
        # Get updated counts using the type field
        chat_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            notification_type='chat'
        ).count()
        
        general_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).exclude(notification_type='chat').count()
        
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
        chat_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            notification_type='chat'
        ).count()
        
        general_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).exclude(notification_type='chat').count()
        
        return JsonResponse({
            'chat_count': chat_count,
            'general_count': general_count,
            'total_count': chat_count + general_count
        })
    return JsonResponse({'status': 'error'}, status=400)
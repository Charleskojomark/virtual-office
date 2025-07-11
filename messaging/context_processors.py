# tasks/context_processors.py
from django.contrib.auth.models import User
from tasks.models import Notification

def notifications(request):
    if request.user.is_authenticated:
        try:
            user_notifications = request.user.notifications.filter(is_read=False)
            return {
                'chat_notifications': {
                    'count': user_notifications.filter(notification_type='chat').count(),
                    'list': user_notifications.filter(notification_type='chat')[:10]
                },
                'general_notifications': {
                    'count': user_notifications.exclude(notification_type='chat').count(),
                    'list': user_notifications.exclude(notification_type='chat')[:10]
                }
            }
        except AttributeError:
            # Fallback if notifications relation doesn't exist
            return {
                'chat_notifications': {'count': 0, 'list': []},
                'general_notifications': {'count': 0, 'list': []}
            }
    return {}
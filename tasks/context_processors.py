# tasks/context_processors.py
from .models import Task, Notification
from django.db.models import Q

def task_and_notification_counts(request):
    if request.user.is_authenticated:
        task_count = Task.objects.filter(
            Q(user=request.user) | Q(assigned_to=request.user)
        ).distinct().count()
        notification_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        task_count = 0
        notification_count = 0

    return {
        'task_count': task_count,
        'notification_count': notification_count,
    }

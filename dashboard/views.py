from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from tasks.models import Task, Notification
from schedule.models import Event
from records.models import Record
from django.contrib.auth.models import User
from dashboard.models import Activity
from messaging.models import Message, Conversation
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
from django.http import JsonResponse

@login_required
def dashboard(request):
    # Fetch tasks where user is creator or assignee
    try:
        tasks = Task.objects.filter(
            models.Q(user=request.user) | models.Q(assigned_to=request.user)
        ).distinct()
        task_count = tasks.count()
        completed_tasks = tasks.filter(status='Completed').count()
        task_completion_percentage = (completed_tasks / task_count * 100) if task_count > 0 else 0
        remaining_tasks = task_count - completed_tasks
    except Task.DoesNotExist:
        task_count = completed_tasks = task_completion_percentage = remaining_tasks = 0

    # Fetch appointments and meetings (include events where user is creator or participant)
    upcoming_events = Event.objects.select_related('created_by').filter(
        models.Q(created_by=request.user) | models.Q(participants=request.user),
        start_time__gte=timezone.now()
    ).distinct().order_by('start_time')[:5]
    appointments = meetings = upcoming_events

    # Fetch messages
    try:
        conversations = Conversation.objects.filter(participants=request.user)
        messages = Message.objects.filter(conversation__in=conversations)
        unread_messages = messages.filter(read=False).exclude(sender=request.user).count()
    except (Conversation.DoesNotExist, Message.DoesNotExist):
        messages = []
        unread_messages = 0

    # Fetch recent activities
    # activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    # Change the activities query to:
    activities = Activity.objects.filter(user=request.user).select_related('user').order_by('-timestamp')[:5]

    # Fetch calendar events (current month ±1 month)
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + relativedelta(months=1) - timedelta(days=1))
    calendar_start = start_of_month - relativedelta(months=1)
    calendar_end = end_of_month + relativedelta(months=1)
    calendar_events = Event.objects.select_related('created_by').filter(
        models.Q(created_by=request.user) | models.Q(participants=request.user),
        start_time__date__range=[calendar_start, calendar_end]
    ).distinct().values('id', 'title', 'start_time')

    # Convert calendar events to JSON-serializable format
    calendar_events_json = [
        {
            'id': event['id'],
            'title': event['title'],
            'date': event['start_time'].isoformat() if event['start_time'] else None,
        }
        for event in calendar_events
    ]

    # Fetch notifications
    notifications = request.user.notifications.filter(is_read=False) if hasattr(request.user, 'notifications') else []

    # Get current date information for JavaScript
    now = timezone.now()
    today_iso = today.isoformat()

    context = {
        'user': request.user,
        'active_users': User.objects.filter(is_active=True).count(),
        'pending_tasks': tasks.filter(status='Pending').count(),
        'upcoming_events': Event.objects.filter(
            models.Q(created_by=request.user) | models.Q(participants=request.user),
            start_time__gte=timezone.now()
        ).count(),
        'total_records': Record.objects.filter(user=request.user).count(),
        'tasks': {
            'count': task_count,
            'remaining': remaining_tasks,
        },
        'task_completion_percentage': task_completion_percentage,
        'appointments': appointments,
        'messages': {
            'count': len(messages),
            'unread': unread_messages,
        },
        'meetings': meetings,
        'activities': activities,
        'notifications': {
            'count': notifications.count(),
            'chat': {
                'count': notifications.filter(notification_type='chat').count(),
                'list': notifications.filter(notification_type='chat')[:5]
            },
            'general': {
                'count': notifications.exclude(notification_type='chat').count(),
                'list': notifications.exclude(notification_type='chat')[:5]
            }
        },
        'now': now,
        'calendar_events_json': calendar_events_json,
        'calendar_month': today.month,
        'calendar_year': today.year,
        'today_iso': today_iso,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def task_updates(request):
    try:
        tasks = Task.objects.filter(
            models.Q(user=request.user) | models.Q(assigned_to=request.user)
        ).distinct()
        task_count = tasks.count()
        completed_tasks = tasks.filter(status='Completed').count()
        task_completion_percentage = (completed_tasks / task_count * 100) if task_count > 0 else 0
        remaining_tasks = task_count - completed_tasks
        return JsonResponse({
            'status': 'success',
            'tasks': {
                'count': task_count,
                'remaining': remaining_tasks,
                'completion_percentage': task_completion_percentage
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def activities(request):
    activities = Activity.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'dashboard/activities.html', {'activities': activities})
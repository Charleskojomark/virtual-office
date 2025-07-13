from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from .models import Task, Notification
from django.contrib.auth.models import User
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.db.models import Q
from dashboard.models import Activity

class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})

@login_required
def tasks(request):
    tasks = Task.objects.filter(
        models.Q(user=request.user) | models.Q(assigned_to=request.user)
    ).distinct()
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    users = User.objects.all().values('id', 'first_name', 'last_name', 'username')
    user_list = [
        {
            'id': user['id'],
            'full_name': f"{user['first_name']} {user['last_name']}".strip() or user['username'],
            'username': user['username']
        }
        for user in users
    ]
    context = {
        'tasks': tasks,
        'notifications': notifications,
        'users': user_list
    }
    return render(request, 'tasks/tasks.html', context)


@login_required
def bulk_complete_tasks(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_ids = data.get('task_ids', [])
            tasks = Task.objects.filter(
                Q(id__in=task_ids) & (Q(user=request.user) | Q(assigned_to=request.user))
            ).distinct()

            count = tasks.count()
            tasks.update(status='Completed')
            return JsonResponse({'status': 'success', 'message': f'{count} tasks marked as complete'})
        except (ValueError, KeyError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def task_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            assigned_to_ids = data.get('assigned_to', [])
            task = Task.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                due_date=data['due_date'],
                status=data['status'],
                priority=data.get('priority', 'Medium'),
                user=request.user
            )
            Activity.objects.create(
                user=request.user,
                action_type='TASK_CREATED',
                description=f'Created task: {task.title}'
            )
            if assigned_to_ids:
                assigned_users = User.objects.filter(id__in=assigned_to_ids)
                task.assigned_to.set(assigned_users)
            return JsonResponse({'status': 'success', 'id': task.id})
        except (KeyError, ValueError, User.DoesNotExist) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def task_detail(request, task_id):
    try:
        task = Task.objects.filter(
            models.Q(user=request.user) | models.Q(assigned_to=request.user),
            id=task_id
        ).distinct().get()
        assigned_to = [
            {
                'id': user.id,
                'full_name': user.get_full_name() or user.username,
                'username': user.username
            }
            for user in task.assigned_to.all()
        ]
        return JsonResponse({
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date.isoformat(),
            'status': task.status,
            'priority': task.priority,
            'assigned_to': assigned_to,
            'is_creator': task.user == request.user
        })
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found or you lack permission'}, status=404)

@login_required
def task_delete(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.filter(
                user=request.user,  # Only creator can delete
                id=task_id
            ).get()
            task.delete()
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found or you lack permission to delete'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def edit_task(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.filter(
                models.Q(user=request.user) | models.Q(assigned_to=request.user),
                id=task_id
            ).distinct().get()
            data = json.loads(request.body)
            assigned_to_ids = data.get('assigned_to', [])
            task.title = data['title']
            task.description = data.get('description', task.description)
            task.due_date = data['due_date']
            task.status = data['status']
            task.priority = data['priority']
            task.save()
            task.assigned_to.set(User.objects.filter(id__in=assigned_to_ids) if assigned_to_ids else [])
            return JsonResponse({'status': 'success', 'id': task.id})
        except Task.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found or you lack permission'}, status=404)
        except (KeyError, ValueError, User.DoesNotExist) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def bulk_delete_tasks(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_ids = data.get('task_ids', [])
            tasks = Task.objects.filter(
                id__in=task_ids,
                user=request.user  # Only creator can delete
            )
            count = tasks.count()
            tasks.delete()
            return JsonResponse({'status': 'success', 'message': f'{count} tasks deleted'})
        except (ValueError, KeyError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


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
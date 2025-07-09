from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task, Notification
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
import logging
import json
from collections import defaultdict
from dashboard.models import Activity

# Set up logging for debugging
logger = logging.getLogger(__name__)

def reports_view(request):
    # Get filter parameters from GET request
    date_filter = request.GET.get('date-filter', 'all')
    user_filter = request.GET.get('user-filter', 'all')

    # Log filter action using Activity model
    if user_filter != 'all' or date_filter != 'all':
        Activity.objects.create(
            user=request.user,
            action_type='REPORT_FILTERED',
            description=f"Applied report filters: date={date_filter}, user={user_filter}"
        )

    # Base queryset for tasks
    tasks = Task.objects.all()

    # Apply date filter
    today = timezone.now().date()
    if date_filter == 'today':
        tasks = tasks.filter(created_at__date=today)
    elif date_filter == 'week':
        start_of_week = today - timedelta(days=today.weekday())
        tasks = tasks.filter(created_at__date__gte=start_of_week)
    elif date_filter == 'month':
        tasks = tasks.filter(created_at__year=today.year, created_at__month=today.month)
    elif date_filter == 'year':
        tasks = tasks.filter(created_at__year=today.year)

    # Apply user filter - Fixed to handle ManyToManyField properly
    if user_filter != 'all':
        try:
            user_filter_id = int(user_filter)
            tasks = tasks.filter(Q(user__id=user_filter_id) | Q(assigned_to__id=user_filter_id)).distinct()
        except (ValueError, TypeError):
            logger.warning(f"Invalid user filter value: {user_filter}")
            # Keep all tasks if invalid filter

    # Summary data
    new_users = User.objects.filter(
        date_joined__year=today.year,
        date_joined__month=today.month
    )
    new_registrations = new_users.count()
    
    # Debug logging for new_registrations
    logger.debug(f"New registrations query: year={today.year}, month={today.month}, count={new_registrations}")

    # Calculate overdue tasks correctly
    overdue_tasks_count = tasks.filter(
        due_date__lt=today,  # Use today (date) instead of timezone.now() (datetime)
        status__in=['Pending', 'In Progress']  # Only tasks that are not completed
    ).count()
    
    # Use filtered tasks for completed count
    completed_tasks_count = tasks.filter(status='Completed').count()
    
    summary = {
        'completed_tasks': completed_tasks_count,
        'missed_appointments': overdue_tasks_count,  # This represents overdue tasks
        'new_registrations': new_registrations,
    }

    # List of new users for context
    new_users_data = [
        {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'date_joined': user.date_joined.isoformat()
        }
        for user in new_users
    ]

    # Chart data for Tasks Completed vs Overdue using filtered queryset
    tasks_bar_data = {
        'labels': ['Completed', 'Overdue'],
        'data': [completed_tasks_count, overdue_tasks_count]
    }

    # Chart data for Task Completion (monthly) - SQLite compatible
    try:
        task_completion = tasks.filter(status='Completed').annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        # Handle empty task_completion data gracefully
        if task_completion:
            task_completion_data = {
                'labels': [item['month'].strftime('%b %Y') for item in task_completion],
                'data': [item['count'] for item in task_completion],
            }
        else:
            task_completion_data = {
                'labels': [],
                'data': [],
            }
    except Exception as e:
        logger.error(f"Error in task completion calculation: {e}")
        # Fallback: Manual calculation
        task_completion_data = calculate_monthly_completion_manual(tasks.filter(status='Completed'))

    # Chart data for User Activity - Simplified and more reliable approach
    user_activity_data = calculate_user_activity(tasks)

    # Enhanced debug logging
    logger.debug(f"Date filter: {date_filter}, User filter: {user_filter}")
    logger.debug(f"Total tasks in queryset: {tasks.count()}")
    logger.debug(f"Completed tasks: {completed_tasks_count}")
    logger.debug(f"Overdue tasks: {overdue_tasks_count}")
    logger.debug(f"Tasks bar data: {tasks_bar_data}")
    logger.debug(f"Task completion data: {task_completion_data}")
    logger.debug(f"User activity data: {user_activity_data}")
    
    # Log some actual task data for debugging
    if tasks.exists():
        logger.debug(f"Sample tasks:")
        for task in tasks[:5]:  # Log first 5 tasks
            logger.debug(f"  Task: {task.title}, Status: {task.status}, Due: {task.due_date}, Created: {task.created_at}")

    # Context for template rendering
    context = {
        'notifications': Notification.objects.filter(user=request.user, is_read=False),
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
            for user in User.objects.all()
        ],
        'new_users': new_users_data,
        'summary': summary,
        'tasks_bar_data': json.dumps(tasks_bar_data),
        'task_completion_data': json.dumps(task_completion_data),
        'user_activity_data': json.dumps(user_activity_data),
        'current_filters': {
            'date': date_filter,
            'user': user_filter,
        },
    }

    return render(request, 'reports/reports.html', context)


def calculate_monthly_completion_manual(completed_tasks):
    """Manual calculation of monthly completion data - SQLite fallback"""
    monthly_counts = defaultdict(int)
    
    for task in completed_tasks:
        # Group by year-month
        month_key = task.created_at.strftime('%Y-%m')
        monthly_counts[month_key] += 1
    
    # Sort by month and convert to chart format
    sorted_months = sorted(monthly_counts.keys())
    
    labels = []
    data = []
    
    for month_key in sorted_months:
        # Convert 'YYYY-MM' to 'Mon YYYY' format
        from datetime import datetime
        month_date = datetime.strptime(month_key, '%Y-%m')
        labels.append(month_date.strftime('%b %Y'))
        data.append(monthly_counts[month_key])
    
    return {
        'labels': labels,
        'data': data,
    }


def calculate_user_activity(tasks):
    """Calculate user activity data with proper handling of ManyToManyField"""
    user_task_counts = defaultdict(int)
    user_objects = {}
    
    # Process all tasks and count per user
    for task in tasks.select_related('user').prefetch_related('assigned_to'):
        # Count tasks created by user
        if task.user:
            user_id = task.user.id
            user_task_counts[user_id] += 1
            user_objects[user_id] = task.user
        
        # Count tasks assigned to users
        for assigned_user in task.assigned_to.all():
            user_id = assigned_user.id
            # Only count if different from creator to avoid double counting
            if not task.user or task.user.id != user_id:
                user_task_counts[user_id] += 1
                user_objects[user_id] = assigned_user
    
    # Convert to chart format
    labels = []
    data = []
    
    # Sort by username for consistent display
    sorted_users = sorted(user_task_counts.items(), key=lambda x: user_objects[x[0]].username)
    
    for user_id, count in sorted_users:
        user = user_objects[user_id]
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        labels.append(full_name)
        data.append(count)
    
    return {
        'labels': labels,
        'data': data,
    }
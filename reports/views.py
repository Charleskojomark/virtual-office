# reports/views.py
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from tasks.models import Task, Notification
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
import json
from collections import defaultdict
from dashboard.models import Activity
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import get_template
from xhtml2pdf import pisa
import openpyxl
from io import BytesIO
from django.http import HttpResponse



def reports_view(request):
    date_filter = request.GET.get('date-filter', 'all')
    user_filter = request.GET.get('user-filter', 'all')
    today = timezone.now().date()

    # Initialize date ranges
    start_date, end_date = None, None
    if date_filter == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif date_filter == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif date_filter == 'month':
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)  # Safely get next month
        end_date = next_month.replace(day=1)
    elif date_filter == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year+1, month=1, day=1)

    # Base querysets
    tasks = Task.objects.all()
    users = User.objects.all()

    # Apply date filter to tasks
    if date_filter != 'all' and start_date and end_date:
        tasks = tasks.filter(due_date__gte=start_date, due_date__lt=end_date)

    # Apply user filter to tasks
    if user_filter != 'all':
        try:
            user_filter_id = int(user_filter)
            tasks = tasks.filter(
                Q(user__id=user_filter_id) | 
                Q(assigned_to__id=user_filter_id)
            ).distinct()
        except (ValueError, TypeError):
            pass  # Invalid filter - use all tasks

    # Calculate summary stats
    completed_tasks_count = tasks.filter(status='Completed').count()
    overdue_tasks_count = tasks.filter(
        due_date__lt=today,
        status__in=['Pending', 'In Progress']
    ).count()
    
    # Apply date filter to new users
    if date_filter != 'all' and start_date and end_date:
        new_users_queryset = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lt=end_date
        )
    else:
        new_users_queryset = User.objects.all()

    # Summary data
    summary = {
        'completed_tasks': completed_tasks_count,
        'missed_appointments': overdue_tasks_count,
        'new_registrations': new_users_queryset.count(),
    }

    # New users data
    new_users_data = [
        {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'date_joined': user.date_joined
        }
        for user in new_users_queryset.order_by('-date_joined')[:10]  # Limit to 10
    ]

    # Tasks Completed vs Overdue
    tasks_bar_data = {
        'labels': ['Completed', 'Overdue'],
        'data': [completed_tasks_count, overdue_tasks_count]
    }

    # Monthly Task Completion
    task_completion = tasks.filter(status='Completed').annotate(
        month=TruncMonth('due_date')  # Use due_date instead of created_at
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    task_completion_data = {
        'labels': [item['month'].strftime('%b %Y') for item in task_completion],
        'data': [item['count'] for item in task_completion],
    }

    # User Activity
    user_activity = defaultdict(int)
    for task in tasks:
        # Count tasks created by user
        if task.user:
            user_activity[task.user.id] += 1
        # Count tasks assigned to user
        for assigned_user in task.assigned_to.all():
            user_activity[assigned_user.id] += 1
    
    # Get user objects
    user_objects = {user.id: user for user in users}
    
    # Prepare labels and data
    user_labels, user_data = [], []
    for user_id, count in user_activity.items():
        if user_id in user_objects:
            user = user_objects[user_id]
            user_labels.append(f"{user.first_name} {user.last_name}".strip() or user.username)
            user_data.append(count)
    
    user_activity_data = {
        'labels': user_labels,
        'data': user_data,
    }

    context = {
        'notifications': Notification.objects.filter(user=request.user, is_read=False),
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
            for user in users
        ],
        'new_users': new_users_data,
        'summary': summary,
        'tasks_bar_data': tasks_bar_data,
        'task_completion_data': task_completion_data,
        'user_activity_data': user_activity_data,
        'current_filters': {
            'date': date_filter,
            'user': user_filter,
        },
    }
    
    export_format = request.GET.get('export')
    if export_format in ['pdf', 'excel']:
        context['export_mode'] = True  # Add this to context to adjust template if needed
        
        if export_format == 'pdf':
            return generate_pdf(request, context)
        elif export_format == 'excel':
            return generate_excel(request, context)

    return render(request, 'reports/reports.html', context)
# Keep your existing helper functions
def calculate_monthly_completion_manual(completed_tasks):
    monthly_counts = defaultdict(int)
    for task in completed_tasks:
        month_key = task.created_at.strftime('%Y-%m')
        monthly_counts[month_key] += 1
    
    sorted_months = sorted(monthly_counts.keys())
    labels = []
    data = []
    
    for month_key in sorted_months:
        month_date = datetime.strptime(month_key, '%Y-%m')
        labels.append(month_date.strftime('%b %Y'))
        data.append(monthly_counts[month_key])
    
    return {
        'labels': labels,
        'data': data,
    }

def calculate_user_activity(tasks):
    user_task_counts = defaultdict(int)
    user_objects = {}
    
    for task in tasks.select_related('user').prefetch_related('assigned_to'):
        if task.user:
            user_task_counts[task.user.id] += 1
            user_objects[task.user.id] = task.user
        for assigned_user in task.assigned_to.all():
            user_task_counts[assigned_user.id] += 1
            user_objects[assigned_user.id] = assigned_user
    
    sorted_users = sorted(user_task_counts.items(), key=lambda x: user_objects[x[0]].username)
    labels = [f"{user_objects[user_id].first_name} {user_objects[user_id].last_name}".strip() or user_objects[user_id].username for user_id, _ in sorted_users]
    data = [count for _, count in sorted_users]
    
    return {
        'labels': labels,
        'data': data,
    }
    

def generate_pdf(request, context):
    template = get_template('reports/reports_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="task_reports.pdf"'
    
    # Clean CSS - remove problematic styles
    safe_css = """
        body { 
            font-family: Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            font-size: 12px;
            line-height: 1.4;
        }
        h1, h2, h3 { 
            color: #333; 
            margin-top: 0;
            margin-bottom: 10px;
        }
        h1 { font-size: 18px; }
        h2 { font-size: 16px; }
        h3 { font-size: 14px; }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin-bottom: 20px; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
            font-size: 11px;
        }
        th { 
            background-color: #f2f2f2; 
            font-weight: bold;
        }
        .chart-placeholder { 
            background: #f9f9f9; 
            padding: 20px; 
            text-align: center; 
            margin: 10px 0;
            border: 1px solid #ddd;
        }
        .summary-section {
            margin-bottom: 30px;
        }
        .summary-item {
            display: inline-block;
            margin: 5px 15px 5px 0;
            padding: 8px 12px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
        }
        .page-break {
            page-break-before: always;
        }
        /* Remove any animations or transitions */
        * {
            animation: none !important;
            transition: none !important;
        }
    """
    
    # Create PDF with cleaned CSS
    pdf = pisa.CreatePDF(
        html,
        dest=response,
        encoding='UTF-8',
        default_css=safe_css
    )
    
    if pdf.err:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PDF generation error: {pdf.err}")
        return HttpResponse('Error generating PDF', status=500)
    
    return response


# Alternative approach using WeasyPrint (more robust PDF generation)
def generate_pdf_weasyprint(request, context):
    """
    Alternative PDF generation using WeasyPrint
    Install with: pip install weasyprint
    """
    try:
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string
        
        # Render the template
        html_string = render_to_string('reports/reports_pdf.html', context)
        
        # Create CSS for WeasyPrint
        css_string = """
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
            h1, h2, h3 {
                color: #333;
                margin-top: 0;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .chart-placeholder {
                background: #f9f9f9;
                padding: 20px;
                text-align: center;
                margin: 10px 0;
                border: 1px solid #ddd;
            }
        """
        
        # Generate PDF
        html = HTML(string=html_string)
        css = CSS(string=css_string)
        pdf = html.write_pdf(stylesheets=[css])
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="task_reports.pdf"'
        
        return response
        
    except ImportError:
        # Fallback to original method if WeasyPrint not available
        return generate_pdf(request, context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"WeasyPrint PDF generation error: {e}")
        return HttpResponse('Error generating PDF', status=500)


# Enhanced version with better error handling
def generate_pdf_enhanced(request, context):
    """
    Enhanced PDF generation with better error handling
    """
    try:
        template = get_template('reports/reports_pdf.html')
        html = template.render(context)
        
        # Strip out problematic CSS patterns
        import re
        
        # Remove CSS animations and keyframes
        html = re.sub(r'@keyframes[^}]*}[^}]*}', '', html, flags=re.DOTALL)
        html = re.sub(r'@-webkit-keyframes[^}]*}[^}]*}', '', html, flags=re.DOTALL)
        
        # Remove webkit-specific properties
        html = re.sub(r'-webkit-[^:]*:[^;]*;', '', html)
        html = re.sub(r'-moz-[^:]*:[^;]*;', '', html)
        html = re.sub(r'-ms-[^:]*:[^;]*;', '', html)
        
        # Remove animation properties
        html = re.sub(r'animation[^:]*:[^;]*;', '', html)
        html = re.sub(r'transition[^:]*:[^;]*;', '', html)
        html = re.sub(r'transform[^:]*:[^;]*;', '', html)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="task_reports.pdf"'
        
        # Minimal, safe CSS
        safe_css = """
            body { font-family: Arial; margin: 20px; font-size: 12px; }
            h1 { font-size: 18px; color: #333; margin-bottom: 10px; }
            h2 { font-size: 16px; color: #333; margin-bottom: 8px; }
            h3 { font-size: 14px; color: #333; margin-bottom: 6px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
            th { background-color: #f0f0f0; }
            .chart-placeholder { background: #f5f5f5; padding: 15px; text-align: center; margin: 10px 0; }
        """
        
        pdf = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8',
            default_css=safe_css
        )
        
        if pdf.err:
            raise Exception(f"PDF generation failed: {pdf.err}")
            
        return response
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PDF generation error: {str(e)}")
        
        # Return a simple error response
        return HttpResponse(
            f'Error generating PDF: {str(e)}', 
            status=500,
            content_type='text/plain'
        )

def generate_excel(request, context):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="task_reports.xlsx"'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reports Summary"
    
    # Add summary data
    ws.append(["Report Summary"])
    ws.append(["Completed Tasks", context['summary']['completed_tasks']])
    ws.append(["Missed Appointments", context['summary']['missed_appointments']])
    ws.append(["New Registrations", context['summary']['new_registrations']])
    ws.append([])
    
    # Add tasks data
    ws.append(["Tasks Completed vs Overdue"])
    ws.append(["Completed", context['tasks_bar_data']['data'][0]])
    ws.append(["Overdue", context['tasks_bar_data']['data'][1]])
    ws.append([])
    
    # Add monthly completion data
    ws.append(["Monthly Task Completion"])
    for label, data in zip(context['task_completion_data']['labels'], context['task_completion_data']['data']):
        ws.append([label, data])
    ws.append([])
    
    # Add user activity data
    ws.append(["User Activity"])
    for label, data in zip(context['user_activity_data']['labels'], context['user_activity_data']['data']):
        ws.append([label, data])
    
    # Add new users data
    ws.append([])
    ws.append(["New Users"])
    ws.append(["Name", "Username", "Date Joined"])
    for user in context['new_users']:
        ws.append([user['full_name'], user['username'], user['date_joined'].strftime('%Y-%m-%d')])
    
    wb.save(response)
    return response
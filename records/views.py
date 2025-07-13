from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Record
from tasks.models import Notification
from django.utils import timezone
from django.db.models import Q
from dashboard.models import Activity

# Add this to your existing view
@login_required
def records_view(request):
    # Get filter parameters from GET request
    search_query = request.GET.get('search', '')
    record_type_filter = request.GET.get('record-type-filter', 'all')
    status_filter = request.GET.get('status-filter', 'all')

    # Base queryset for records
    records = Record.objects.filter(user=request.user)

    # Apply search filter
    if search_query:
        records = records.filter(name__icontains=search_query)

    # Apply record type filter
    if record_type_filter != 'all':
        records = records.filter(record_type=record_type_filter)

    # Apply status filter
    if status_filter != 'all':
        records = records.filter(status=status_filter)

    context = {
        'records': records,
        'notifications': Notification.objects.filter(user=request.user, is_read=False),
        'record_type_choices': Record.RECORD_TYPE_CHOICES,
        'status_choices': Record.STATUS_CHOICES,
        'current_filters': {
            'search': search_query,
            'record_type': record_type_filter,
            'status': status_filter,
        },
    }
    return render(request, 'records/records.html', context)

@login_required
def add_record(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        record_type = request.POST.get('record_type')
        status = request.POST.get('status', 'Draft')
        file = request.FILES.get('file')

        if name:
            record_data = {
                'name': name,
                'record_type': record_type if record_type in dict(Record.RECORD_TYPE_CHOICES).keys() else 'Other',
                'status': status,
                'user': request.user,
                'date_created': timezone.now(),
            }
            if file:
                record_data['file'] = file
            record = Record.objects.create(**record_data)
            Activity.objects.create(
                user=request.user,
                action_type='RECORD_UPLOADED',
                description=f'Uploaded record: {record.name}'
            )
            return redirect('records:records')
        return render(request, 'records/new_record_modal.html', {
            'record_type_choices': Record.RECORD_TYPE_CHOICES,
            'status_choices': Record.STATUS_CHOICES,
            'error': 'Please provide a name.'
        })

    return render(request, 'records/new_record_modal.html', {
        'record_type_choices': Record.RECORD_TYPE_CHOICES,
        'status_choices': Record.STATUS_CHOICES,
    })

# Update the delete_record view
@login_required
@require_POST
def delete_record(request, pk):
    record = get_object_or_404(Record, pk=pk, user=request.user)
    try:
        record.delete()
        return JsonResponse({'status': 'success', 'message': 'Record deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
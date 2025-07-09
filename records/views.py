from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Record, RecordType
from tasks.models import Notification
from django.utils import timezone
from django.db.models import Q

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
        records = records.filter(record_type__id=record_type_filter)

    # Apply status filter
    if status_filter != 'all':
        records = records.filter(status=status_filter)

    context = {
        'records': records,
        'notifications': Notification.objects.filter(user=request.user, is_read=False),
        'record_types': RecordType.objects.all(),
        'status_choices': Record.STATUS_CHOICES,
        'current_filters': {
            'search': search_query,
            'record_type': record_type_filter,
            'status': status_filter,
        },
    }
    return render(request, 'records/records.html', context)

@login_required
def view_record(request, pk):
    record = get_object_or_404(Record, pk=pk, user=request.user)
    # Placeholder for view logic; adjust based on your needs
    return render(request, 'records/view_record.html', {'record': record})

@login_required
@require_POST
def delete_record(request, pk):
    record = get_object_or_404(Record, pk=pk, user=request.user)
    try:
        record.delete()
        return JsonResponse({'status': 'success', 'message': 'Record deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def add_record(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        record_type_id = request.POST.get('record_type')
        status = request.POST.get('status', 'Draft')

        if name and record_type_id:
            record_type = get_object_or_404(RecordType, pk=record_type_id)
            Record.objects.create(
                name=name,
                record_type=record_type,
                status=status,
                user=request.user,
                date_created=timezone.now()
            )
            return redirect('records:records')
        return render(request, 'partials/new_record_modal.html', {
            'record_types': RecordType.objects.all(),
            'status_choices': Record.STATUS_CHOICES,
            'error': 'Please provide a name and record type.'
        })

    return render(request, 'partials/new_record_modal.html', {
        'record_types': RecordType.objects.all(),
        'status_choices': Record.STATUS_CHOICES,
    })
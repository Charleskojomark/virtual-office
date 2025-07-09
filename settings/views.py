from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Profile
from tasks.models import Notification
from django.core.files.storage import FileSystemStorage

@login_required
def settings_view(request):
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    
    context = {
        'user': request.user,
        'notifications': Notification.objects.filter(user=request.user, is_read=False),
    }
    return render(request, 'settings/settings.html', context)

@login_required
@require_POST
def update_profile(request):
    try:
        user = request.user
        profile = user.profile
        data = request.POST
        
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()
        
        profile.phone = data.get('phone', profile.phone)
        profile.bio = data.get('bio', profile.bio)
        
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            fs = FileSystemStorage()
            filename = fs.save(f'profile_pics/{profile_picture.name}', profile_picture)
            profile.profile_picture = filename
        
        profile.save()
        return JsonResponse({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def change_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        return JsonResponse({'status': 'success', 'message': 'Password changed successfully'})
    else:
        errors = form.errors.as_json()
        return JsonResponse({'status': 'error', 'message': errors}, status=400)

@login_required
@require_POST
def update_preferences(request):
    try:
        profile = request.user.profile
        data = request.POST
        
        profile.dark_mode = data.get('dark_mode', 'false') == 'true'
        profile.email_tasks = data.get('email_tasks', 'false') == 'true'
        profile.email_reports = data.get('email_reports', 'false') == 'true'
        profile.email_security = data.get('email_security', 'false') == 'true'
        profile.push_tasks = data.get('push_tasks', 'false') == 'true'
        profile.push_meetings = data.get('push_meetings', 'false') == 'true'
        profile.save()
        
        return JsonResponse({'status': 'success', 'message': 'Preferences updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
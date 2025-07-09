from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from settings.models import Profile
import uuid
import re

def splash_screen(request):
    if not request.session.get('splash_shown', False):
        request.session['splash_shown'] = True
        return render(request, 'splash.html')
    return redirect('auth:login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember') == 'on'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    if not request.session.get('splash_shown', False):
        return redirect('auth:splash_screen')
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        terms = request.POST.get('terms') == 'on'

        errors = {}
        
        if not first_name or len(first_name) < 2:
            errors['firstName'] = 'First name must be at least 2 characters long'
        if not last_name or len(last_name) < 2:
            errors['lastName'] = 'Last name must be at least 2 characters long'
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors['email'] = 'Please enter a valid email address'
        if not username or len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors['username'] = 'Username must be at least 3 characters long and contain only letters, numbers, and underscores'
        if not password or len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long'
        if password != confirm_password:
            errors['confirmPassword'] = 'Passwords do not match'
        if not terms:
            errors['terms'] = 'Please accept the Terms of Service and Privacy Policy'
        
        if errors:
            for message in errors.values():
                messages.error(request, message)
            return render(request, 'auth/register.html', {'errors': errors})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'auth/register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'auth/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        Profile.objects.create(
            user=user,
            terms_accepted=terms
        )
        
        messages.success(request, 'Account created successfully!')
        
        return redirect('auth:login')

    if not request.session.get('splash_shown', False):
        return redirect('auth:splash_screen')
    
    return render(request, 'auth/register.html')

def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'auth/password_reset.html')
        
        try:
            user = User.objects.get(email=email)
            token = str(uuid.uuid4())
            # Simplified: In production, save token to a PasswordReset model
            reset_link = f"{request.build_absolute_uri('/reset-password-confirm/')}?token={token}"
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return render(request, 'auth/password_reset.html', {
                'email_sent': True,
                'sent_email': email
            })
        
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address')
        
        return render(request, 'auth/password_reset.html')
    
    return render(request, 'auth/password_reset.html')

def logout_view(request):
    logout(request)
    request.session['splash_shown'] = False
    return redirect('auth:splash_screen')
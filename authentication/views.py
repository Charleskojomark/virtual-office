from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from settings.models import Profile
import uuid
import re
from django.contrib.auth.forms import SetPasswordForm
from .models import PasswordResetToken
from django.utils import timezone
from django.urls import reverse


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
        
        messages.success(request, 'Account created successfully!')
        
        return redirect('auth:login')

    if not request.session.get('splash_shown', False):
        return redirect('auth:splash_screen')
    
    return render(request, 'auth/register.html')

def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Validate email format
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'auth/password_reset.html', {
                'email_sent': False,
                'sent_email': None
            })
        
        try:
            user = User.objects.get(email=email)
            
            # Create and store password reset token
            token_obj = PasswordResetToken.create_for_user(user)
            
            # Build reset URL using reverse() for URL safety
            reset_url = request.build_absolute_uri(
                reverse('auth:password_reset_confirm') + 
                f'?token={token_obj.token}&email={email}'
            )
            
            # Send password reset email
            send_mail(
                subject='Password Reset Request - Virtual Office',
                message=(
                    f'You requested a password reset for your Virtual Office account.\n\n'
                    f'Please click the following link to reset your password:\n{reset_url}\n\n'
                    f'This link will expire in 24 hours.\n\n'
                    f'If you didn\'t request this, please ignore this email.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
                html_message=(
                    f'<h3>Password Reset Request</h3>'
                    f'<p>You requested a password reset for your Virtual Office account.</p>'
                    f'<p><a href="{reset_url}">Click here to reset your password</a></p>'
                    f'<p>This link will expire in 24 hours.</p>'
                    f'<p>If you didn\'t request this, please ignore this email.</p>'
                )
            )
            
            
            # Return success response
            messages.success(request, 'Password reset link sent to your email')
            return render(request, 'auth/password_reset.html', {
                'email_sent': True,
                'sent_email': email
            })
            
        except User.DoesNotExist:
            # Security best practice: don't reveal whether email exists
            messages.success(request, 'If an account exists with this email, a password reset link has been sent')
            return render(request, 'auth/password_reset.html', {
                'email_sent': True,  # Show same UI as successful send
                'sent_email': email   # Show the entered email
            })
        except Exception as e:
            # Log any unexpected errors
            messages.error(request, 'An error occurred while processing your request. Please try again.')
            return render(request, 'auth/password_reset.html', {
                'email_sent': False,
                'sent_email': email
            })
    
    # GET request or initial load
    return render(request, 'auth/password_reset.html', {
        'email_sent': False,
        'sent_email': None
    })
    
def password_reset_confirm_view(request):
    token = request.GET.get('token')
    email = request.GET.get('email')
    
    # Verify token and email are present
    if not token or not email:
        messages.error(request, 'Invalid password reset link')
        return redirect('auth:password_reset')
    
    try:
        # Get the user and verify the token
        user = User.objects.get(email=email)
        
        try:
            # Get the token from database
            token_obj = PasswordResetToken.objects.get(
                token=token,
                user=user,
                expires_at__gt=timezone.now()  # Check if token is still valid
            )
            
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    # Save new password
                    form.save()
                    
                    # Delete the used token
                    token_obj.delete()
                    
                    # Add success message
                    messages.success(request, 'Your password has been reset successfully! You can now login with your new password.')
                    
                    # Clear any existing session data
                    request.session.flush()
                    
                    return redirect('auth:login')
            else:
                form = SetPasswordForm(user)
            
            return render(request, 'auth/password_reset_confirm.html', {
                'form': form,
                'validlink': True,
                'email': email,
                'token': token  # Pass token to template for form submission
            })
            
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Invalid or expired password reset link. Please request a new one.')
            return redirect('auth:password_reset')
            
    except User.DoesNotExist:
        # Don't reveal whether user exists (security best practice)
        messages.error(request, 'Invalid password reset link')
        return redirect('auth:password_reset')

def logout_view(request):
    logout(request)
    request.session['splash_shown'] = False
    return redirect('auth:splash_screen')
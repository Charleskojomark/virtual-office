from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
    )
    dark_mode = models.BooleanField(default=False)
    
    # Notification preferences
    email_tasks = models.BooleanField(default=True)
    email_reports = models.BooleanField(default=True)
    email_security = models.BooleanField(default=True)
    push_tasks = models.BooleanField(default=True)
    push_meetings = models.BooleanField(default=True)
    
    # Status tracking
    terms_accepted = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now_add=True)
    
    # Privacy settings
    show_online_status = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def avatar_url(self):
        """Returns the profile picture URL or default"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.png'

    def update_online_status(self):
        """Updates and returns the current online status"""
        was_online = self.is_online
        self.is_online = (
            self.show_online_status and 
            (timezone.now() - self.last_seen).total_seconds() < 300
        )
        if was_online != self.is_online:
            self.save(update_fields=['is_online'])
        return self.is_online

    def get_initials(self):
        """Returns user initials for avatar fallback"""
        name_parts = self.user.get_full_name().split() or [self.user.username]
        return ''.join([part[0].upper() for part in name_parts[:2]])

    @classmethod
    def is_user_online(cls, user):
        """Safe method to check online status for any user"""
        if not user.is_authenticated:
            return False
        try:
            profile = user.profile
            return (
                profile.is_online if profile.show_online_status 
                else None  # Returns None if status is hidden
            )
        except (AttributeError, cls.DoesNotExist):
            return False


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create profile when new user registers"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure profile is saved when user is saved"""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
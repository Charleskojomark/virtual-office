from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    email_tasks = models.BooleanField(default=True)
    email_reports = models.BooleanField(default=True)
    email_security = models.BooleanField(default=True)
    push_tasks = models.BooleanField(default=True)
    push_meetings = models.BooleanField(default=True)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

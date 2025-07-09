from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)
    meeting_type = models.CharField(max_length=50, choices=[
        ('in-person', 'In-Person'),
        ('video-call', 'Video Call'),
        ('phone-call', 'Phone Call'),
        ('other', 'Other')
    ])
    meeting_platform = models.CharField(max_length=50, blank=True, choices=[
        ('', 'None'),
        ('zoom', 'Zoom'),
        ('microsoft-teams', 'Microsoft Teams'),
        ('google-meet', 'Google Meet'),
        ('webex', 'Webex'),
        ('other', 'Other')
    ])
    meeting_link = models.URLField(blank=True)
    participants = models.ManyToManyField(User, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_all_day = models.BooleanField(default=False)

    def __str__(self):
        return self.title
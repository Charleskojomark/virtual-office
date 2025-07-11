from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ManyToManyField(User, blank=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'Completed'

    @property
    def is_due_soon(self):
        delta = self.due_date - timezone.now().date()
        return 0 <= delta.days <= 2 and self.status != 'Completed'

# tasks/models.py (update your existing Notification model)
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('chat', 'Chat Message'),
        ('task', 'Task Update'),
        ('event', 'Event Reminder'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.CharField(max_length=255, blank=True, null=True)
    related_id = models.IntegerField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"
from django.db import models
from django.contrib.auth.models import User

class Activity(models.Model):
    ACTION_TYPES = (
        ('TASK_CREATED', 'Task Created'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('MEETING_SCHEDULED', 'Meeting Scheduled'),
        ('MESSAGE_SENT', 'Message Sent'),
        ('RECORD_UPLOADED', 'Record Uploaded'),
        ('REPORT_FILTERED', 'Report Filtered'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

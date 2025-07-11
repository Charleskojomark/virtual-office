from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import mimetypes

class Record(models.Model):
    RECORD_TYPE_CHOICES = [
        ('Image', 'Image'),
        ('Document', 'Document'),
        ('Video', 'Video'),
        ('Audio', 'Audio'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Archived', 'Archived'),
        ('Draft', 'Draft'),
    ]
    name = models.CharField(max_length=200)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default='Other')
    file = models.FileField(upload_to='records/', blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-detect record type based on file MIME type if a file is provided
        if self.file and not self.record_type:
            mime_type, _ = mimetypes.guess_type(self.file.name)
            if mime_type:
                if mime_type.startswith('image/'):
                    self.record_type = 'Image'
                elif mime_type.startswith('video/'):
                    self.record_type = 'Video'
                elif mime_type.startswith('audio/'):
                    self.record_type = 'Audio'
                elif mime_type in ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    self.record_type = 'Document'
                else:
                    self.record_type = 'Other'
        super().save(*args, **kwargs)
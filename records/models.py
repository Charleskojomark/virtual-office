from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class RecordType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Record(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Archived', 'Archived'),
        ('Draft', 'Draft'),
    ]
    name = models.CharField(max_length=200)
    record_type = models.ForeignKey(RecordType, on_delete=models.SET_NULL, null=True, related_name='records')
    date_created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')

    def __str__(self):
        return self.name

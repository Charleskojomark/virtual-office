from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    @classmethod
    def create_for_user(cls, user):
        # Delete any existing tokens for this user
        cls.objects.filter(user=user).delete()
        
        # Create new token with 24 hour expiration
        return cls.objects.create(
            user=user,
            token=str(uuid.uuid4()),
            expires_at=timezone.now() + timedelta(hours=24)
        )
    
    def is_valid(self):
        return timezone.now() < self.expires_at
    
    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Event
from tasks.models import Notification
from django.contrib.auth.models import User

@receiver(post_save, sender=Event)
def create_event_notifications(sender, instance, created, **kwargs):
    if created:
        # Notify all participants (excluding the creator)
        for participant in instance.participants.all():
            if participant != instance.created_by:
                Notification.objects.create(
                    user=participant,
                    message=f"You have been invited to a meeting: '{instance.title}' on {instance.start_time.strftime('%B %d, %Y at %I:%M %p')}"
                )

@receiver(m2m_changed, sender=Event.participants.through)
def update_event_participants_notifications(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        # Notify newly added participants
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            if user != instance.created_by:
                Notification.objects.create(
                    user=user,
                    message=f"You have been added to a meeting: '{instance.title}' on {instance.start_time.strftime('%B %d, %Y at %I:%M %p')}"
                )
    elif action == "post_remove":
        # Optionally notify removed participants
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            Notification.objects.create(
                user=user,
                message=f"You have been removed from a meeting: '{instance.title}' on {instance.start_time.strftime('%B %d, %Y at %I:%M %p')}"
            )
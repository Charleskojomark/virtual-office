# Generated by Django 4.2.23 on 2025-07-07 21:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('description', models.TextField(blank=True)),
                ('meeting_type', models.CharField(choices=[('in-person', 'In-Person'), ('video-call', 'Video Call'), ('phone-call', 'Phone Call'), ('other', 'Other')], max_length=50)),
                ('meeting_platform', models.CharField(blank=True, choices=[('', 'None'), ('zoom', 'Zoom'), ('microsoft-teams', 'Microsoft Teams'), ('google-meet', 'Google Meet'), ('webex', 'Webex'), ('other', 'Other')], max_length=50)),
                ('meeting_link', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_all_day', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(related_name='events', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

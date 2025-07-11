# Generated by Django 4.2.23 on 2025-07-07 17:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Archived', 'Archived'), ('Draft', 'Draft')], default='Draft', max_length=20)),
                ('record_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='records', to='records.recordtype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

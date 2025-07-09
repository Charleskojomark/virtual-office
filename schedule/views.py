from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Event
from tasks.models import Notification
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

class ScheduleView(LoginRequiredMixin, APIView):
    login_url = '/accounts/login/'
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        context = {
            'notifications': {
                'count': notifications.count()
            }
        }
        return render(request, 'schedule/schedule.html', context)

class ParticipantListView(APIView):
    def get(self, request):
        users = User.objects.filter(is_active=True)
        data = [{
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        } for user in users]
        return Response({'participants': data}, status=status.HTTP_200_OK)

class EventListView(APIView):
    def get(self, request):
        # Fetch events where user is creator or participant
        events = Event.objects.filter(
            models.Q(created_by=request.user) | models.Q(participants=request.user)
        ).distinct()
        data = [{
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'extendedProps': {
                'description': event.description,
                'meeting_type': event.meeting_type,
                'meeting_platform': event.meeting_platform,
                'meeting_link': event.meeting_link,
                'participants': [p.email for p in event.participants.all()],
                'created_by': event.created_by.email  # Include creator email for frontend permission checks
            }
        } for event in events]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        try:
            event = Event.objects.create(
                title=data['title'],
                start_time=timezone.datetime.fromisoformat(data['start_time']),
                end_time=timezone.datetime.fromisoformat(data['end_time']),
                description=data.get('description', ''),
                meeting_type=data['meeting_type'],
                meeting_platform=data.get('meeting_platform', ''),
                meeting_link=data.get('meeting_link', ''),
                created_by=request.user
            )
            participant_emails = data.get('participants', [])
            participants = User.objects.filter(email__in=participant_emails, is_active=True)
            if participant_emails and not participants:
                return Response({
                    'status': 'warning',
                    'message': 'No matching active users found for the provided emails'
                }, status=status.HTTP_400_BAD_REQUEST)
            event.participants.set(participants)
            return Response({'status': 'success', 'id': event.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EventDetailView(APIView):
    def get(self, request, pk):
        # Allow access if user is creator or participant
        event = get_object_or_404(Event, pk=pk, created_by__in=[request.user] + list(Event.objects.filter(participants=request.user)))
        data = {
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'extendedProps': {
                'description': event.description,
                'meeting_type': event.meeting_type,
                'meeting_platform': event.meeting_platform,
                'meeting_link': event.meeting_link,
                'participants': [p.email for p in event.participants.all()],
                'created_by': event.created_by.email
            }
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        # Restrict edit to creator only
        event = get_object_or_404(Event, pk=pk, created_by=request.user)
        data = request.data
        try:
            event.title = data['title']
            event.start_time = timezone.datetime.fromisoformat(data['start_time'])
            event.end_time = timezone.datetime.fromisoformat(data['end_time'])
            event.description = data.get('description', '')
            event.meeting_type = data['meeting_type']
            event.meeting_platform = data.get('meeting_platform', '')
            event.meeting_link = data.get('meeting_link', '')
            event.save()
            participant_emails = data.get('participants', [])
            participants = User.objects.filter(email__in=participant_emails, is_active=True)
            if participant_emails and not participants:
                return Response({
                    'status': 'warning',
                    'message': 'No matching active users found for the provided emails'
                }, status=status.HTTP_400_BAD_REQUEST)
            event.participants.set(participants)
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Restrict delete to creator only
        event = get_object_or_404(Event, pk=pk, created_by=request.user)
        event.delete()
        return Response({'status': 'success'}, status=status.HTTP_204_NO_CONTENT)
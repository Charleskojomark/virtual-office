from django.urls import path
from . import views
app_name = 'schedule'
urlpatterns = [
    path('', views.ScheduleView.as_view(), name='schedule'),
    path('api/participants/', views.ParticipantListView.as_view(), name='participant-list'),
    path('api/events/', views.EventListView.as_view(), name='event-list'),
    path('api/events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
]
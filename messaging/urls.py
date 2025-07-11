from django.urls import path, re_path
from . import views, consumers

app_name = 'messaging'

urlpatterns = [
    # HTML Views
    path('', views.messaging, name='messaging'),
    
    # API Endpoints
    path('api/messages/<int:conversation_id>/', views.messages_api, name='messages_api'),
    path('api/messages/<int:conversation_id>/read/', views.mark_messages_read, name='mark_messages_read'),
    path('send/', views.send_message, name='send_message'),
    
    # Notification Endpoints
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/count/', views.get_notifications_count, name='get_notifications_count'),
]


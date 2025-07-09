from django.urls import path
from . import views

app_name = 'messaging'
urlpatterns = [
    path('', views.messaging, name='messaging'),
    path('api/messages/<int:conversation_id>/', views.messages_api, name='messages_api'),
]
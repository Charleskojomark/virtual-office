from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('task_updates/', views.task_updates, name='task_updates'),
    path('activities/', views.activities, name='activities'),
]

from django.urls import path
from . import views
from .views import MarkAllReadView
app_name = 'tasks'

urlpatterns = [
    path('', views.tasks, name='tasks'),
    path('create/', views.task_create, name='task_create'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('bulk_delete/', views.bulk_delete_tasks, name='bulk_delete_tasks'),
    path('bulk_complete/', views.bulk_complete_tasks, name='bulk_complete_tasks'),
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
]
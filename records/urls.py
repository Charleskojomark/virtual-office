from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    path('', views.records_view, name='records'),
    path('add/', views.add_record, name='add_record'),
    path('<int:pk>/delete/', views.delete_record, name='delete_record'),
]
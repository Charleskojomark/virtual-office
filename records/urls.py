from django.urls import path
from . import views

app_name = 'records'
urlpatterns = [
    path('', views.records_view, name='records'),
    path('records/view/<int:pk>/', views.view_record, name='view_record'),
    path('records/delete/<int:pk>/', views.delete_record, name='delete_record'),
    path('records/add/', views.add_record, name='add_record'),
]
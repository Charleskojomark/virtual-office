from django.urls import path
from . import views

app_name = 'settings'
urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('settings/update-profile/', views.update_profile, name='update_profile'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/update-preferences/', views.update_preferences, name='update_preferences'),
]
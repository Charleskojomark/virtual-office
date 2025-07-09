from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('', views.splash_screen, name='splash_screen'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('logout/', views.logout_view, name='logout'),
]
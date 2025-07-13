from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='accounts/login/')),
    path('accounts/', include('authentication.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('schedule/', include('schedule.urls')),
    path('tasks/', include('tasks.urls')),
    path('messaging/', include('messaging.urls')),
    path('reports/', include('reports.urls')),
    path('records/', include('records.urls')),
    path('settings/', include('settings.urls')),
    
    path('serviceworker.js', serve, {
        'document_root': settings.STATIC_ROOT,
        'path': 'serviceworker.js'
    }),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

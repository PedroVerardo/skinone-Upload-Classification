from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', include('users.admin_urls')),
    path('auth/', include('users.urls')),
    path('images/', include('images.urls')),
    path('classifications/', include('classification.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

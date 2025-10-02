from django.urls import path
from . import admin_views

urlpatterns = [
    path('metrics/', admin_views.get_metrics, name='admin_metrics'),
    path('users/', admin_views.list_admin_users, name='admin_users'),
]
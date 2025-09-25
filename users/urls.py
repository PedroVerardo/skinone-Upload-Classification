from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('verify-email-password/', views.verify_email_password, name='verify_email_password'),
]
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('verify-email-password/', views.verify_email_password, name='verify_email_password'),
    # path('verify-google-sso/', views.verify_google_sso, name='verify_google_sso'),  # TODO: Implement this view
]
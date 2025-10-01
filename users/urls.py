from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.auth_page, name='auth_page'),  # HTML auth page
    path('verify-email-password/', views.verify_email_password, name='verify_email_password'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('verify-token/', views.verify_token, name='verify_token'),
]
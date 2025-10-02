from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('csrf/', views.csrf_token, name='csrf_token'),
    path('me/', views.me, name='me'),
    path('test/', views.auth_page, name='auth_page'),
]
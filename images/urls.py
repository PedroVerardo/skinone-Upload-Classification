from django.urls import path
from . import views

app_name = 'images'

urlpatterns = [
    path('', views.upload_page, name='upload_page'),  # HTML upload page
    path('upload/', views.upload_image, name='upload_image'),  # API endpoint
    path('<int:image_id>/', views.get_image_info, name='image_info'),
    path('list/', views.list_images, name='list_images'),
]

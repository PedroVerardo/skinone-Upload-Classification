from django.urls import path
from . import views

app_name = 'images'

urlpatterns = [
    path('', views.upload_page, name='upload_page'),
    path('upload/', views.upload_image, name='upload_image'),
    path('upload/batch/', views.upload_batch_images, name='upload_batch_images'),
    path('upload/base64/', views.upload_base64_image, name='upload_base64_image'),  
    path('upload/batch-base64/', views.upload_batch_base64_images, name='upload_batch_base64_images'),
    path('upload/with-classification/', views.upload_image_with_classification, name='upload_with_classification'),
    path('<int:image_id>/', views.get_image_info, name='image_info'),
    path('list/', views.list_images, name='list_images'),
]

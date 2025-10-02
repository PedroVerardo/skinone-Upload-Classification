from django.urls import path
from . import views

app_name = 'images'

urlpatterns = [
    path('', views.list_images, name='list_images'),  # GET /images/
    path('upload/', views.upload_batch_images, name='upload_batch'),  # POST /images/upload/
    path('upload/single/', views.upload_single_image, name='upload_single'),  # POST /images/upload/single/
    path('upload/with-stage/', views.upload_with_stage, name='upload_with_stage'),  # POST /images/upload/with-stage/?stage=<stage>
    path('test/', views.upload_page, name='upload_page'),
]

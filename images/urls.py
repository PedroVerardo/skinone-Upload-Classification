from django.urls import path
from . import views

app_name = 'images'

urlpatterns = [
    path('', views.list_images, name='list_images'),
    path('upload/', views.upload_batch_images, name='upload_batch'),
    path('upload/single/', views.upload_single_image, name='upload_single'),
    path('upload/with-stage/', views.upload_with_stage, name='upload_with_stage'),  # POST /images/upload/with-stage/?stage=<stage>
    
    # Base64 upload routes
    path('upload/base64/', views.upload_base64_image, name='upload_base64'),
    path('upload/base64/batch/', views.upload_batch_base64_images, name='upload_batch_base64'),
    path('upload/base64/with-classification/', views.upload_image_with_classification, name='upload_base64_with_classification'),
 
    path('<int:image_id>/', views.get_image_info, name='get_image_info'),
    path('test/', views.upload_page, name='upload_page'),
]

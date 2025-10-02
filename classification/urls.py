from django.urls import path
from . import views

app_name = 'classification'

urlpatterns = [
    path('', views.create_classification, name='create_classification'),  # POST /classifications/
    path('', views.list_classifications, name='list_classifications'),   # GET /classifications/?image_id=<id>
]

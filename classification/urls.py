from django.urls import path
from . import views

app_name = 'classification'

urlpatterns = [
    path('', views.create_classification, name='create_classification'),  # POST /classifications/ and GET list
]

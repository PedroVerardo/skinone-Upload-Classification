from django.urls import path
from . import views

app_name = 'classification'

urlpatterns = [
    path('create/', views.create_classification, name='create_classification'),
    path('<int:classification_id>/', views.get_classification, name='get_classification'),
    path('<int:classification_id>/update/', views.update_classification, name='update_classification'),
    path('<int:classification_id>/delete/', views.delete_classification, name='delete_classification'),
    path('list/', views.list_classifications, name='list_classifications'),
    path('choices/', views.get_classification_choices, name='classification_choices'),
]

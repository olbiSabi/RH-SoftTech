from django.urls import path
from . import views
from .views import *

#path('departement', views.departement, name='departement'),

# Pas de app_name si vous n'utilisez pas de namespace dans urls.py principal

urlpatterns = [
    path('departement', views.department_list, name='list'),
    path('edit/<int:pk>/', views.department_edit, name='edit'),
    path('delete/<int:pk>/', views.department_delete, name='delete'),
    path('poste/', poste, name='poste'),
]

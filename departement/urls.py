from django.urls import path
from . import views

urlpatterns = [
    path('departement', views.department_list, name='list'),
    path('edit/<int:pk>/', views.department_edit, name='edit'),
    path('delete/<int:pk>/', views.department_delete, name='delete'),

# Routes Poste
    path('poste/', views.poste_list, name='poste_list'),
    path('poste/edit/<int:pk>/', views.poste_edit, name='poste_edit'),
    path('poste/delete/<int:pk>/', views.poste_delete, name='poste_delete'),
]

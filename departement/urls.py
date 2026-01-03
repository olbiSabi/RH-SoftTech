from django.urls import path
from . import views

app_name = 'departement'

urlpatterns = [
    path('departement', views.department_list, name='list'),
    path('edit/<int:pk>/', views.department_edit, name='edit'),
    path('delete/<int:pk>/', views.department_delete, name='delete'),

# Routes Poste
    path('poste/', views.poste_list, name='poste_list'),
    path('poste/edit/<int:pk>/', views.poste_edit, name='poste_edit'),
    path('poste/delete/<int:pk>/', views.poste_delete, name='poste_delete'),

# URLs pour les managers
    path('managers/', views.liste_managers, name='liste_managers'),
    path('api/manager/create/', views.api_manager_create_modal, name='api_manager_create'),
    path('api/manager/<int:id>/', views.api_manager_detail, name='api_manager_detail'),
    path('api/manager/<int:id>/update/', views.api_manager_update_modal, name='api_manager_update'),
    path('api/manager/<int:id>/delete/', views.api_manager_delete_modal, name='api_manager_delete'),
    path('api/managers/departement/<int:departement_id>/', views.api_managers_by_departement, name='api_managers_by_departement'),
]

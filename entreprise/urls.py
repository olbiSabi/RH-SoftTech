# entreprise/urls.py

from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'entreprise'

urlpatterns = [
    # Profil entreprise (unique)
    path('profil/', views.profil_entreprise, name='profil_entreprise'),
    # API
    path('api/entreprise/<uuid:uuid>/', views.api_entreprise_detail, name='api_entreprise_detail'),
    path('api/entreprise/create/', views.api_entreprise_create, name='api_entreprise_create'),
    path('api/entreprise/<uuid:uuid>/update/', views.api_entreprise_update, name='api_entreprise_update'),
    path('api/entreprise/<uuid:uuid>/delete/', views.api_entreprise_delete, name='api_entreprise_delete'),
]
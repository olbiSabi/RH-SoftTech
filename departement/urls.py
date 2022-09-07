from django.urls import path

from .views import *

urlpatterns = [
    path('departement/', departement, name='departement'),
    path('poste/', poste, name='poste'),
]
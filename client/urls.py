from django.urls import path

from .views import *

urlpatterns = [
    path('client/', client, name='client'),
    path('client-profil/', profilClient, name='client-profil'),
    # path('detail-projet/', detailProjet, name='detail-projet'),
]
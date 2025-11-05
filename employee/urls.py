from django.urls import path

from .views import *

urlpatterns = [
    path('embauche-agent/', embaucheAgent, name='embauche-agent'),
    path('liste-employee/', listeEmployee, name='liste-employee'),
    path('employee/', employee, name='employee'),
    path('valider-embauche/', validerEmbauche, name='valider-embauche'),
    path('dossierSortie/', dossierSortie, name='dossier-sortie'),
    path('profil-employee/', profilEmployee, name='profile-employee'),
    path('conges/', conges, name='conges'),
    path('validerConges/', validerConges, name='valider-conges'),
    path('feuille-de-temps/', feuilleDeTemps, name='feuilleDeTemps'),
    path('planification/', planification, name='planification'),
    path('presence/', presence, name='presence'),
    # path('gestion_absence/', gestion_absence, name='gestion-absence'),
]
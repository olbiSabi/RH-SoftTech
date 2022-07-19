from django.urls import path

from .views import *

urlpatterns = [
    path('liste-employee/', listeEmployee, name='liste-employee'),
    path('employee/', employee, name='employee'),
    path('valider-embauche/', validerEmbauche, name='valider-embauche'),
    path('dossierSortie/', dossierSortie, name='dossier-sortie'),
    path('profile-employee/', profileEmployee, name='profile-employee'),
    # path('supprimer_dossier/', supprimer_dossier, name='supprimer-dossier'),
    # path('editer_dossier/', editer_dossier, name='editer-dossier'),
    # path('gestion_absence/', gestion_absence, name='gestion-absence'),
]
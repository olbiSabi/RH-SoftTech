from django.urls import path
from .views import *
from . import views

urlpatterns = [

    path('embauche-agent/', views.embauche_agent, name='embauche_agent'),
    path('employe/<str:matricule>/valider/', views.valider_embauche, name='valider_embauche'),
    # ===============================
    # URLs pour les employés (ZY00)
    # ===============================
    path('liste-employee/', views.EmployeListView.as_view(), name='liste_employes'),
    path('employe/<str:matricule>/', views.detail_employe, name='detail_employe'),
    path('employe/<str:matricule>/modifier/', views.EmployeUpdateView.as_view(), name='modifier_employe'),
    path('employe/<str:matricule>/supprimer/', views.EmployeDeleteView.as_view(), name='supprimer_employe'),
    # path('dossier_individuel/', views.dossierIndividuel, name='dossier_individuel'),
    path('dossier-individuel/', views.dossierIndividuel.as_view(), name='dossier_individuel'),
    # path('employe/nouveau/', views.EmployeCreateView.as_view(), name='creer_employe'),

    # ===============================
    # URLs pour les contrats (ZYCO)
    # ===============================
    path('contrats/', views.ContratListView.as_view(), name='liste_contrats'),
    path('contrat/nouveau/', views.ContratCreateView.as_view(), name='creer_contrat'),
    path('contrat/<int:pk>/modifier/', views.ContratUpdateView.as_view(), name='modifier_contrat'),
    path('contrat/<int:pk>/supprimer/', views.ContratDeleteView.as_view(), name='supprimer_contrat'),

    # ===============================
    # URLs pour les téléphones (ZYTE)
    # ===============================
    path('telephones/', views.TelephoneListView.as_view(), name='liste_telephones'),
    path('telephone/nouveau/', views.TelephoneCreateView.as_view(), name='creer_telephone'),
    path('telephone/<int:pk>/modifier/', views.TelephoneUpdateView.as_view(), name='modifier_telephone'),
    path('telephone/<int:pk>/supprimer/', views.TelephoneDeleteView.as_view(), name='supprimer_telephone'),

    # ===============================
    # URLs pour les emails (ZYME)
    # ===============================
    path('emails/', views.EmailListView.as_view(), name='liste_emails'),
    path('email/nouveau/', views.EmailCreateView.as_view(), name='creer_email'),
    path('email/<int:pk>/modifier/', views.EmailUpdateView.as_view(), name='modifier_email'),
    path('email/<int:pk>/supprimer/', views.EmailDeleteView.as_view(), name='supprimer_email'),

    # ===============================
    # URLs pour les affectations (ZYAF)
    # ===============================
    path('affectations/', views.AffectationListView.as_view(), name='liste_affectations'),
    path('affectation/nouvelle/', views.AffectationCreateView.as_view(), name='creer_affectation'),
    path('affectation/<int:pk>/modifier/', views.AffectationUpdateView.as_view(), name='modifier_affectation'),
    path('affectation/<int:pk>/supprimer/', views.AffectationDeleteView.as_view(), name='supprimer_affectation'),

    # ===============================
    # URLs pour les adresses (ZYAD)
    # ===============================
    path('adresses/', views.AdresseListView.as_view(), name='liste_adresses'),
    path('adresse/nouvelle/', views.AdresseCreateView.as_view(), name='creer_adresse'),
    path('adresse/<int:pk>/modifier/', views.AdresseUpdateView.as_view(), name='modifier_adresse'),
    path('adresse/<int:pk>/supprimer/', views.AdresseDeleteView.as_view(), name='supprimer_adresse'),

    # path('liste-employee/', listeEmployee, name='liste_employes'),
    path('dossierSortie/', dossierSortie, name='dossier-sortie'),
    path('profil-employee/', profilEmployee, name='profile-employee'),
    path('conges/', conges, name='conges'),
    path('validerConges/', validerConges, name='valider-conges'),
    path('feuille-de-temps/', feuilleDeTemps, name='feuilleDeTemps'),
    path('planification/', planification, name='planification'),
    path('presence/', presence, name='presence'),
    # path('gestion_absence/', gestion_absence, name='gestion-absence'),
]
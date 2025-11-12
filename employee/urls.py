from django.urls import path
from .views import *
from . import views

urlpatterns = [

    path('embauche-agent/', views.embauche_agent, name='embauche_agent'),
    path('employe/<uuid:uuid>/valider/', views.valider_embauche, name='valider_embauche'),
    # ===============================
    # URLs pour les employés (ZY00)
    # ===============================
    path('liste-employee/', views.EmployeListView.as_view(), name='liste_employes'),
    path('matricule/<uuid:uuid>/', views.detail_employe, name='detail_employe'),
    path('dossier-individuel/', views.DossierIndividuelView.as_view(), name='liste_dossiers'),
    path('dossier-individuel/<uuid:uuid>/', views.DossierIndividuelView.as_view(), name='dossier_detail'),
    path('employe/<uuid:uuid>/modifier/', views.EmployeUpdateView.as_view(), name='modifier_employe'),
    path('employe/<uuid:uuid>/supprimer/', views.EmployeDeleteView.as_view(), name='supprimer_employe'),
    # path('employe/nouveau/', views.EmployeCreateView.as_view(), name='creer_employe'),
    # 🆕 URLs pour la gestion de la photo de profil
    path('photo/modifier-ajax/', views.modifier_photo_ajax, name='modifier_photo_ajax'),
    path('photo/<uuid:uuid>/supprimer-ajax/', views.supprimer_photo_ajax, name='supprimer_photo_ajax'),

    # ===============================
    # URLs pour les contrats (ZYCO)
    # ===============================
    path('contrat/nouveau-ajax/', views.contrat_create_ajax, name='contrat_create_ajax'),
    path('contrat/<int:pk>/modifier-ajax/', views.contrat_update_ajax, name='contrat_update_ajax'),
    path('contrat/<int:pk>/supprimer-ajax/', views.contrat_delete_ajax, name='contrat_delete_ajax'),

    # ===============================
    # AFFECTATIONS (ZYAF)
    # ===============================
    path('affectation/nouveau-ajax/', views.affectation_create_ajax, name='affectation_create_ajax'),
    path('affectation/<int:pk>/modifier-ajax/', views.affectation_update_ajax, name='affectation_update_ajax'),
    path('affectation/<int:pk>/supprimer-ajax/', views.affectation_delete_ajax, name='affectation_delete_ajax'),

    # ===============================
    # TÉLÉPHONES (ZYTE)
    # ===============================
    path('telephone/nouveau-ajax/', views.telephone_create_ajax, name='telephone_create_ajax'),
    path('telephone/<int:pk>/modifier-ajax/', views.telephone_update_ajax, name='telephone_update_ajax'),
    path('telephone/<int:pk>/supprimer-ajax/', views.telephone_delete_ajax, name='telephone_delete_ajax'),

    # ===============================
    # EMAILS (ZYME)
    # ===============================
    path('email/nouveau-ajax/', views.email_create_ajax, name='email_create_ajax'),
    path('email/<int:pk>/modifier-ajax/', views.email_update_ajax, name='email_update_ajax'),
    path('email/<int:pk>/supprimer-ajax/', views.email_delete_ajax, name='email_delete_ajax'),

    # ===============================
    # ADRESSES (ZYAD)
    # ===============================
    path('adresse/nouveau-ajax/', views.adresse_create_ajax, name='adresse_create_ajax'),
    path('adresse/<int:pk>/modifier-ajax/', views.adresse_update_ajax, name='adresse_update_ajax'),
    path('adresse/<int:pk>/supprimer-ajax/', views.adresse_delete_ajax, name='adresse_delete_ajax'),

    # ===============================
    # Gestion des documents ZYDO
    # ===============================
    path('documents/<str:matricule>/', views.gerer_documents_employe, name='gerer_documents_employe'),
    path('documents/telecharger/<int:pk>/', views.telecharger_document, name='telecharger_document'),
    path('ajax/document/create/', views.document_create_ajax, name='document_create_ajax'),
    path('ajax/document/delete/<int:pk>/', views.document_delete_ajax, name='document_delete_ajax'),




    path('dossierSortie/', dossierSortie, name='dossier-sortie'),
    path('profil-employee/', profilEmployee, name='profile-employee'),
    path('conges/', conges, name='conges'),
    path('validerConges/', validerConges, name='valider-conges'),
    path('feuille-de-temps/', feuilleDeTemps, name='feuilleDeTemps'),
    path('planification/', planification, name='planification'),
    path('presence/', presence, name='presence'),
    # path('gestion_absence/', gestion_absence, name='gestion-absence'),
]
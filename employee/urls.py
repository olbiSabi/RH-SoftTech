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
    path('employe/<uuid:uuid>/modifier/', views.EmployeUpdateView.as_view(), name='modifier_employe'),
    path('employe/<uuid:uuid>/supprimer/', views.EmployeDeleteView.as_view(), name='supprimer_employe'),
    # path('employe/nouveau/', views.EmployeCreateView.as_view(), name='creer_employe'),
    # Route pour la liste des employés sans sélection
    path('dossier/', DossierIndividuelView.as_view(), name='dossier_individuel'),
    # Route pour afficher le détail d'un employé spécifique
    path('dossier/<uuid:uuid>/', DossierIndividuelView.as_view(), name='dossier_individuel_detail'),


    # ===== NOUVELLES API POUR LES MODALES =====

    # API Adresses (pour modales)
    path('api/adresse/<int:id>/', views.api_adresse_detail, name='api_adresse_detail_modal'),
    path('api/adresse/create/', views.api_adresse_create_modal, name='api_adresse_create_modal'),
    path('api/adresse/<int:id>/update/', views.api_adresse_update_modal, name='api_adresse_update_modal'),
    path('api/adresse/<int:id>/delete/', views.api_adresse_delete_modal, name='api_adresse_delete_modal'),

    # API Téléphones (pour modales)
    path('api/telephone/<int:id>/', views.api_telephone_detail, name='api_telephone_detail_modal'),
    path('api/telephone/create/', views.api_telephone_create_modal, name='api_telephone_create_modal'),
    path('api/telephone/<int:id>/update/', views.api_telephone_update_modal, name='api_telephone_update_modal'),
    path('api/telephone/<int:id>/delete/', views.api_telephone_delete_modal, name='api_telephone_delete_modal'),

    # API Emails (pour modales)
    path('api/email/<int:id>/', views.api_email_detail, name='api_email_detail_modal'),
    path('api/email/create/', views.api_email_create_modal, name='api_email_create_modal'),
    path('api/email/<int:id>/update/', views.api_email_update_modal, name='api_email_update_modal'),
    path('api/email/<int:id>/delete/', views.api_email_delete_modal, name='api_email_delete_modal'),

    # API Documents (pour modales)
    path('api/document/create/', views.api_document_create_modal, name='api_document_create_modal'),
    path('api/document/<int:id>/delete/', views.api_document_delete_modal, name='api_document_delete_modal'),

    # API Contrats (pour modales)
    path('api/contrat/<int:id>/', views.api_contrat_detail, name='api_contrat_detail_modal'),
    path('api/contrat/create/', views.api_contrat_create_modal, name='api_contrat_create_modal'),
    path('api/contrat/<int:id>/update/', views.api_contrat_update_modal, name='api_contrat_update_modal'),
    path('api/contrat/<int:id>/delete/', views.api_contrat_delete_modal, name='api_contrat_delete_modal'),

    # API Affectations (pour modales)
    path('api/affectation/<int:id>/', views.api_affectation_detail, name='api_affectation_detail_modal'),
    path('api/affectation/create/', views.api_affectation_create_modal, name='api_affectation_create_modal'),
    path('api/affectation/<int:id>/update/', views.api_affectation_update_modal,
         name='api_affectation_update_modal'),
    path('api/affectation/<int:id>/delete/', views.api_affectation_delete_modal,
         name='api_affectation_delete_modal'),

    # API Helper
    path('api/postes/', views.api_postes_by_departement, name='api_postes_by_departement'),


    # Photo
    path('ajax/photo/modifier/', views.modifier_photo_ajax, name='modifier_photo_ajax'),
    path('ajax/photo/<uuid:uuid>/supprimer/', views.supprimer_photo_ajax, name='supprimer_photo_ajax'),

    # API Famille (ZYFA)
    path('api/famille/create/', views.api_famille_create_modal, name='api_famille_create'),
    path('api/famille/<int:id>/update/', views.api_famille_update_modal, name='api_famille_update'),
    path('api/famille/<int:id>/delete/', views.api_famille_delete_modal, name='api_famille_delete'),
    path('api/famille/<int:id>/', views.api_famille_detail, name='api_famille_detail'),


    path('profil-employee/', profilEmployee, name='profile-employee'),
    path('validerConges/', validerConges, name='valider-conges'),
]
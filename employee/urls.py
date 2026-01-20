from django.urls import path
from .views import *
from . import views
from .auth_views import login_view, logout_view, dashboard_view, change_password_view, password_reset_request, \
    CustomPasswordResetConfirmView,  test_reset_account

app_name = 'employee'

urlpatterns = [

    # ===== AUTHENTIFICATION =====
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # URLs pour la gestion des mots de passe
    path('change-password/', change_password_view, name='change_password'),
    path('password-reset-request/', password_reset_request, name='password_reset_request'),  # ← CORRIGÉ
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    #path('test-reset/<str:username>/', test_reset_account, name='test_reset'),


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
    path('api/affectation/<int:id>/update/', views.api_affectation_update_modal, name='api_affectation_update_modal'),
    path('api/affectation/<int:id>/delete/', views.api_affectation_delete_modal, name='api_affectation_delete_modal'),

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

    # API Historique Noms/Prénoms (ZYNP)
    path('api/znp/<int:id>/', views.api_znp_detail, name='api_znp_detail'),
    path('api/znp/create/', views.api_znp_create_modal, name='api_znp_create_modal'),
    path('api/znp/<int:id>/update/', views.api_znp_update_modal, name='api_znp_update_modal'),
    path('api/znp/<int:id>/delete/', views.api_znp_delete_modal, name='api_znp_delete_modal'),

    # API Personnes à prévenir (ZYPP)
    path('ajax/personne-prevenir/<int:id>/detail/', api_personne_prevenir_detail, name='api_personne_prevenir_detail'),
    path('ajax/personne-prevenir/create/', api_personne_prevenir_create_modal, name='api_personne_prevenir_create'),
    path('ajax/personne-prevenir/<int:id>/update/', api_personne_prevenir_update_modal,name='api_personne_prevenir_update'),
    path('ajax/personne-prevenir/<int:id>/delete/', api_personne_prevenir_delete_modal,name='api_personne_prevenir_delete'),

    # API Identité Bancaire (ZYIB)
    path('ajax/identite-bancaire/<uuid:employe_uuid>/detail/', api_identite_bancaire_detail, name='api_identite_bancaire_detail'),
    path('ajax/identite-bancaire/<uuid:employe_uuid>/save/', api_identite_bancaire_create_or_update, name='api_identite_bancaire_save'),
    path('ajax/identite-bancaire/<uuid:employe_uuid>/delete/', api_identite_bancaire_delete, name='api_identite_bancaire_delete'),


# Gestion des rôles
    path('roles/', views.gestion_roles_employes, name='gestion_roles'),
    path('roles/attribuer/', views.attribuer_role, name='attribuer_role'),
    path('roles/retirer/<int:attribution_id>/', views.retirer_role, name='retirer_role'),
    path('roles/reactiver/<int:attribution_id>/', views.reactiver_role, name='reactiver_role'),
    path('roles/modifier/<int:attribution_id>/', views.modifier_role, name='modifier_role'),
    path('roles/supprimer/<int:attribution_id>/', views.supprimer_role, name='supprimer_role'),
    path('roles/employe/<uuid:employe_uuid>/', views.roles_employe, name='roles_employe'),

    # Profil
    path('profil/<str:matricule>/', views.profil_employe, name='profil'),
    path('profil/<str:matricule>/upload-photo/', views.upload_photo, name='upload_photo'),

    # Contacts d'urgence
    path('profil/<str:matricule>/contact-urgence/create/', views.create_contact_urgence, name='create_contact_urgence'),
    path('contact-urgence/<int:contact_id>/detail/', views.contact_urgence_detail, name='contact_urgence_detail'),
    path('contact-urgence/<int:contact_id>/update/', views.update_contact_urgence, name='update_contact_urgence'),
    path('contact-urgence/<int:contact_id>/delete/', views.delete_contact_urgence, name='delete_contact_urgence'),

    # Documents
    path('profil/<str:matricule>/upload-document/', views.upload_document, name='upload_document'),
    path('document/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]
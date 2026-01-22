# employee/urls_modules/api_urls.py
"""
URLs pour toutes les API modales (CRUD AJAX).
"""
from django.urls import path

# Import des vues API refactorisées
from employee.views_api.api import (
    # Téléphone
    api_telephone_detail,
    api_telephone_create_modal,
    api_telephone_update_modal,
    api_telephone_delete_modal,
    # Email
    api_email_detail,
    api_email_create_modal,
    api_email_update_modal,
    api_email_delete_modal,
    # Adresse
    api_adresse_detail,
    api_adresse_create_modal,
    api_adresse_update_modal,
    api_adresse_delete_modal,
    # Contrat
    api_contrat_detail,
    api_contrat_create_modal,
    api_contrat_update_modal,
    api_contrat_delete_modal,
    # Affectation
    api_affectation_detail,
    api_affectation_create_modal,
    api_affectation_update_modal,
    api_affectation_delete_modal,
    # Document
    api_document_create_modal,
    api_document_delete_modal,
    # Famille (ZYFA)
    api_famille_detail,
    api_famille_create_modal,
    api_famille_update_modal,
    api_famille_delete_modal,
    # Historique Noms/Prénoms (ZYNP)
    api_znp_detail,
    api_znp_create_modal,
    api_znp_update_modal,
    api_znp_delete_modal,
    # Personnes à prévenir (ZYPP)
    api_personne_prevenir_detail,
    api_personne_prevenir_create_modal,
    api_personne_prevenir_update_modal,
    api_personne_prevenir_delete_modal,
    # Identité Bancaire (ZYIB)
    api_identite_bancaire_detail,
    api_identite_bancaire_create_or_update,
    api_identite_bancaire_delete,
    # Photo
    modifier_photo_ajax,
    supprimer_photo_ajax,
    # Helper
    api_postes_by_departement,
)

urlpatterns = [
    # ===== API Adresses =====
    path('api/adresse/<int:id>/', api_adresse_detail, name='api_adresse_detail_modal'),
    path('api/adresse/create/', api_adresse_create_modal, name='api_adresse_create_modal'),
    path('api/adresse/<int:id>/update/', api_adresse_update_modal, name='api_adresse_update_modal'),
    path('api/adresse/<int:id>/delete/', api_adresse_delete_modal, name='api_adresse_delete_modal'),

    # ===== API Téléphones =====
    path('api/telephone/<int:id>/', api_telephone_detail, name='api_telephone_detail_modal'),
    path('api/telephone/create/', api_telephone_create_modal, name='api_telephone_create_modal'),
    path('api/telephone/<int:id>/update/', api_telephone_update_modal, name='api_telephone_update_modal'),
    path('api/telephone/<int:id>/delete/', api_telephone_delete_modal, name='api_telephone_delete_modal'),

    # ===== API Emails =====
    path('api/email/<int:id>/', api_email_detail, name='api_email_detail_modal'),
    path('api/email/create/', api_email_create_modal, name='api_email_create_modal'),
    path('api/email/<int:id>/update/', api_email_update_modal, name='api_email_update_modal'),
    path('api/email/<int:id>/delete/', api_email_delete_modal, name='api_email_delete_modal'),

    # ===== API Documents =====
    path('api/document/create/', api_document_create_modal, name='api_document_create_modal'),
    path('api/document/<int:id>/delete/', api_document_delete_modal, name='api_document_delete_modal'),

    # ===== API Contrats =====
    path('api/contrat/<int:id>/', api_contrat_detail, name='api_contrat_detail_modal'),
    path('api/contrat/create/', api_contrat_create_modal, name='api_contrat_create_modal'),
    path('api/contrat/<int:id>/update/', api_contrat_update_modal, name='api_contrat_update_modal'),
    path('api/contrat/<int:id>/delete/', api_contrat_delete_modal, name='api_contrat_delete_modal'),

    # ===== API Affectations =====
    path('api/affectation/<int:id>/', api_affectation_detail, name='api_affectation_detail_modal'),
    path('api/affectation/create/', api_affectation_create_modal, name='api_affectation_create_modal'),
    path('api/affectation/<int:id>/update/', api_affectation_update_modal, name='api_affectation_update_modal'),
    path('api/affectation/<int:id>/delete/', api_affectation_delete_modal, name='api_affectation_delete_modal'),

    # ===== API Helper =====
    path('api/postes/', api_postes_by_departement, name='api_postes_by_departement'),

    # ===== API Famille (ZYFA) =====
    path('api/famille/create/', api_famille_create_modal, name='api_famille_create'),
    path('api/famille/<int:id>/update/', api_famille_update_modal, name='api_famille_update'),
    path('api/famille/<int:id>/delete/', api_famille_delete_modal, name='api_famille_delete'),
    path('api/famille/<int:id>/', api_famille_detail, name='api_famille_detail'),

    # ===== API Historique Noms/Prénoms (ZYNP) =====
    path('api/znp/<int:id>/', api_znp_detail, name='api_znp_detail'),
    path('api/znp/create/', api_znp_create_modal, name='api_znp_create_modal'),
    path('api/znp/<int:id>/update/', api_znp_update_modal, name='api_znp_update_modal'),
    path('api/znp/<int:id>/delete/', api_znp_delete_modal, name='api_znp_delete_modal'),

    # ===== API Personnes à prévenir (ZYPP) =====
    path('ajax/personne-prevenir/<int:id>/detail/', api_personne_prevenir_detail, name='api_personne_prevenir_detail'),
    path('ajax/personne-prevenir/create/', api_personne_prevenir_create_modal, name='api_personne_prevenir_create'),
    path('ajax/personne-prevenir/<int:id>/update/', api_personne_prevenir_update_modal, name='api_personne_prevenir_update'),
    path('ajax/personne-prevenir/<int:id>/delete/', api_personne_prevenir_delete_modal, name='api_personne_prevenir_delete'),

    # ===== API Identité Bancaire (ZYIB) =====
    path('ajax/identite-bancaire/<uuid:employe_uuid>/detail/', api_identite_bancaire_detail, name='api_identite_bancaire_detail'),
    path('ajax/identite-bancaire/<uuid:employe_uuid>/save/', api_identite_bancaire_create_or_update, name='api_identite_bancaire_save'),
    path('ajax/identite-bancaire/<uuid:employe_uuid>/delete/', api_identite_bancaire_delete, name='api_identite_bancaire_delete'),

    # ===== Photo AJAX =====
    path('ajax/photo/modifier/', modifier_photo_ajax, name='modifier_photo_ajax'),
    path('ajax/photo/<uuid:uuid>/supprimer/', supprimer_photo_ajax, name='supprimer_photo_ajax'),
]

# employee/views_api/__init__.py
"""
Package des vues API pour l'application employee.

Structure:
    - api/         : Vues API modales (CRUD via AJAX)
"""

# Pour compatibilité, on réexporte les vues API modales
from .api import (
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
)

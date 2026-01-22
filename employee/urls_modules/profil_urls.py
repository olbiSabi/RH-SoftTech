# employee/urls_modules/profil_urls.py
"""
URLs pour le profil employé, contacts d'urgence et documents.
"""
from django.urls import path

from employee.views_modules.profil_views import (
    profil_employe,
    upload_photo,
    create_contact_urgence,
    contact_urgence_detail,
    update_contact_urgence,
    delete_contact_urgence,
    upload_document,
    delete_document,
)

urlpatterns = [
    # Profil
    path('profil/<str:matricule>/', profil_employe, name='profil'),
    path('profil/<str:matricule>/upload-photo/', upload_photo, name='upload_photo'),

    # Contacts d'urgence
    path('profil/<str:matricule>/contact-urgence/create/', create_contact_urgence, name='create_contact_urgence'),
    path('contact-urgence/<int:contact_id>/detail/', contact_urgence_detail, name='contact_urgence_detail'),
    path('contact-urgence/<int:contact_id>/update/', update_contact_urgence, name='update_contact_urgence'),
    path('contact-urgence/<int:contact_id>/delete/', delete_contact_urgence, name='delete_contact_urgence'),

    # Documents
    path('profil/<str:matricule>/upload-document/', upload_document, name='upload_document'),
    path('document/<int:document_id>/delete/', delete_document, name='delete_document'),
]

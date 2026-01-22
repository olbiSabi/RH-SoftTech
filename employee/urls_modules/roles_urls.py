# employee/urls_modules/roles_urls.py
"""
URLs pour la gestion des rôles des employés.
"""
from django.urls import path

from employee.views_modules.roles_views import (
    gestion_roles_employes,
    attribuer_role,
    retirer_role,
    reactiver_role,
    modifier_role,
    supprimer_role,
    roles_employe,
)

urlpatterns = [
    path('roles/', gestion_roles_employes, name='gestion_roles'),
    path('roles/attribuer/', attribuer_role, name='attribuer_role'),
    path('roles/retirer/<int:attribution_id>/', retirer_role, name='retirer_role'),
    path('roles/reactiver/<int:attribution_id>/', reactiver_role, name='reactiver_role'),
    path('roles/modifier/<int:attribution_id>/', modifier_role, name='modifier_role'),
    path('roles/supprimer/<int:attribution_id>/', supprimer_role, name='supprimer_role'),
    path('roles/employe/<uuid:employe_uuid>/', roles_employe, name='roles_employe'),
]

# employee/views_modules/__init__.py
"""
Module regroupant toutes les vues de l'application employee.
Réorganisation du fichier views.py monolithique en modules spécialisés.
"""

# Vues d'embauche
from .embauche_views import (
    embauche_agent,
    valider_embauche,
)

# Vues CRUD employés
from .employee_views import (
    EmployeListView,
    EmployeCreateView,
    EmployeUpdateView,
    EmployeDeleteView,
)

# Vues dossier individuel
from .dossier_views import (
    DossierIndividuelView,
    detail_employe,
    get_historique_actif,
)

# Vues gestion des rôles
from .roles_views import (
    gestion_roles_employes,
    attribuer_role,
    retirer_role,
    reactiver_role,
    modifier_role,
    roles_employe,
    supprimer_role,
)

# Vues profil employé
from .profil_views import (
    profil_employe,
    upload_photo,
    create_contact_urgence,
    contact_urgence_detail,
    update_contact_urgence,
    delete_contact_urgence,
    upload_document,
    delete_document,
)

# Dashboard
from .dashboard_views import (
    dashboard,
    handler400,
)

__all__ = [
    # Embauche
    'embauche_agent',
    'valider_embauche',

    # Employés CRUD
    'EmployeListView',
    'EmployeCreateView',
    'EmployeUpdateView',
    'EmployeDeleteView',

    # Dossier
    'DossierIndividuelView',
    'detail_employe',
    'get_historique_actif',

    # Rôles
    'gestion_roles_employes',
    'attribuer_role',
    'retirer_role',
    'reactiver_role',
    'modifier_role',
    'roles_employe',
    'supprimer_role',

    # Profil
    'profil_employe',
    'upload_photo',
    'create_contact_urgence',
    'contact_urgence_detail',
    'update_contact_urgence',
    'delete_contact_urgence',
    'upload_document',
    'delete_document',

    # Dashboard
    'dashboard',
    'handler400',
]

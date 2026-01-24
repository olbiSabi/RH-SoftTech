# employee/views.py
"""
Point d'entrée pour les vues de l'application employee.
Ce fichier ré-exporte les vues depuis les modules pour assurer la rétrocompatibilité.

Les vues sont organisées dans:
- views_modules/embauche_views.py - Vues d'embauche
- views_modules/employee_views.py - CRUD employés
- views_modules/dossier_views.py - Dossier individuel
- views_modules/roles_views.py - Gestion des rôles
- views_modules/profil_views.py - Profil employé
- views_modules/dashboard_views.py - Dashboard
- views_api/api/ - APIs modales
"""

# =============================================================================
# RÉ-EXPORTS DEPUIS LES MODULES
# =============================================================================

# Vues d'embauche
from employee.views_modules.embauche_views import (
    embauche_agent,
    valider_embauche,
)

# Vues CRUD employés
from employee.views_modules.employee_views import (
    EmployeListView,
    EmployeCreateView,
    EmployeUpdateView,
    EmployeDeleteView,
)

# Vues dossier individuel
from employee.views_modules.dossier_views import (
    DossierIndividuelView,
    detail_employe,
    get_historique_actif,
)

# Vues gestion des rôles
from employee.views_modules.roles_views import (
    gestion_roles_employes,
    attribuer_role,
    retirer_role,
    reactiver_role,
    modifier_role,
    roles_employe,
    supprimer_role,
)

# Vues profil employé
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

# Dashboard
from employee.views_modules.dashboard_views import (
    dashboard,
)

# Services réexportés pour rétrocompatibilité
from employee.services.embauche_service import EmbaucheService

# Fonction utilitaire réexportée
create_user_account = EmbaucheService.create_user_account

# Fonction utilitaire de validation des chevauchements
from employee.services.validation_service import ValidationService
validate_date_overlap = ValidationService.check_overlap


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Embauche
    'embauche_agent',
    'valider_embauche',
    'create_user_account',
    'validate_date_overlap',

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
]

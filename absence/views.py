# absence/views.py
"""
Point d'entrée pour les vues de l'application absence.

ARCHITECTURE MODULAIRE:
Ce fichier réexporte les vues depuis leurs modules respectifs pour maintenir
la compatibilité ascendante. Les vues sont maintenant organisées en:

- views_modules/configuration_views.py : Conventions, jours fériés, types, paramètres
- views_modules/acquisition_views.py : Gestion des acquisitions
- views_modules/absence_views.py : Création, modification, liste des absences
- views_modules/validation_views.py : Validation manager et RH

- views_api/convention_api.py : APIs CRUD pour conventions
- views_api/jour_ferie_api.py : APIs CRUD pour jours fériés
- views_api/type_absence_api.py : APIs CRUD pour types d'absence
- views_api/parametre_calcul_api.py : APIs CRUD pour paramètres de calcul
- views_api/acquisition_api.py : APIs pour acquisitions
- views_api/absence_api.py : APIs pour absences
- views_api/notification_api.py : APIs pour notifications

Pour les nouveaux développements, importez directement depuis les modules spécifiques.
"""

# ==============================================================================
# VUES DE PAGES
# ==============================================================================

# Configuration
from absence.views_modules.configuration_views import (
    liste_conventions,
    liste_jours_feries,
    liste_types_absence,
    liste_parametres_calcul,
)

# Acquisitions
from absence.views_modules.acquisition_views import (
    liste_acquisitions,
)

# Absences
from absence.views_modules.absence_views import (
    liste_absences,
    creer_absence,
    modifier_absence,
)

# Validation
from absence.views_modules.validation_views import (
    validation_manager,
    validation_rh,
    consultation_absences,
)

# ==============================================================================
# APIS
# ==============================================================================

# APIs Convention
from absence.views_api.convention_api import (
    api_convention_detail,
    api_convention_create,
    api_convention_update,
    api_convention_delete,
    api_convention_toggle_actif,
)

# APIs Jour férié
from absence.views_api.jour_ferie_api import (
    api_jour_ferie_detail,
    api_jour_ferie_create,
    api_jour_ferie_update,
    api_jour_ferie_delete,
    api_jour_ferie_toggle,
    api_dupliquer_jours_feries,
    api_jours_feries,
)

# APIs Type absence
from absence.views_api.type_absence_api import (
    api_type_absence_detail,
    api_type_absence_create,
    api_type_absence_update,
    api_type_absence_delete,
    api_type_absence_toggle,
)

# APIs Paramètre calcul
from absence.views_api.parametre_calcul_api import (
    api_parametre_calcul_detail,
    api_parametre_calcul_create,
    api_parametre_calcul_update,
    api_parametre_calcul_delete,
)

# APIs Acquisition
from absence.views_api.acquisition_api import (
    api_acquisition_detail,
    api_acquisition_update,
    api_acquisition_delete,
    api_recalculer_acquisition,
    api_calculer_acquisitions,
    api_calculer_acquis_a_date,
    api_acquisition_employe_annee,
)

# APIs Absence
from absence.views_api.absence_api import (
    api_absence_detail,
    api_absence_delete,
    api_absence_annuler,
    api_valider_absence,
    api_historique_validation,
    api_verifier_solde,
    api_mes_absences_calendrier,
)

# APIs Notification
from absence.views_api.notification_api import (
    notification_detail,
    marquer_toutes_lues,
    toutes_notifications,
    notification_counts,
    marquer_notification_lue,
)

# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Vues de pages - Configuration
    'liste_conventions',
    'liste_jours_feries',
    'liste_types_absence',
    'liste_parametres_calcul',
    # Vues de pages - Acquisitions
    'liste_acquisitions',
    # Vues de pages - Absences
    'liste_absences',
    'creer_absence',
    'modifier_absence',
    # Vues de pages - Validation
    'validation_manager',
    'validation_rh',
    'consultation_absences',
    # APIs Convention
    'api_convention_detail',
    'api_convention_create',
    'api_convention_update',
    'api_convention_delete',
    'api_convention_toggle_actif',
    # APIs Jour férié
    'api_jour_ferie_detail',
    'api_jour_ferie_create',
    'api_jour_ferie_update',
    'api_jour_ferie_delete',
    'api_jour_ferie_toggle',
    'api_dupliquer_jours_feries',
    'api_jours_feries',
    # APIs Type absence
    'api_type_absence_detail',
    'api_type_absence_create',
    'api_type_absence_update',
    'api_type_absence_delete',
    'api_type_absence_toggle',
    # APIs Paramètre calcul
    'api_parametre_calcul_detail',
    'api_parametre_calcul_create',
    'api_parametre_calcul_update',
    'api_parametre_calcul_delete',
    # APIs Acquisition
    'api_acquisition_detail',
    'api_acquisition_update',
    'api_acquisition_delete',
    'api_recalculer_acquisition',
    'api_calculer_acquisitions',
    'api_calculer_acquis_a_date',
    'api_acquisition_employe_annee',
    # APIs Absence
    'api_absence_detail',
    'api_absence_delete',
    'api_absence_annuler',
    'api_valider_absence',
    'api_historique_validation',
    'api_verifier_solde',
    'api_mes_absences_calendrier',
    # APIs Notification
    'notification_detail',
    'marquer_toutes_lues',
    'toutes_notifications',
    'notification_counts',
    'marquer_notification_lue',
]

# absence/views_api/__init__.py
"""
Vues API pour l'application absence.
Exports de toutes les vues API modulaires.
"""
from .convention_api import (
    api_convention_detail,
    api_convention_create,
    api_convention_update,
    api_convention_delete,
    api_convention_toggle_actif,
)

from .jour_ferie_api import (
    api_jour_ferie_detail,
    api_jour_ferie_create,
    api_jour_ferie_update,
    api_jour_ferie_delete,
    api_jour_ferie_toggle,
    api_dupliquer_jours_feries,
    api_jours_feries,
)

from .type_absence_api import (
    api_type_absence_detail,
    api_type_absence_create,
    api_type_absence_update,
    api_type_absence_delete,
    api_type_absence_toggle,
)

from .parametre_calcul_api import (
    api_parametre_calcul_detail,
    api_parametre_calcul_create,
    api_parametre_calcul_update,
    api_parametre_calcul_delete,
)

from .acquisition_api import (
    api_acquisition_detail,
    api_acquisition_update,
    api_acquisition_delete,
    api_recalculer_acquisition,
    api_calculer_acquisitions,
    api_calculer_acquis_a_date,
    api_acquisition_employe_annee,
)

from .absence_api import (
    api_absence_detail,
    api_absence_delete,
    api_absence_annuler,
    api_valider_absence,
    api_historique_validation,
    api_verifier_solde,
    api_mes_absences_calendrier,
)

from .notification_api import (
    notification_detail,
    marquer_toutes_lues,
    toutes_notifications,
    notification_counts,
    marquer_notification_lue,
)

__all__ = [
    # Convention
    'api_convention_detail',
    'api_convention_create',
    'api_convention_update',
    'api_convention_delete',
    'api_convention_toggle_actif',
    # Jour férié
    'api_jour_ferie_detail',
    'api_jour_ferie_create',
    'api_jour_ferie_update',
    'api_jour_ferie_delete',
    'api_jour_ferie_toggle',
    'api_dupliquer_jours_feries',
    'api_jours_feries',
    # Type absence
    'api_type_absence_detail',
    'api_type_absence_create',
    'api_type_absence_update',
    'api_type_absence_delete',
    'api_type_absence_toggle',
    # Paramètre calcul
    'api_parametre_calcul_detail',
    'api_parametre_calcul_create',
    'api_parametre_calcul_update',
    'api_parametre_calcul_delete',
    # Acquisition
    'api_acquisition_detail',
    'api_acquisition_update',
    'api_acquisition_delete',
    'api_recalculer_acquisition',
    'api_calculer_acquisitions',
    'api_calculer_acquis_a_date',
    'api_acquisition_employe_annee',
    # Absence
    'api_absence_detail',
    'api_absence_delete',
    'api_absence_annuler',
    'api_valider_absence',
    'api_historique_validation',
    'api_verifier_solde',
    'api_mes_absences_calendrier',
    # Notification
    'notification_detail',
    'marquer_toutes_lues',
    'toutes_notifications',
    'notification_counts',
    'marquer_notification_lue',
]

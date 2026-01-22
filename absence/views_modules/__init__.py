# absence/views_modules/__init__.py
"""
Vues modulaires pour l'application absence.

Organisation:
- configuration_views.py : Conventions, jours fériés, types d'absence, paramètres
- acquisition_views.py : Gestion des acquisitions de congés
- absence_views.py : Création, modification, liste des absences
- validation_views.py : Validation manager et RH
"""

# Vues de configuration
from absence.views_modules.configuration_views import (
    liste_conventions,
    liste_jours_feries,
    liste_types_absence,
    liste_parametres_calcul,
)

# Vues d'acquisition
from absence.views_modules.acquisition_views import (
    liste_acquisitions,
)

# Vues d'absence
from absence.views_modules.absence_views import (
    liste_absences,
    creer_absence,
    modifier_absence,
)

# Vues de validation
from absence.views_modules.validation_views import (
    validation_manager,
    validation_rh,
    consultation_absences,
)

__all__ = [
    # Configuration
    'liste_conventions',
    'liste_jours_feries',
    'liste_types_absence',
    'liste_parametres_calcul',
    # Acquisitions
    'liste_acquisitions',
    # Absences
    'liste_absences',
    'creer_absence',
    'modifier_absence',
    # Validation
    'validation_manager',
    'validation_rh',
    'consultation_absences',
]

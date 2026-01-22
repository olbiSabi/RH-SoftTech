# absence/services/__init__.py
"""
Couche services pour l'application absence.
Contient la logique métier extraite des modèles et vues.
"""

from .acquisition_service import AcquisitionService
from .absence_service import AbsenceService
from .notification_service import NotificationService
from .validation_service import ValidationService

__all__ = [
    'AcquisitionService',
    'AbsenceService',
    'NotificationService',
    'ValidationService',
]

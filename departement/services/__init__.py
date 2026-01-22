# departement/services/__init__.py
"""
Services pour l'application Département.

Ce module contient la logique métier séparée des vues.
"""

from .departement_service import DepartementService
from .poste_service import PosteService
from .manager_service import ManagerService

__all__ = [
    'DepartementService',
    'PosteService',
    'ManagerService',
]

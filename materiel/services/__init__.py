# materiel/services/__init__.py
"""
Services métier pour le module Suivi du Matériel & Parc.
"""
from materiel.services.materiel_service import MaterielService
from materiel.services.statistiques_service import StatistiquesMaterielService

__all__ = [
    'MaterielService',
    'StatistiquesMaterielService',
]

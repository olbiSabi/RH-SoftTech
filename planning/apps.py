"""
Configuration du module Planning.
"""
from django.apps import AppConfig


class PlanningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planning'
    verbose_name = 'Planning et Pointage'
    
    def ready(self):
        # Import des signaux si nécessaire
        pass

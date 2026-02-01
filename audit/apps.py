# audit/apps.py
from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Conformité & Audit'

    def ready(self):
        """Importe les signaux lors du démarrage de l'application."""
        import audit.signals  # noqa

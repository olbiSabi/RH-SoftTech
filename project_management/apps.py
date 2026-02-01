from django.apps import AppConfig


class ProjectManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'project_management'
    verbose_name = 'Gestion de Projet'

    def ready(self):
        """Importe les signaux au démarrage de l'application."""
        import project_management.signals  # noqa

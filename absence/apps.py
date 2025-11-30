from django.apps import AppConfig


class AbsenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'absence'
    verbose_name = 'Gestion des Absences'

    def ready(self):
        """Importer les signaux au démarrage de l'application"""
        import absence.signals  # 🆕 AJOUTEZ CETTE LIGNE
from django.apps import AppConfig

class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employee'  # Nom de l'application
    verbose_name = "Gestion des Employés"  # Nom lisible

    def ready(self):
        """Méthode appelée quand l'application est prête"""
        # Import des signaux
        import employee.signals
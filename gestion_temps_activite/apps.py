from django.apps import AppConfig


class GestionTempsActiviteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_temps_activite'
    verbose_name = 'Gestion Temps et Activités'

    def ready(self):
        # Pour les signaux ou initialisation
        import gestion_temps_activite.signals
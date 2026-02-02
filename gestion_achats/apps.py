from django.apps import AppConfig


class GestionAchatsConfig(AppConfig):
    """Configuration de l'application Gestion des Achats & Commandes (GAC)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_achats'
    verbose_name = 'Gestion des Achats & Commandes'

    def ready(self):
        """
        Méthode appelée quand Django démarre.
        Import des signaux pour activer les notifications automatiques.
        """
        import gestion_achats.signals  # noqa

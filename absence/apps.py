# absence/apps.py
from django.apps import AppConfig


class AbsenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'absence'

    def ready(self):
        # Créer les permissions par défaut
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate)
        def create_absence_permissions(sender, **kwargs):
            if sender.name == 'absence':
                # Permissions pour le modèle Absence
                content_type = ContentType.objects.get_for_model(self.get_model('Absence'))

                permissions_data = [
                    ('valider_absence_rh', 'Peut valider les absences (RH)'),
                    ('valider_absence_manager', 'Peut valider les absences (Manager)'),
                    ('voir_toutes_absences', 'Peut voir toutes les absences'),
                    ('gerer_types_absence', 'Peut gérer les types d\'absence'),
                    ('gerer_conventions', 'Peut gérer les conventions collectives'),
                    ('exporter_absences', 'Peut exporter les données d\'absence'),
                    ('declarer_absence', 'Peut déclarer une absence'),
                    ('voir_mes_absences', 'Peut voir ses propres absences'),
                ]

                for codename, name in permissions_data:
                    Permission.objects.get_or_create(
                        codename=codename,
                        content_type=content_type,
                        defaults={'name': name}
                    )
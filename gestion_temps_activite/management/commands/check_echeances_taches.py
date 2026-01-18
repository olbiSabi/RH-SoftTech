# management/commands/check_echeances_taches.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_temps_activite.models import ZDTA
from gestion_temps_activite.views import notifier_echeance_tache_proche


class Command(BaseCommand):
    help = 'Vérifie les échéances de tâches et envoie des notifications'

    def handle(self, *args, **options):
        aujourdhui = timezone.now().date()

        # Tâches avec date d'échéance dans les 2 prochains jours
        taches_echeance = ZDTA.objects.filter(
            date_fin_prevue__gte=aujourdhui,
            date_fin_prevue__lte=aujourdhui + timezone.timedelta(days=2),
            statut__in=['A_FAIRE', 'EN_COURS']
        ).select_related('assignee')

        count = 0
        for tache in taches_echeance:
            if notifier_echeance_tache_proche(tache):
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} notification(s) d\'échéance envoyée(s)')
        )
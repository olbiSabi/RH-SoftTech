"""
Commande de management Django pour vérifier les délais de validation des demandes.

Cette commande identifie les demandes d'achat en attente de validation depuis trop longtemps
et envoie des notifications de rappel aux validateurs concernés.

Usage:
    python manage.py verifier_delais_validation [--delai-n1 JOURS] [--delai-n2 JOURS] [--dry-run]

Options:
    --delai-n1: Délai maximum en jours pour validation N1 (défaut: 3)
    --delai-n2: Délai maximum en jours pour validation N2 (défaut: 5)
    --dry-run: Mode simulation sans envoi de notifications

Exemples:
    python manage.py verifier_delais_validation
    python manage.py verifier_delais_validation --delai-n1 2 --delai-n2 4
    python manage.py verifier_delais_validation --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from gestion_achats.models import GACDemandeAchat
from gestion_achats.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vérifie les délais de validation des demandes d\'achat et envoie des rappels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delai-n1',
            type=int,
            default=3,
            help='Délai maximum en jours pour validation N1 (défaut: 3)'
        )
        parser.add_argument(
            '--delai-n2',
            type=int,
            default=5,
            help='Délai maximum en jours pour validation N2 (défaut: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation sans envoi de notifications'
        )

    def handle(self, *args, **options):
        delai_n1 = options['delai_n1']
        delai_n2 = options['delai_n2']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'Vérification des délais de validation des demandes d\'achat\n'
            f'{"="*70}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune notification ne sera envoyée\n'))

        self.stdout.write(f'Délai maximum N1: {delai_n1} jours')
        self.stdout.write(f'Délai maximum N2: {delai_n2} jours\n')

        # Vérifier les demandes en attente de validation N1
        demandes_n1_retard = self._verifier_validation_n1(delai_n1, dry_run)

        # Vérifier les demandes en attente de validation N2
        demandes_n2_retard = self._verifier_validation_n2(delai_n2, dry_run)

        # Résumé
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'RÉSUMÉ\n'
            f'{"="*70}'
        ))
        self.stdout.write(f'Demandes en retard de validation N1: {len(demandes_n1_retard)}')
        self.stdout.write(f'Demandes en retard de validation N2: {len(demandes_n2_retard)}')
        self.stdout.write(f'Total notifications envoyées: {0 if dry_run else len(demandes_n1_retard) + len(demandes_n2_retard)}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nMode simulation activé - Pour envoyer les notifications, '
                'exécutez la commande sans --dry-run'
            ))

    def _verifier_validation_n1(self, delai_jours, dry_run):
        """Vérifie les demandes en attente de validation N1."""
        self.stdout.write(self.style.HTTP_INFO('\n--- Vérification validation N1 ---'))

        date_limite = timezone.now() - timedelta(days=delai_jours)

        demandes = GACDemandeAchat.objects.filter(
            statut='SOUMISE',
            date_soumission__lte=date_limite
        ).select_related('demandeur', 'validateur_n1')

        self.stdout.write(f'Demandes trouvées: {demandes.count()}')

        demandes_traitees = []
        for demande in demandes:
            delai_actuel = (timezone.now() - demande.date_soumission).days

            self.stdout.write(
                f'  • Demande {demande.numero} - En attente depuis {delai_actuel} jours'
            )
            self.stdout.write(f'    Demandeur: {demande.demandeur.get_full_name()}')
            if demande.validateur_n1:
                self.stdout.write(f'    Validateur N1: {demande.validateur_n1.get_full_name()}')
            else:
                self.stdout.write(self.style.WARNING('    Aucun validateur N1 assigné!'))

            if not dry_run and demande.validateur_n1:
                try:
                    NotificationService.rappel_validation_n1(demande)
                    self.stdout.write(self.style.SUCCESS('    ✓ Notification envoyée'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erreur: {str(e)}'))
                    logger.error(f'Erreur notification demande {demande.numero}: {str(e)}')
            elif dry_run:
                self.stdout.write('    ℹ Notification (simulation)')

            demandes_traitees.append(demande)

        return demandes_traitees

    def _verifier_validation_n2(self, delai_jours, dry_run):
        """Vérifie les demandes en attente de validation N2."""
        self.stdout.write(self.style.HTTP_INFO('\n--- Vérification validation N2 ---'))

        date_limite = timezone.now() - timedelta(days=delai_jours)

        demandes = GACDemandeAchat.objects.filter(
            statut='VALIDEE_N1',
            date_validation_n1__lte=date_limite
        ).select_related('demandeur', 'validateur_n2')

        self.stdout.write(f'Demandes trouvées: {demandes.count()}')

        demandes_traitees = []
        for demande in demandes:
            delai_actuel = (timezone.now() - demande.date_validation_n1).days

            self.stdout.write(
                f'  • Demande {demande.numero} - En attente depuis {delai_actuel} jours'
            )
            self.stdout.write(f'    Demandeur: {demande.demandeur.get_full_name()}')
            if demande.validateur_n2:
                self.stdout.write(f'    Validateur N2: {demande.validateur_n2.get_full_name()}')
            else:
                self.stdout.write(self.style.WARNING('    Aucun validateur N2 assigné!'))

            if not dry_run and demande.validateur_n2:
                try:
                    NotificationService.rappel_validation_n2(demande)
                    self.stdout.write(self.style.SUCCESS('    ✓ Notification envoyée'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erreur: {str(e)}'))
                    logger.error(f'Erreur notification demande {demande.numero}: {str(e)}')
            elif dry_run:
                self.stdout.write('    ℹ Notification (simulation)')

            demandes_traitees.append(demande)

        return demandes_traitees

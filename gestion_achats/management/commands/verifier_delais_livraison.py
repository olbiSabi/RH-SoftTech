"""
Commande de management Django pour vérifier les délais de livraison des bons de commande.

Cette commande identifie les bons de commande dont la date de livraison souhaitée est dépassée
ou approche, et envoie des notifications de rappel.

Usage:
    python manage.py verifier_delais_livraison [--alerte-jours JOURS] [--dry-run]

Options:
    --alerte-jours: Nombre de jours avant la date de livraison pour alerter (défaut: 2)
    --dry-run: Mode simulation sans envoi de notifications

Exemples:
    python manage.py verifier_delais_livraison
    python manage.py verifier_delais_livraison --alerte-jours 3
    python manage.py verifier_delais_livraison --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import logging

from gestion_achats.models import GACBonCommande
from gestion_achats.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vérifie les délais de livraison des bons de commande et envoie des alertes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--alerte-jours',
            type=int,
            default=2,
            help='Nombre de jours avant la date de livraison pour alerter (défaut: 2)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation sans envoi de notifications'
        )

    def handle(self, *args, **options):
        alerte_jours = options['alerte_jours']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'Vérification des délais de livraison des bons de commande\n'
            f'{"="*70}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune notification ne sera envoyée\n'))

        self.stdout.write(f'Alerte déclenchée {alerte_jours} jours avant la date de livraison\n')

        # Date du jour
        aujourd_hui = date.today()
        date_alerte = aujourd_hui + timedelta(days=alerte_jours)

        # Statuts concernés : ENVOYE, CONFIRME
        statuts_concernes = ['ENVOYE', 'CONFIRME', 'RECU_PARTIEL']

        # Récupérer les BCs avec date de livraison proche ou dépassée
        bcs = GACBonCommande.objects.filter(
            statut__in=statuts_concernes,
            date_livraison_souhaitee__isnull=False
        ).select_related('fournisseur', 'acheteur', 'demande_achat__demandeur')

        # Classifier les BCs
        bcs_en_retard = []
        bcs_bientot_retard = []
        bcs_ok = []

        for bc in bcs:
            if bc.date_livraison_souhaitee < aujourd_hui:
                bcs_en_retard.append(bc)
            elif bc.date_livraison_souhaitee <= date_alerte:
                bcs_bientot_retard.append(bc)
            else:
                bcs_ok.append(bc)

        # Traiter les BCs en retard
        self._traiter_bcs_en_retard(bcs_en_retard, aujourd_hui, dry_run)

        # Traiter les BCs bientôt en retard
        self._traiter_bcs_bientot_retard(bcs_bientot_retard, aujourd_hui, dry_run)

        # Résumé
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'RÉSUMÉ\n'
            f'{"="*70}'
        ))
        self.stdout.write(f'Bons de commande en retard: {len(bcs_en_retard)}')
        self.stdout.write(f'Bons de commande bientôt en retard: {len(bcs_bientot_retard)}')
        self.stdout.write(f'Bons de commande dans les délais: {len(bcs_ok)}')
        self.stdout.write(f'Total notifications envoyées: {0 if dry_run else len(bcs_en_retard) + len(bcs_bientot_retard)}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nMode simulation activé - Pour envoyer les notifications, '
                'exécutez la commande sans --dry-run'
            ))

    def _traiter_bcs_en_retard(self, bcs, aujourd_hui, dry_run):
        """Traite les BCs dont la date de livraison est dépassée."""
        if not bcs:
            self.stdout.write(self.style.SUCCESS('\n✓ Aucun bon de commande en retard'))
            return

        self.stdout.write(self.style.ERROR(f'\n⚠ {len(bcs)} bon(s) de commande en retard:'))

        for bc in bcs:
            jours_retard = (aujourd_hui - bc.date_livraison_souhaitee).days

            self.stdout.write(f'\n  • BC {bc.numero}')
            self.stdout.write(f'    Fournisseur: {bc.fournisseur.raison_sociale}')
            self.stdout.write(f'    Date livraison: {bc.date_livraison_souhaitee.strftime("%d/%m/%Y")}')
            self.stdout.write(self.style.ERROR(f'    Retard: {jours_retard} jour(s)'))
            self.stdout.write(f'    Statut: {bc.get_statut_display()}')
            self.stdout.write(f'    Montant TTC: {bc.montant_total_ttc:.2f} €')

            if not dry_run:
                try:
                    NotificationService.alerte_livraison_retard(bc, jours_retard)
                    self.stdout.write(self.style.SUCCESS('    ✓ Notification envoyée'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erreur: {str(e)}'))
                    logger.error(f'Erreur notification BC {bc.numero}: {str(e)}')
            else:
                self.stdout.write('    ℹ Notification (simulation)')

    def _traiter_bcs_bientot_retard(self, bcs, aujourd_hui, dry_run):
        """Traite les BCs dont la date de livraison approche."""
        if not bcs:
            self.stdout.write(self.style.SUCCESS('\n✓ Aucun bon de commande avec échéance proche'))
            return

        self.stdout.write(self.style.WARNING(f'\n⚡ {len(bcs)} bon(s) de commande avec échéance proche:'))

        for bc in bcs:
            jours_restants = (bc.date_livraison_souhaitee - aujourd_hui).days

            self.stdout.write(f'\n  • BC {bc.numero}')
            self.stdout.write(f'    Fournisseur: {bc.fournisseur.raison_sociale}')
            self.stdout.write(f'    Date livraison: {bc.date_livraison_souhaitee.strftime("%d/%m/%Y")}')
            self.stdout.write(self.style.WARNING(f'    Jours restants: {jours_restants}'))
            self.stdout.write(f'    Statut: {bc.get_statut_display()}')
            self.stdout.write(f'    Montant TTC: {bc.montant_total_ttc:.2f} €')

            if not dry_run:
                try:
                    NotificationService.rappel_livraison_proche(bc, jours_restants)
                    self.stdout.write(self.style.SUCCESS('    ✓ Notification envoyée'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erreur: {str(e)}'))
                    logger.error(f'Erreur notification BC {bc.numero}: {str(e)}')
            else:
                self.stdout.write('    ℹ Notification (simulation)')

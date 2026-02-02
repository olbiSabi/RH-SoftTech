"""
Commande de management Django pour envoyer des rappels sur les réceptions en attente.

Cette commande identifie les réceptions en brouillon (non validées) depuis trop longtemps
et envoie des notifications de rappel aux réceptionnaires et validateurs.

Usage:
    python manage.py rappel_receptions_attente [--delai-jours JOURS] [--dry-run]

Options:
    --delai-jours: Délai maximum en jours avant rappel (défaut: 3)
    --dry-run: Mode simulation sans envoi de notifications

Exemples:
    python manage.py rappel_receptions_attente
    python manage.py rappel_receptions_attente --delai-jours 2
    python manage.py rappel_receptions_attente --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from gestion_achats.models import GACReception
from gestion_achats.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envoie des rappels pour les réceptions en attente de validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delai-jours',
            type=int,
            default=3,
            help='Délai maximum en jours avant rappel (défaut: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation sans envoi de notifications'
        )

    def handle(self, *args, **options):
        delai_jours = options['delai_jours']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'Rappels pour les réceptions en attente de validation\n'
            f'{"="*70}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune notification ne sera envoyée\n'))

        self.stdout.write(f'Délai avant rappel: {delai_jours} jours\n')

        date_limite = timezone.now() - timedelta(days=delai_jours)

        # Récupérer les réceptions en brouillon depuis trop longtemps
        receptions = GACReception.objects.filter(
            statut='BROUILLON',
            date_creation__lte=date_limite
        ).select_related(
            'bon_commande__fournisseur',
            'receptionnaire',
            'bon_commande__acheteur',
            'bon_commande__demande_achat__demandeur'
        ).prefetch_related('lignes')

        self.stdout.write(f'Réceptions trouvées: {receptions.count()}')

        if not receptions.exists():
            self.stdout.write(self.style.SUCCESS('\n✓ Aucune réception en attente au-delà du délai'))
            return

        # Traiter les réceptions
        notifications_envoyees = 0

        for reception in receptions:
            delai_actuel = (timezone.now() - reception.date_creation).days

            self.stdout.write(f'\n  • Réception {reception.numero}')
            self.stdout.write(f'    BC: {reception.bon_commande.numero}')
            self.stdout.write(f'    Fournisseur: {reception.bon_commande.fournisseur.raison_sociale}')
            self.stdout.write(f'    Réceptionnaire: {reception.receptionnaire.get_full_name()}')
            self.stdout.write(f'    Date création: {reception.date_creation.strftime("%d/%m/%Y %H:%M")}')
            self.stdout.write(self.style.WARNING(f'    En attente depuis: {delai_actuel} jours'))

            # Compteur de lignes
            nb_lignes_total = reception.lignes.count()
            nb_lignes_renseignees = reception.lignes.filter(
                quantite_recue__gt=0
            ).count()

            self.stdout.write(f'    Lignes: {nb_lignes_renseignees}/{nb_lignes_total} renseignées')

            # Statut de progression
            if nb_lignes_renseignees == 0:
                statut_progression = 'Aucune ligne renseignée'
                style = self.style.ERROR
            elif nb_lignes_renseignees < nb_lignes_total:
                statut_progression = 'Réception partielle'
                style = self.style.WARNING
            else:
                statut_progression = 'Toutes les lignes renseignées'
                style = self.style.SUCCESS

            self.stdout.write(style(f'    Progression: {statut_progression}'))

            # Envoyer les notifications
            if not dry_run:
                try:
                    # Notifier le réceptionnaire
                    NotificationService.rappel_reception_brouillon(
                        reception,
                        delai_actuel
                    )

                    # Si toutes les lignes sont renseignées, notifier aussi le validateur
                    if nb_lignes_renseignees == nb_lignes_total:
                        NotificationService.rappel_validation_reception(
                            reception,
                            delai_actuel
                        )
                        self.stdout.write(self.style.SUCCESS(
                            '    ✓ Notifications envoyées (réceptionnaire + validateur)'
                        ))
                        notifications_envoyees += 2
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            '    ✓ Notification envoyée (réceptionnaire)'
                        ))
                        notifications_envoyees += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Erreur: {str(e)}'))
                    logger.error(f'Erreur notification réception {reception.numero}: {str(e)}')
            else:
                if nb_lignes_renseignees == nb_lignes_total:
                    self.stdout.write('    ℹ Notifications (simulation): réceptionnaire + validateur')
                    notifications_envoyees += 2
                else:
                    self.stdout.write('    ℹ Notification (simulation): réceptionnaire')
                    notifications_envoyees += 1

        # Résumé
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'RÉSUMÉ\n'
            f'{"="*70}'
        ))
        self.stdout.write(f'Réceptions en attente: {receptions.count()}')
        self.stdout.write(f'Notifications envoyées: {0 if dry_run else notifications_envoyees}')

        # Statistiques détaillées
        receptions_vides = receptions.filter(lignes__quantite_recue=0).distinct().count()
        receptions_partielles = sum(
            1 for r in receptions
            if 0 < r.lignes.filter(quantite_recue__gt=0).count() < r.lignes.count()
        )
        receptions_completes = sum(
            1 for r in receptions
            if r.lignes.filter(quantite_recue__gt=0).count() == r.lignes.count()
        )

        self.stdout.write(f'\nDétail:')
        self.stdout.write(f'  - Aucune ligne renseignée: {receptions_vides}')
        self.stdout.write(f'  - Réception partielle: {receptions_partielles}')
        self.stdout.write(f'  - Toutes lignes renseignées (prêt validation): {receptions_completes}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nMode simulation activé - Pour envoyer les notifications, '
                'exécutez la commande sans --dry-run'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Traitement terminé avec succès'))

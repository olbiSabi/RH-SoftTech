"""
Management command pour vérifier les budgets et envoyer des alertes.

Usage:
    python manage.py verifier_budgets

Cette commande doit être exécutée régulièrement (via cron) pour :
- Détecter les dépassements budgétaires
- Envoyer des alertes aux gestionnaires
- Identifier les budgets en fin de validité
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal
from datetime import timedelta

from gestion_achats.models import GACBudget
from gestion_achats.services.budget_service import BudgetService
from gestion_achats.services.notification_service import NotificationService


class Command(BaseCommand):
    help = 'Vérifie les budgets et envoie des alertes en cas de dépassement ou fin de validité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation, sans envoi de notifications',
        )
        parser.add_argument(
            '--exercice',
            type=int,
            help='Exercice spécifique à vérifier (par défaut: année en cours)',
        )

    def handle(self, *args, **options):
        """Exécute la commande de vérification des budgets."""

        dry_run = options['dry_run']
        exercice = options.get('exercice') or timezone.now().year

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Vérification des budgets'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE SIMULATION (pas d\'envoi de notifications)'))
            self.stdout.write('')

        # Récupérer les budgets de l'exercice en cours
        budgets = GACBudget.objects.filter(exercice=exercice)

        self.stdout.write(f"📊 Analyse de {budgets.count()} budget(s) pour l'exercice {exercice}")
        self.stdout.write('')

        stats = {
            'total': budgets.count(),
            'en_alerte_1': 0,
            'en_alerte_2': 0,
            'depasses': 0,
            'fin_validite': 0,
            'notifications_envoyees': 0,
        }

        for budget in budgets:
            # Calculer le taux de consommation
            taux = budget.taux_consommation()

            self.stdout.write(f"\n🔍 Budget: {budget.code} - {budget.libelle}")
            self.stdout.write(f"   Montant initial: {budget.montant_initial} €")
            self.stdout.write(f"   Montant disponible: {budget.montant_disponible()} €")
            self.stdout.write(f"   Taux de consommation: {taux}%")

            # Vérifier les seuils d'alerte
            if taux >= budget.seuil_alerte_2:
                stats['en_alerte_2'] += 1
                self.stdout.write(self.style.ERROR(f"   ⚠️  ALERTE NIVEAU 2: Seuil de {budget.seuil_alerte_2}% dépassé!"))

                if not budget.alerte_2_envoyee:
                    if not dry_run:
                        self._envoyer_alerte_budget(budget, niveau=2)
                        budget.alerte_2_envoyee = True
                        budget.save()
                        stats['notifications_envoyees'] += 1
                    else:
                        self.stdout.write(self.style.WARNING("      [SIMULATION] Notification niveau 2 à envoyer"))

            elif taux >= budget.seuil_alerte_1:
                stats['en_alerte_1'] += 1
                self.stdout.write(self.style.WARNING(f"   ⚠️  ALERTE NIVEAU 1: Seuil de {budget.seuil_alerte_1}% dépassé!"))

                if not budget.alerte_1_envoyee:
                    if not dry_run:
                        self._envoyer_alerte_budget(budget, niveau=1)
                        budget.alerte_1_envoyee = True
                        budget.save()
                        stats['notifications_envoyees'] += 1
                    else:
                        self.stdout.write(self.style.WARNING("      [SIMULATION] Notification niveau 1 à envoyer"))

            else:
                self.stdout.write(self.style.SUCCESS("   ✅ Budget OK"))

            # Vérifier si le budget est dépassé
            if budget.montant_disponible() < 0:
                stats['depasses'] += 1
                self.stdout.write(self.style.ERROR(f"   ❌ DÉPASSEMENT: {abs(budget.montant_disponible())} € en négatif!"))

            # Vérifier la fin de validité
            jours_restants = (budget.date_fin - timezone.now().date()).days
            if 0 <= jours_restants <= 30:
                stats['fin_validite'] += 1
                self.stdout.write(self.style.WARNING(f"   📅 Fin de validité dans {jours_restants} jour(s)"))

                if not dry_run and jours_restants <= 7:
                    self._envoyer_alerte_fin_validite(budget, jours_restants)
                    stats['notifications_envoyees'] += 1

        # Afficher le résumé
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ DE LA VÉRIFICATION'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f"  📊 Total de budgets analysés: {stats['total']}")
        self.stdout.write(f"  ⚠️  Budgets en alerte niveau 1: {stats['en_alerte_1']}")
        self.stdout.write(f"  🚨 Budgets en alerte niveau 2: {stats['en_alerte_2']}")
        self.stdout.write(f"  ❌ Budgets dépassés: {stats['depasses']}")
        self.stdout.write(f"  📅 Budgets en fin de validité: {stats['fin_validite']}")

        if not dry_run:
            self.stdout.write(f"  📧 Notifications envoyées: {stats['notifications_envoyees']}")
        else:
            self.stdout.write(self.style.WARNING(f"  🔍 Notifications à envoyer: {stats['notifications_envoyees']}"))

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Vérification terminée avec succès!'))
        else:
            self.stdout.write(self.style.WARNING('✅ Simulation terminée!'))

    def _envoyer_alerte_budget(self, budget, niveau):
        """Envoie une alerte de dépassement budgétaire."""
        try:
            NotificationService.notifier_alerte_budget(
                budget=budget,
                niveau=niveau,
                destinataires=[budget.gestionnaire]
            )
            self.stdout.write(self.style.SUCCESS(f"      ✅ Notification niveau {niveau} envoyée à {budget.gestionnaire}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erreur lors de l'envoi: {str(e)}"))

    def _envoyer_alerte_fin_validite(self, budget, jours_restants):
        """Envoie une alerte de fin de validité de budget."""
        try:
            NotificationService.notifier_fin_validite_budget(
                budget=budget,
                jours_restants=jours_restants,
                destinataires=[budget.gestionnaire]
            )
            self.stdout.write(self.style.SUCCESS(f"      ✅ Alerte fin de validité envoyée à {budget.gestionnaire}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erreur lors de l'envoi: {str(e)}"))

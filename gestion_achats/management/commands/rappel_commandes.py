"""
Management command pour envoyer des rappels sur les commandes en retard.

Usage:
    python manage.py rappel_commandes

Cette commande doit être exécutée régulièrement (via cron) pour :
- Identifier les bons de commande non livrés dans les délais
- Envoyer des rappels aux acheteurs
- Notifier les gestionnaires en cas de retard important
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from gestion_achats.models import GACBonCommande
from gestion_achats.services.notification_service import NotificationService
from gestion_achats.constants import (
    STATUT_BC_ENVOYE,
    STATUT_BC_CONFIRME,
    STATUT_BC_RECU_PARTIEL,
)


class Command(BaseCommand):
    help = 'Envoie des rappels pour les bons de commande en retard de livraison'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation, sans envoi de notifications',
        )
        parser.add_argument(
            '--jours',
            type=int,
            default=7,
            help='Nombre de jours de retard avant rappel (défaut: 7)',
        )
        parser.add_argument(
            '--relance',
            action='store_true',
            help='Envoyer aussi des rappels de relance (tous les 7 jours)',
        )

    def handle(self, *args, **options):
        """Exécute la commande d'envoi de rappels."""

        dry_run = options['dry_run']
        jours_retard = options['jours']
        relance = options['relance']

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Vérification des commandes en retard'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE SIMULATION (pas d\'envoi de notifications)'))
            self.stdout.write('')

        today = timezone.now().date()
        date_limite = today - timedelta(days=jours_retard)

        # Récupérer les bons de commande non livrés
        bons_commande = GACBonCommande.objects.filter(
            statut__in=[STATUT_BC_ENVOYE, STATUT_BC_CONFIRME, STATUT_BC_RECU_PARTIEL],
            date_livraison_confirmee__isnull=False,
            date_livraison_confirmee__lt=date_limite
        ).select_related('fournisseur', 'acheteur', 'demande_achat')

        self.stdout.write(f"📦 Analyse de {bons_commande.count()} bon(s) de commande en retard")
        self.stdout.write(f"📅 Date limite de livraison: {date_limite}")
        self.stdout.write('')

        stats = {
            'total': bons_commande.count(),
            'retard_leger': 0,      # < 15 jours
            'retard_moyen': 0,       # 15-30 jours
            'retard_important': 0,   # > 30 jours
            'rappels_envoyes': 0,
        }

        for bc in bons_commande:
            jours_retard_reel = (today - bc.date_livraison_confirmee).days

            self.stdout.write(f"\n📦 BC: {bc.numero}")
            self.stdout.write(f"   Fournisseur: {bc.fournisseur.raison_sociale}")
            self.stdout.write(f"   Date de livraison prévue: {bc.date_livraison_confirmee}")
            self.stdout.write(f"   Retard: {jours_retard_reel} jour(s)")
            self.stdout.write(f"   Statut: {bc.get_statut_display()}")

            # Catégoriser le retard
            if jours_retard_reel < 15:
                stats['retard_leger'] += 1
                niveau_alerte = 'leger'
                self.stdout.write(self.style.WARNING("   ⚠️  Retard léger"))
            elif jours_retard_reel < 30:
                stats['retard_moyen'] += 1
                niveau_alerte = 'moyen'
                self.stdout.write(self.style.WARNING("   🔶 Retard moyen"))
            else:
                stats['retard_important'] += 1
                niveau_alerte = 'important'
                self.stdout.write(self.style.ERROR("   🚨 Retard important!"))

            # Envoyer le rappel
            if not dry_run:
                if self._doit_envoyer_rappel(bc, jours_retard_reel, relance):
                    try:
                        self._envoyer_rappel_commande(bc, jours_retard_reel, niveau_alerte)
                        stats['rappels_envoyes'] += 1
                        self.stdout.write(self.style.SUCCESS("      ✅ Rappel envoyé"))

                        # Enregistrer la date du dernier rappel
                        bc.date_dernier_rappel = today
                        bc.save(update_fields=['date_dernier_rappel'])

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"      ❌ Erreur: {str(e)}"))
                else:
                    self.stdout.write(self.style.WARNING("      ⏭️  Rappel déjà envoyé récemment"))
            else:
                self.stdout.write(self.style.WARNING("      [SIMULATION] Rappel à envoyer"))
                stats['rappels_envoyes'] += 1

        # Afficher le résumé
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ DES RAPPELS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f"  📦 Total de BC en retard: {stats['total']}")
        self.stdout.write(f"  ⚠️  Retards légers (< 15j): {stats['retard_leger']}")
        self.stdout.write(f"  🔶 Retards moyens (15-30j): {stats['retard_moyen']}")
        self.stdout.write(f"  🚨 Retards importants (> 30j): {stats['retard_important']}")

        if not dry_run:
            self.stdout.write(f"  📧 Rappels envoyés: {stats['rappels_envoyes']}")
        else:
            self.stdout.write(self.style.WARNING(f"  🔍 Rappels à envoyer: {stats['rappels_envoyes']}"))

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Envoi des rappels terminé!'))
        else:
            self.stdout.write(self.style.WARNING('✅ Simulation terminée!'))

    def _doit_envoyer_rappel(self, bc, jours_retard, relance):
        """
        Détermine si un rappel doit être envoyé.

        Args:
            bc: Le bon de commande
            jours_retard: Nombre de jours de retard
            relance: Si True, envoie aussi des rappels de relance

        Returns:
            bool: True si un rappel doit être envoyé
        """
        # Premier rappel toujours envoyé si en retard
        if not hasattr(bc, 'date_dernier_rappel') or bc.date_dernier_rappel is None:
            return True

        # Si relance activée, envoyer tous les 7 jours
        if relance:
            jours_depuis_dernier_rappel = (timezone.now().date() - bc.date_dernier_rappel).days
            return jours_depuis_dernier_rappel >= 7

        # Sinon, envoyer seulement le premier rappel
        return False

    def _envoyer_rappel_commande(self, bc, jours_retard, niveau_alerte):
        """
        Envoie un rappel pour un bon de commande en retard.

        Args:
            bc: Le bon de commande
            jours_retard: Nombre de jours de retard
            niveau_alerte: Niveau d'alerte ('leger', 'moyen', 'important')
        """
        # Déterminer les destinataires
        destinataires = [bc.acheteur]

        # Si retard important, notifier aussi le manager
        if niveau_alerte == 'important' and bc.demande_achat:
            if bc.demande_achat.validateur_n2:
                destinataires.append(bc.demande_achat.validateur_n2)

        # Envoyer la notification
        NotificationService.notifier_commande_en_retard(
            bon_commande=bc,
            jours_retard=jours_retard,
            niveau_alerte=niveau_alerte,
            destinataires=destinataires
        )

    def _afficher_statistiques_fournisseurs(self):
        """Affiche des statistiques sur les retards par fournisseur."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📊 STATISTIQUES PAR FOURNISSEUR'))
        self.stdout.write('='*70)

        # Récupérer les fournisseurs avec le plus de retards
        from django.db.models import Count, Avg

        fournisseurs_retards = GACBonCommande.objects.filter(
            statut__in=[STATUT_BC_ENVOYE, STATUT_BC_CONFIRME, STATUT_BC_RECU_PARTIEL],
            date_livraison_confirmee__lt=timezone.now().date()
        ).values(
            'fournisseur__raison_sociale'
        ).annotate(
            nb_retards=Count('id')
        ).order_by('-nb_retards')[:10]

        for item in fournisseurs_retards:
            self.stdout.write(
                f"  {item['fournisseur__raison_sociale']}: {item['nb_retards']} BC en retard"
            )

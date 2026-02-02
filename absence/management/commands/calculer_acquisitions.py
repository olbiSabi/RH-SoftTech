# absence/management/commands/calculer_acquisitions.py
"""
Commande Django pour calculer automatiquement les acquisitions de congés.

Usage:
    python manage.py calculer_acquisitions
    python manage.py calculer_acquisitions --annee 2026
    python manage.py calculer_acquisitions --mois-en-cours
    python manage.py calculer_acquisitions --tous
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from absence.services.acquisition_service import AcquisitionService
from employee.models import ZY00

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calcule automatiquement les acquisitions de congés pour les employés actifs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--annee',
            type=int,
            default=None,
            help="Année de référence (par défaut: année en cours)"
        )
        parser.add_argument(
            '--mois-en-cours',
            action='store_true',
            help='Calculer uniquement pour le mois en cours'
        )
        parser.add_argument(
            '--tous',
            action='store_true',
            help='Recalculer pour tous les employés (même ceux déjà calculés)'
        )
        parser.add_argument(
            '--employe',
            type=str,
            help='Matricule d\'un employé spécifique'
        )
        parser.add_argument(
            '--verbeux',
            action='store_true',
            help='Afficher plus de détails'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans sauvegarder les changements'
        )

    def handle(self, *args, **options):
        debut = timezone.now()
        annee = options.get('annee') or timezone.now().year
        mois_en_cours = options.get('mois_en_cours')
        tous = options.get('tous')
        matricule_employe = options.get('employe')
        verbeux = options.get('verbeux')
        dry_run = options.get('dry_run')

        self.stdout.write(self.style.WARNING(f"\n{'='*80}"))
        self.stdout.write(self.style.WARNING(
            f"📊 CALCUL DES ACQUISITIONS DE CONGÉS - {debut.strftime('%d/%m/%Y %H:%M:%S')}"
        ))
        self.stdout.write(self.style.WARNING(f"{'='*80}\n"))

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODE SIMULATION - Aucune modification ne sera enregistrée\n"))

        # Déterminer les employés à traiter
        if matricule_employe:
            try:
                employes = [ZY00.objects.get(matricule=matricule_employe)]
                self.stdout.write(self.style.HTTP_INFO(
                    f"🎯 Calcul pour l'employé: {employes[0].nom} {employes[0].prenoms}\n"
                ))
            except ZY00.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Employé {matricule_employe} non trouvé"))
                return
        else:
            employes = ZY00.objects.filter(etat='actif')
            self.stdout.write(self.style.HTTP_INFO(
                f"👥 Calcul pour {employes.count()} employé(s) actif(s)\n"
            ))

        # Informations sur le calcul
        self.stdout.write(f"📅 Année de référence: {annee}")
        if mois_en_cours:
            mois_actuel = timezone.now().month
            self.stdout.write(f"📆 Mois en cours: {mois_actuel}")
        self.stdout.write(f"")

        # Calcul des acquisitions
        self.stdout.write(self.style.HTTP_INFO("🔄 Calcul en cours...\n"))

        try:
            if dry_run:
                # Simulation
                resultats = self._simuler_calcul(employes, annee, verbeux)
            else:
                # Calcul réel
                resultats = AcquisitionService.calculer_acquisitions_employes(
                    annee=annee,
                    employes=employes
                )

            # Affichage des résultats
            self._afficher_resultats(resultats, verbeux)

            # Résumé final
            fin = timezone.now()
            duree = (fin - debut).total_seconds()

            self.stdout.write(self.style.WARNING(f"\n{'='*80}"))
            self.stdout.write(self.style.WARNING("📊 RÉSUMÉ"))
            self.stdout.write(self.style.WARNING(f"{'='*80}"))

            total_traite = resultats['total']
            total_erreurs = len(resultats.get('erreurs', []))

            self.stdout.write(f"✅ Traitements réussis: {total_traite}")
            if total_erreurs > 0:
                self.stdout.write(self.style.WARNING(f"⚠️  Erreurs: {total_erreurs}"))

            self.stdout.write(f"\n⏱️  Durée: {duree:.2f} secondes")
            self.stdout.write(self.style.WARNING(f"{'='*80}\n"))

            if not dry_run:
                logger.info(
                    f"Calcul des acquisitions terminé: {total_traite} succès, "
                    f"{total_erreurs} erreurs en {duree:.2f}s"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Erreur lors du calcul: {str(e)}"))
            logger.exception("Erreur lors du calcul des acquisitions")
            raise

    def _simuler_calcul(self, employes, annee, verbeux):
        """Simule le calcul sans sauvegarder."""
        from decimal import Decimal

        resultats = {
            'succes': [],
            'erreurs': [],
            'total': 0
        }

        for employe in employes:
            try:
                # Simuler le calcul
                resultat = AcquisitionService.calculer_jours_acquis_au(
                    employe,
                    annee,
                    timezone.now().date()
                )

                jours_acquis = resultat.get('jours_acquis', Decimal('0.00'))

                resultats['succes'].append({
                    'employe': f"{employe.nom} {employe.prenoms}",
                    'jours_acquis': str(jours_acquis),
                    'created': False
                })

                if verbeux:
                    self.stdout.write(
                        f"  ✓ {employe.matricule} - {employe.nom}: {jours_acquis} jours"
                    )

            except Exception as e:
                resultats['erreurs'].append({
                    'employe': f"{employe.nom} {employe.prenoms}",
                    'erreur': str(e)
                })

                if verbeux:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ {employe.matricule} - {employe.nom}: {str(e)}")
                    )

        resultats['total'] = len(resultats['succes'])
        return resultats

    def _afficher_resultats(self, resultats, verbeux):
        """Affiche les résultats du calcul."""
        if verbeux and resultats['succes']:
            self.stdout.write("\n📋 DÉTAILS DES CALCULS :\n")
            for item in resultats['succes']:
                status = "🆕" if item.get('created') else "🔄"
                self.stdout.write(
                    f"  {status} {item['employe']}: {item['jours_acquis']} jours acquis"
                )

        if resultats.get('erreurs'):
            self.stdout.write(self.style.WARNING("\n⚠️  ERREURS RENCONTRÉES :\n"))
            for err in resultats['erreurs']:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ {err['employe']}: {err['erreur']}")
                )

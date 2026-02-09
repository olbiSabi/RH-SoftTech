# absence/management/commands/calculer_acquisitions.py
"""
Commande Django pour calculer automatiquement les acquisitions de congés.

Usage:
    python manage.py calculer_acquisitions
    python manage.py calculer_acquisitions --annee 2026
    python manage.py calculer_acquisitions --employe MT000045
    python manage.py calculer_acquisitions --tous --verbeux
    python manage.py calculer_acquisitions --dry-run --verbeux
"""
import logging
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from absence.models import AcquisitionConges
from absence.utils import calculer_jours_acquis_au
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
        tous = options.get('tous')
        matricule_employe = options.get('employe')
        verbeux = options.get('verbeux')
        dry_run = options.get('dry_run')
        date_reference = timezone.now().date()

        self._log_header(debut, annee, dry_run)

        # Déterminer les employés à traiter
        employes = self._get_employes(matricule_employe)
        if employes is None:
            return

        self.stdout.write(f"  Annee de reference: {annee}")
        self.stdout.write(f"  Date de reference:  {date_reference.strftime('%d/%m/%Y')}")
        self.stdout.write(f"  Employes a traiter: {len(employes)}")
        self.stdout.write(f"  Mode: {'SIMULATION' if dry_run else 'REEL'}")
        self.stdout.write(f"  Recalcul: {'Tous' if tous else 'Nouveaux uniquement'}")
        self.stdout.write("")

        # Calcul
        resultats = {
            'succes': [],
            'rejets': [],
            'erreurs': [],
            'ignores': 0,
        }

        for employe in employes:
            self._traiter_employe(
                employe, annee, date_reference,
                tous, dry_run, verbeux, resultats
            )

        # Résumé
        self._log_resume(resultats, debut, dry_run)

    def _get_employes(self, matricule):
        """Récupère la liste des employés à traiter."""
        if matricule:
            try:
                employes = [ZY00.objects.get(matricule=matricule)]
                self.stdout.write(self.style.HTTP_INFO(
                    f"  Employe cible: {employes[0].matricule} - "
                    f"{employes[0].nom} {employes[0].prenoms}"
                ))
                return employes
            except ZY00.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"  ERREUR: Employe {matricule} non trouve"
                ))
                return None

        employes = list(ZY00.objects.filter(
            etat='actif',
            entreprise__isnull=False
        ))
        return employes

    def _traiter_employe(self, employe, annee, date_reference,
                         recalculer, dry_run, verbeux, resultats):
        """Traite le calcul pour un employé individuel."""
        matricule = employe.matricule
        nom_complet = f"{employe.nom} {employe.prenoms}"

        # --- Vérification 1 : Contrat actif ---
        contrat = employe.contrats.filter(
            actif=True
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date_reference)
        ).order_by('-date_debut').first()

        if not contrat:
            raison = "Aucun contrat actif en vigueur"
            self._log_rejet(resultats, matricule, nom_complet, raison, verbeux)
            return

        # --- Vérification 2 : Convention applicable ---
        convention = employe.convention_applicable
        if not convention:
            raison = "Aucune convention applicable (ni personnalisee, ni entreprise)"
            self._log_rejet(resultats, matricule, nom_complet, raison, verbeux)
            return

        # --- Vérification 3 : Acquisition existante ---
        try:
            acquisition, created = AcquisitionConges.objects.get_or_create(
                employe=employe,
                annee_reference=annee,
                defaults={
                    'jours_acquis': Decimal('0.00'),
                    'jours_pris': Decimal('0.00'),
                    'jours_restants': Decimal('0.00'),
                    'jours_report_anterieur': Decimal('0.00'),
                    'jours_report_nouveau': Decimal('0.00'),
                }
            )
        except Exception as e:
            resultats['erreurs'].append({
                'matricule': matricule,
                'employe': nom_complet,
                'erreur': f"Erreur creation acquisition: {e}",
            })
            logger.error("ERREUR %s (%s): %s", matricule, nom_complet, e)
            return

        if not created and not recalculer:
            resultats['ignores'] += 1
            if verbeux:
                self.stdout.write(
                    f"  IGNORE {matricule} - {nom_complet}: "
                    f"acquisition existante ({acquisition.jours_acquis} jours)"
                )
            return

        # --- Calcul ---
        try:
            resultat = calculer_jours_acquis_au(employe, annee, date_reference)
        except ValueError as e:
            self._log_rejet(
                resultats, matricule, nom_complet, str(e), verbeux,
                contrat_debut=contrat.date_debut
            )
            return
        except Exception as e:
            resultats['erreurs'].append({
                'matricule': matricule,
                'employe': nom_complet,
                'erreur': str(e),
            })
            logger.error("ERREUR %s (%s): %s", matricule, nom_complet, e)
            return

        jours_acquis = resultat['jours_acquis']
        mois_travailles = resultat['mois_travailles']
        detail = resultat.get('detail', {})
        jours_restants_calc = detail.get('jours_restants', 0)

        # --- Vérification 4 : Résultat nul avec raison ---
        if jours_acquis == Decimal('0.00') and 'raison' in detail:
            self._log_rejet(
                resultats, matricule, nom_complet, detail['raison'], verbeux,
                contrat_debut=contrat.date_debut, mois=mois_travailles
            )
            return

        # --- Sauvegarde ---
        if not dry_run:
            with transaction.atomic():
                acquisition.jours_acquis = jours_acquis
                acquisition.save()

        status = "CREE" if created else "MAJ"
        resultats['succes'].append({
            'matricule': matricule,
            'employe': nom_complet,
            'jours_acquis': str(jours_acquis),
            'mois_travailles': str(mois_travailles),
            'jours_reste': jours_restants_calc,
            'contrat_debut': str(contrat.date_debut),
            'created': created,
        })

        if verbeux:
            bonus = "+0.5j" if jours_restants_calc >= 15 else ""
            self.stdout.write(self.style.SUCCESS(
                f"  {status} {matricule} - {nom_complet}: "
                f"{jours_acquis} jours "
                f"({mois_travailles} mois, reste {jours_restants_calc}j {bonus}) "
                f"[contrat: {contrat.date_debut}]"
            ))

        logger.info(
            "%s %s (%s): %s jours | mois=%s, reste=%sj, contrat=%s",
            status, matricule, nom_complet, jours_acquis,
            mois_travailles, jours_restants_calc, contrat.date_debut
        )

    def _log_rejet(self, resultats, matricule, nom_complet, raison, verbeux,
                   contrat_debut=None, mois=None):
        """Enregistre et affiche un rejet."""
        entry = {
            'matricule': matricule,
            'employe': nom_complet,
            'raison': raison,
        }
        if contrat_debut:
            entry['contrat_debut'] = str(contrat_debut)
        if mois is not None:
            entry['mois'] = str(mois)

        resultats['rejets'].append(entry)

        extra = ""
        if contrat_debut:
            extra += f" | contrat={contrat_debut}"
        if mois is not None:
            extra += f", mois={mois}"

        if verbeux:
            self.stdout.write(self.style.WARNING(
                f"  REJET {matricule} - {nom_complet}: {raison}{extra}"
            ))

        logger.warning("REJET %s (%s): %s%s", matricule, nom_complet, raison, extra)

    def _log_header(self, debut, annee, dry_run):
        """Affiche l'en-tête."""
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(
            f"  CALCUL DES ACQUISITIONS DE CONGES - "
            f"{debut.strftime('%d/%m/%Y %H:%M:%S')}"
        )
        self.stdout.write(f"{'='*70}")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "  MODE SIMULATION - Aucune modification ne sera enregistree"
            ))
        self.stdout.write("")

    def _log_resume(self, resultats, debut, dry_run):
        """Affiche le résumé final."""
        fin = timezone.now()
        duree = (fin - debut).total_seconds()

        total_succes = len(resultats['succes'])
        total_rejets = len(resultats['rejets'])
        total_erreurs = len(resultats['erreurs'])
        total_ignores = resultats['ignores']

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("  RESUME")
        self.stdout.write(f"{'='*70}")
        self.stdout.write(self.style.SUCCESS(
            f"  Calculs reussis : {total_succes}"
        ))

        if total_ignores > 0:
            self.stdout.write(f"  Ignores (deja calcules) : {total_ignores}")

        if total_rejets > 0:
            self.stdout.write(self.style.WARNING(
                f"  Rejets : {total_rejets}"
            ))
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("  DETAIL DES REJETS :"))
            for rej in resultats['rejets']:
                extra = ""
                if 'contrat_debut' in rej:
                    extra += f" | contrat={rej['contrat_debut']}"
                if 'mois' in rej:
                    extra += f", mois={rej['mois']}"
                self.stdout.write(self.style.WARNING(
                    f"    - {rej['matricule']} {rej['employe']}: "
                    f"{rej['raison']}{extra}"
                ))

        if total_erreurs > 0:
            self.stdout.write(self.style.ERROR(
                f"  Erreurs : {total_erreurs}"
            ))
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("  DETAIL DES ERREURS :"))
            for err in resultats['erreurs']:
                self.stdout.write(self.style.ERROR(
                    f"    - {err['matricule']} {err['employe']}: "
                    f"{err['erreur']}"
                ))

        self.stdout.write(f"\n  Duree: {duree:.2f} secondes")
        self.stdout.write(f"{'='*70}\n")

        logger.info(
            "Calcul termine: %s succes, %s rejets, %s erreurs, "
            "%s ignores en %.2fs",
            total_succes, total_rejets, total_erreurs, total_ignores, duree
        )

# absence/management/commands/verifier_acquisitions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from absence.models import AcquisitionConges
from absence.views import calculer_jours_acquis
from decimal import Decimal


class Command(BaseCommand):
    help = 'Vérifie si les acquisitions sont à jour'

    def add_arguments(self, parser):
        parser.add_argument(
            '--annee',
            type=int,
            default=timezone.now().year,
            help='Année à vérifier'
        )
        parser.add_argument(
            '--recalculer',
            action='store_true',
            help='Recalculer automatiquement si différence'
        )

    def handle(self, *args, **options):
        annee = options['annee']
        recalculer = options['recalculer']

        self.stdout.write(f"\n🔍 Vérification des acquisitions pour {annee}\n")
        self.stdout.write("=" * 80)

        acquisitions = AcquisitionConges.objects.filter(
            annee_reference=annee
        ).select_related('employe')

        total = 0
        a_jour = 0
        obsoletes = []
        erreurs = []

        for acq in acquisitions:
            total += 1

            try:
                # Recalculer
                jours_calcules = calculer_jours_acquis(acq.employe, annee)

                # Comparer avec tolérance de 0.01
                diff = abs(jours_calcules - acq.jours_acquis)

                if diff < Decimal('0.01'):
                    a_jour += 1
                    status = "✅"
                else:
                    obsoletes.append({
                        'employe': str(acq.employe),
                        'stocke': acq.jours_acquis,
                        'calcule': jours_calcules,
                        'diff': diff,
                        'date_maj': acq.date_maj
                    })
                    status = "⚠️ "

                    # Recalculer si demandé
                    if recalculer:
                        acq.jours_acquis = jours_calcules
                        acq.save()
                        status = "🔄"

                self.stdout.write(
                    f"{status} {acq.employe.matricule} - {acq.employe.nom}: "
                    f"{acq.jours_acquis}j (calculé: {jours_calcules}j)"
                )

            except Exception as e:
                erreurs.append({
                    'employe': str(acq.employe),
                    'erreur': str(e)
                })
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ {acq.employe.matricule} - {acq.employe.nom}: ERREUR - {str(e)}"
                    )
                )

        # Résumé
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(f"\n📊 RÉSUMÉ\n")
        self.stdout.write(f"Total acquisitions : {total}")
        self.stdout.write(f"✅ À jour : {a_jour} ({a_jour / total * 100:.1f}%)" if total > 0 else "Aucune acquisition")
        self.stdout.write(f"⚠️  Obsolètes : {len(obsoletes)}")
        self.stdout.write(f"❌ Erreurs : {len(erreurs)}")

        # Détails obsolètes
        if obsoletes:
            self.stdout.write(f"\n⚠️  ACQUISITIONS OBSOLÈTES :\n")
            for obs in obsoletes:
                self.stdout.write(
                    f"  • {obs['employe']}: {obs['stocke']}j → {obs['calcule']}j "
                    f"(diff: {obs['diff']}j, MAJ: {obs['date_maj'].strftime('%d/%m/%Y %H:%M')})"
                )

        # Détails erreurs
        if erreurs:
            self.stdout.write(f"\n❌ ERREURS :\n")
            for err in erreurs:
                self.stdout.write(f"  • {err['employe']}: {err['erreur']}")

        if recalculer and obsoletes:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ {len(obsoletes)} acquisitions recalculées")
            )
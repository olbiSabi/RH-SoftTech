# employee/management/commands/check_contrats_expires.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from employee.models import ZY00, ZYCO


class Command(BaseCommand):
    help = 'Désactive automatiquement les employés dont le contrat a expiré'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les employés qui seraient désactivés sans les modifier',
        )

    def handle(self, *args, **options):
        date_actuelle = timezone.now().date()
        dry_run = options['dry_run']

        # Récupérer les contrats expirés
        contrats_expires = ZYCO.objects.filter(
            date_fin__lt=date_actuelle,
            actif=True,
            employe__etat='actif'
        ).select_related('employe')

        total = contrats_expires.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucun contrat expiré trouvé'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 MODE DRY-RUN : {total} contrat(s) expiré(s) trouvé(s)'))

        desactives = 0

        for contrat in contrats_expires:
            employe = contrat.employe

            self.stdout.write(
                f"⚠️  Contrat expiré : {employe.matricule} - {employe.nom} {employe.prenoms} "
                f"(Fin: {contrat.date_fin.strftime('%d/%m/%Y')})"
            )

            if not dry_run:
                # Désactiver l'employé
                employe.etat = 'inactif'
                employe.save(update_fields=['etat'])

                # Désactiver le contrat
                contrat.actif = False
                contrat.save(update_fields=['actif'])

                desactives += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'🔍 DRY-RUN : {total} employé(s) seraient désactivé(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {desactives} employé(s) désactivé(s) pour cause de contrat expiré'
                )
            )
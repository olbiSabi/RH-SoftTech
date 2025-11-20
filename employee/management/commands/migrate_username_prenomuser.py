# management/commands/migrate_username_prenomuser.py
from django.core.management.base import BaseCommand
from employee.models import ZY00, ZYNP


class Command(BaseCommand):
    help = 'Migre les champs username et prenomuser pour les employés existants'

    def handle(self, *args, **options):
        for employe in ZY00.objects.all():
            # Vérifier s'il y a un historique actif
            historique_actif = ZYNP.objects.filter(
                employe=employe,
                actif=True,
                date_fin_validite__isnull=True
            ).first()

            if historique_actif:
                # Utiliser les valeurs de l'historique actif
                employe.username = historique_actif.nom
                employe.prenomuser = historique_actif.prenoms
            else:
                # Utiliser les valeurs originales
                employe.username = employe.nom
                employe.prenomuser = employe.prenoms

            employe.save()
            self.stdout.write(
                self.style.SUCCESS(f'Migré {employe.matricule}: {employe.username} {employe.prenomuser}')
            )
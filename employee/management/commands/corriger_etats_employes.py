# management/commands/corriger_etats.py
from django.core.management.base import BaseCommand
from employee.models import ZY00
from django.db import transaction


class Command(BaseCommand):
    help = 'Corrige les états des employés basés sur leurs contrats'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Correction des états des employés...')

        avec_transaction = options.get('transaction', True)

        if avec_transaction:
            with transaction.atomic():
                self.corriger_etats()
        else:
            self.corriger_etats()

    def corriger_etats(self):
        corriges = 0
        total = ZY00.objects.count()

        for employe in ZY00.objects.all():
            if employe.synchroniser_etat():
                corriges += 1
                self.stdout.write(f'✅ {employe.matricule}: {employe.nom} {employe.prenoms}')

        self.stdout.write(self.style.SUCCESS(
            f'🎯 {corriges}/{total} employés corrigés'
        ))
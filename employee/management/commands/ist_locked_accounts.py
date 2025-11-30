# employee/management/commands/list_locked_accounts.py
from django.core.management.base import BaseCommand
from employee.models import UserSecurity
from django.utils import timezone


class Command(BaseCommand):
    help = 'Lister tous les comptes actuellement bloqués'

    def handle(self, *args, **options):
        locked_accounts = UserSecurity.objects.filter(is_locked=True)

        if not locked_accounts:
            self.stdout.write(self.style.SUCCESS('Aucun compte bloqué trouvé'))
            return

        self.stdout.write(self.style.WARNING('📋 Comptes bloqués:'))
        for security in locked_accounts:
            status = "🔴 BLOQUÉ"
            if security.locked_until:
                if timezone.now() < security.locked_until:
                    status = f"🔴 BLOQUÉ (jusqu'à {security.locked_until.strftime('%d/%m/%Y %H:%M')})"
                else:
                    status = "🟡 BLOQUÉ (expiré, devrait être débloqué)"

            self.stdout.write(
                f"• {security.user.username} - {security.user.email} - {status}"
            )
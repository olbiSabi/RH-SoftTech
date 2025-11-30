# management/commands/unlock_accounts.py
from django.core.management.base import BaseCommand
from employee.models import UserSecurity
from django.utils import timezone


class Command(BaseCommand):
    help = 'Débloquer les comptes utilisateurs après la période de blocage'

    def handle(self, *args, **options):
        locked_accounts = UserSecurity.objects.filter(is_locked=True)

        for security in locked_accounts:
            if security.locked_until and timezone.now() >= security.locked_until:
                security.reset_attempts()
                self.stdout.write(
                    self.style.SUCCESS(f'Compte {security.user.username} débloqué')
                )
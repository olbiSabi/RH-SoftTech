"""
Commande de gestion Django pour assigner des rôles GAC aux employés.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from employee.models import ZY00, ZYRO


class Command(BaseCommand):
    help = 'Assigne un rôle GAC à un employé'

    def add_arguments(self, parser):
        parser.add_argument(
            'matricule',
            type=str,
            help='Matricule de l\'employé'
        )
        parser.add_argument(
            'role_code',
            type=str,
            help='Code du rôle GAC (ADMIN_GAC, ACHETEUR, RECEPTIONNAIRE, GESTIONNAIRE_BUDGET)'
        )

    def handle(self, *args, **options):
        matricule = options['matricule']
        role_code = options['role_code']

        # Vérifier si l'employé existe
        try:
            employe = ZY00.objects.get(matricule=matricule)
            self.stdout.write(f"Employé trouvé: {employe.nom} {employe.prenoms}")
        except ZY00.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Employé avec matricule {matricule} introuvable"))
            return

        # Vérifier si le rôle existe, sinon le créer
        role, created = ZYRO.objects.get_or_create(
            CODE=role_code,
            defaults={
                'LIBELLE': role_code,
                'DESCRIPTION': f'Rôle {role_code} pour le module GAC',
                'actif': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Rôle {role_code} créé"))
        else:
            self.stdout.write(f"✓ Rôle {role_code} trouvé")

        # Vérifier si l'employé a déjà ce rôle
        if employe.has_role(role_code):
            self.stdout.write(self.style.WARNING(f"⚠ L'employé a déjà le rôle {role_code}"))
        else:
            # Assigner le rôle en utilisant la méthode add_role
            try:
                employe.add_role(role_code, date_debut=timezone.now().date())
                self.stdout.write(self.style.SUCCESS(f"✓ Rôle {role_code} assigné à {employe.nom} {employe.prenoms}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Erreur lors de l'assignation: {e}"))
                return

        # Afficher tous les rôles de l'employé
        roles = employe.get_roles()
        if roles:
            self.stdout.write(f"\n📋 Rôles actuels de {employe.nom} {employe.prenoms}:")
            for r in roles:
                self.stdout.write(f"  • {r.CODE}: {r.LIBELLE}")
        else:
            self.stdout.write(self.style.WARNING("⚠ L'employé n'a aucun rôle"))

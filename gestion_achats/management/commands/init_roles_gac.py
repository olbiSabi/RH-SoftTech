"""
Management command pour initialiser les rôles du module GAC.

Usage:
    python manage.py init_roles_gac
"""

from django.core.management.base import BaseCommand
from employee.models import ZYRO


class Command(BaseCommand):
    help = 'Initialise les rôles du module Gestion des Achats & Commandes (GAC)'

    def handle(self, *args, **options):
        """Exécute la commande d'initialisation des rôles."""

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Initialisation des rôles GAC'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        # Définition des rôles
        roles = [
            {
                'CODE': 'DEMANDEUR',
                'LIBELLE': 'Demandeur',
                'DESCRIPTION': 'Tout employé pouvant créer une demande d\'achat'
            },
            {
                'CODE': 'VALIDATEUR_N1',
                'LIBELLE': 'Validateur niveau 1',
                'DESCRIPTION': 'Manager validant les demandes de son équipe'
            },
            {
                'CODE': 'VALIDATEUR_N2',
                'LIBELLE': 'Validateur niveau 2',
                'DESCRIPTION': 'Direction ou responsable achats validant les demandes importantes'
            },
            {
                'CODE': 'ACHETEUR',
                'LIBELLE': 'Acheteur',
                'DESCRIPTION': 'Personne en charge de créer et gérer les bons de commande'
            },
            {
                'CODE': 'RECEPTIONNAIRE',
                'LIBELLE': 'Réceptionnaire',
                'DESCRIPTION': 'Personne habilitée à réceptionner les marchandises'
            },
            {
                'CODE': 'GESTIONNAIRE_BUDGET',
                'LIBELLE': 'Gestionnaire de budget',
                'DESCRIPTION': 'Personne gérant les enveloppes budgétaires'
            },
            {
                'CODE': 'ADMIN_GAC',
                'LIBELLE': 'Administrateur GAC',
                'DESCRIPTION': 'Administrateur complet du module Gestion des Achats & Commandes'
            },
        ]

        created_count = 0
        updated_count = 0

        for role_data in roles:
            role, created = ZYRO.objects.update_or_create(
                CODE=role_data['CODE'],
                defaults={
                    'LIBELLE': role_data['LIBELLE'],
                    'DESCRIPTION': role_data['DESCRIPTION']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Rôle créé: {role.CODE:20s} - {role.LIBELLE}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Rôle mis à jour: {role.CODE:20s} - {role.LIBELLE}"
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('Résumé:'))
        self.stdout.write(self.style.SUCCESS(f"  - Rôles créés: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Rôles mis à jour: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Total: {created_count + updated_count}"))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')

        # Afficher la hiérarchie
        self.stdout.write(self.style.SUCCESS('Hiérarchie des rôles:'))
        self.stdout.write('')
        self.stdout.write('  ADMIN_GAC (tous les droits)')
        self.stdout.write('    │')
        self.stdout.write('    ├── GESTIONNAIRE_BUDGET (gestion budgets)')
        self.stdout.write('    │')
        self.stdout.write('    ├── ACHETEUR (gestion BCs + validation N2)')
        self.stdout.write('    │   │')
        self.stdout.write('    │   └── VALIDATEUR_N2 (validation niveau 2)')
        self.stdout.write('    │       │')
        self.stdout.write('    │       └── VALIDATEUR_N1 (validation niveau 1)')
        self.stdout.write('    │           │')
        self.stdout.write('    │           └── RECEPTIONNAIRE (réceptions)')
        self.stdout.write('    │               │')
        self.stdout.write('    │               └── DEMANDEUR (création demandes)')
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée avec succès!'))
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Note: Les rôles doivent maintenant être attribués aux employés '
                'via la gestion des rôles.'
            )
        )

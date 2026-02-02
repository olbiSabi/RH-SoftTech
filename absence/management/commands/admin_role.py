"""
Management command pour initialiser les rôles de l'application HR_ONIAN.

Usage:
    python manage.py admin_role
"""

from django.core.management.base import BaseCommand
from employee.models import ZYRO


class Command(BaseCommand):
    help = 'Initialise les rôles de l\'application HR_ONIAN (Absences, RH, Gestion Temps, Matériel, Frais)'

    def handle(self, *args, **options):
        """Exécute la commande d'initialisation des rôles."""

        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Initialisation des rôles HR_ONIAN'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write('')

        # Définition des rôles
        roles = [
            {
                'CODE': 'GESTION_APP',
                'LIBELLE': 'Gestionnaire Application',
                'DESCRIPTION': 'Accès complet au paramétrage de l\'application (absences, entreprise, types d\'absence, jours fériés, conventions, temps et activités)',
                'PERMISSIONS_CUSTOM': {
                    # Absences
                    'can_manage_absence_settings': True,
                    'can_manage_entreprise_settings': True,
                    'can_manage_types_absence': True,
                    'can_manage_jours_feries': True,
                    'can_manage_conventions': True,
                    'can_manage_acquisitions': True,
                    'full_absence_access': True,
                    'full_entreprise_access': True,
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_view_all_absences': True,
                    'can_manage_employees': True,
                    # Gestion Temps et Activités - ACCÈS COMPLET
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                    # Module Matériel - ACCÈS COMPLET
                    'can_manage_materiel': True,
                    'can_affecter_materiel': True,
                    'can_manage_maintenances': True,
                    'can_manage_categories_materiel': True,
                    'can_manage_fournisseurs': True,
                }
            },
            {
                'CODE': 'RH_VALIDATION_ABS',
                'LIBELLE': 'RH - Validation absences',
                'DESCRIPTION': 'Validation finale des absences au niveau RH',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_rh': True,
                    'can_view_all_absences': True,
                    'absence.valider_absence_rh': True,
                }
            },
            {
                'CODE': 'MANAGER_ABS',
                'LIBELLE': 'Manager - Validation absences',
                'DESCRIPTION': 'Validation des absences de ses subordonnés (niveau 1)',
                'PERMISSIONS_CUSTOM': {
                    'can_validate_manager': True,
                    'can_view_team_absences': True,
                }
            },
            {
                'CODE': 'EMPLOYE_STD',
                'LIBELLE': 'Employé standard',
                'DESCRIPTION': 'Peut déclarer et voir ses propres absences et imputations',
                'PERMISSIONS_CUSTOM': {
                    'can_create_absence': True,
                    'can_view_own_absences': True,
                    # Gestion Temps et Activités - Employé standard
                    'can_create_imputation': True,
                    'can_view_own_imputations': True,
                }
            },
            {
                'CODE': 'DRH',
                'LIBELLE': 'Direction des Ressources Humaines',
                'DESCRIPTION': 'Accès complet à la gestion RH, validation finale des demandes d\'absence et accès total à la gestion des temps',
                'PERMISSIONS_CUSTOM': {
                    # Absences
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_manage_employees': True,
                    'can_view_all_absences': True,
                    'can_manage_roles': True,
                    'can_view_payroll': True,
                    'absence.valider_absence_rh': True,
                    # Gestion Temps et Activités - ACCÈS COMPLET
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                    # Module Matériel - ACCÈS COMPLET
                    'can_manage_materiel': True,
                    'can_affecter_materiel': True,
                    'can_manage_maintenances': True,
                    'can_manage_categories_materiel': True,
                    'can_manage_fournisseurs': True,
                }
            },
            {
                'CODE': 'MANAGER',
                'LIBELLE': 'Manager de département',
                'DESCRIPTION': 'Validation des demandes d\'absence de son équipe et validation des imputations de temps',
                'PERMISSIONS_CUSTOM': {
                    # Absences
                    'can_validate_manager': True,
                    'can_view_team_absences': True,
                    'can_manage_team': True,
                    # Gestion Temps et Activités - Manager
                    'can_validate_imputations': True,
                    'can_view_team_imputations': True,
                    'can_manage_projets': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'COMPTABLE',
                'LIBELLE': 'Comptable',
                'DESCRIPTION': 'Accès à la comptabilité, à la paie et aux imputations facturables',
                'PERMISSIONS_CUSTOM': {
                    'can_view_payroll': True,
                    'can_manage_contracts': True,
                    'can_view_reports': True,
                    # Gestion Temps et Activités - Comptable
                    'can_view_all_imputations': True,
                    'can_view_facturables': True,
                }
            },
            {
                'CODE': 'DIRECTEUR',
                'LIBELLE': 'Directeur / Président',
                'DESCRIPTION': 'Accès complet à toutes les fonctionnalités',
                'PERMISSIONS_CUSTOM': {
                    # Absences
                    'can_validate_rh': True,
                    'can_validate_manager': True,
                    'can_manage_employees': True,
                    'can_view_all_absences': True,
                    'can_manage_roles': True,
                    'can_view_payroll': True,
                    'can_view_dashboard': True,
                    'can_manage_company': True,
                    # Gestion Temps et Activités - ACCÈS COMPLET
                    'can_view_all_imputations': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_manage_activites': True,
                    'can_manage_taches': True,
                    'can_view_all_projets': True,
                }
            },
            {
                'CODE': 'ASSISTANT_RH',
                'LIBELLE': 'Assistant RH',
                'DESCRIPTION': 'Accès en lecture à la gestion RH et aux imputations',
                'PERMISSIONS_CUSTOM': {
                    'can_view_all_absences': True,
                    'can_view_employees': True,
                    # Gestion Temps et Activités - Lecture seule
                    'can_view_all_imputations': True,
                    # Module Matériel - Affectation uniquement
                    'can_affecter_materiel': True,
                    'can_view_materiel': True,
                }
            },
            {
                'CODE': 'RESP_ADMIN',
                'LIBELLE': 'Responsable Administratif',
                'DESCRIPTION': 'Responsable de la gestion administrative incluant le matériel et les fournitures',
                'PERMISSIONS_CUSTOM': {
                    'can_view_employees': True,
                    # Module Matériel - ACCÈS COMPLET
                    'can_manage_materiel': True,
                    'can_affecter_materiel': True,
                    'can_manage_maintenances': True,
                    'can_manage_categories_materiel': True,
                    'can_manage_fournisseurs': True,
                }
            },
            {
                'CODE': 'DAF',
                'LIBELLE': 'Directeur Administratif et Financier',
                'DESCRIPTION': 'Accès complet à la gestion financière, comptable et administrative',
                'PERMISSIONS_CUSTOM': {
                    # Absences - Accès financier
                    'can_view_all_absences': True,
                    'can_view_payroll': True,
                    'can_view_reports': True,
                    # Gestion Temps et Activités - Accès complet pour facturation
                    'can_view_all_imputations': True,
                    'can_view_facturables': True,
                    'can_validate_imputations': True,
                    'can_manage_projets': True,
                    'can_manage_clients': True,
                    'can_view_all_projets': True,
                    # Permissions financières spécifiques
                    'can_manage_contracts': True,
                    'can_view_financial_reports': True,
                    'can_validate_timesheets': True,
                    # Module Notes de Frais - Accès complet DAF
                    'can_validate_frais': True,
                    'can_approve_avances': True,
                    'can_manage_frais_categories': True,
                    'can_view_frais_statistics': True,
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for role_data in roles:
            role, created = ZYRO.objects.update_or_create(
                CODE=role_data['CODE'],
                defaults={
                    'LIBELLE': role_data['LIBELLE'],
                    'DESCRIPTION': role_data['DESCRIPTION'],
                    'PERMISSIONS_CUSTOM': role_data.get('PERMISSIONS_CUSTOM', {}),
                    'actif': True
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
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Résumé:'))
        self.stdout.write(self.style.SUCCESS(f"  - Rôles créés: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Rôles mis à jour: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Total: {created_count + updated_count}"))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write('')

        # Afficher les modules couverts
        self.stdout.write(self.style.SUCCESS('Modules couverts par ces rôles:'))
        self.stdout.write('')
        self.stdout.write('  📋 Absences et Congés')
        self.stdout.write('    └── Gestion des types d\'absence, acquisitions, validations')
        self.stdout.write('')
        self.stdout.write('  👥 Ressources Humaines')
        self.stdout.write('    └── Gestion employés, contrats, paie')
        self.stdout.write('')
        self.stdout.write('  ⏱️  Gestion Temps et Activités')
        self.stdout.write('    └── Imputations, projets, clients, activités, tâches')
        self.stdout.write('')
        self.stdout.write('  💻 Parc Matériel')
        self.stdout.write('    └── Gestion matériel, affectations, maintenances')
        self.stdout.write('')
        self.stdout.write('  💰 Notes de Frais')
        self.stdout.write('    └── Validation, catégories, avances, statistiques')
        self.stdout.write('')

        # Afficher la hiérarchie des rôles
        self.stdout.write(self.style.SUCCESS('Hiérarchie des rôles:'))
        self.stdout.write('')
        self.stdout.write('  DIRECTEUR / GESTION_APP (accès complet)')
        self.stdout.write('    │')
        self.stdout.write('    ├── DAF (financier + frais)')
        self.stdout.write('    │   └── COMPTABLE (paie + facturation)')
        self.stdout.write('    │')
        self.stdout.write('    ├── DRH (RH complet)')
        self.stdout.write('    │   ├── RH_VALIDATION_ABS (validation absences)')
        self.stdout.write('    │   └── ASSISTANT_RH (lecture RH)')
        self.stdout.write('    │')
        self.stdout.write('    ├── RESP_ADMIN (gestion administrative + matériel)')
        self.stdout.write('    │')
        self.stdout.write('    └── MANAGER (validation équipe)')
        self.stdout.write('        ├── MANAGER_ABS (validation absences uniquement)')
        self.stdout.write('        └── EMPLOYE_STD (accès standard)')
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée avec succès!'))
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Note: Les rôles doivent maintenant être attribués aux employés '
                'via la gestion des rôles ou via le shell Django.'
            )
        )
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Pour attribuer un rôle manuellement, utilisez:'
            )
        )
        self.stdout.write('  python manage.py shell')
        self.stdout.write('  >>> from employee.models import ZY00, ZYRO, ZYRE')
        self.stdout.write('  >>> from datetime import date')
        self.stdout.write('  >>> employe = ZY00.objects.get(MATRICULE="XXX")')
        self.stdout.write('  >>> role = ZYRO.objects.get(CODE="DRH")')
        self.stdout.write('  >>> ZYRE.objects.create(employe=employe, role=role, date_debut=date.today(), actif=True)')
        self.stdout.write('')

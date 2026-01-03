# employee/management/commands/import_employees.py
import pandas as pd
import datetime
import os
import uuid
import traceback
from typing import Dict, List, Optional, Any, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Importe les données des employés depuis un fichier Excel avec rapport détaillé'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialisation des attributs
        self.employee_cache = {}
        self.post_cache = {}
        self.entreprise_cache = {}
        self.departement_cache = {}
        self.role_cache = {}

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='salaires_template.xlsx',
            help='Chemin du fichier Excel à importer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'importation sans écrire en base'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            help='Importe uniquement une feuille spécifique'
        )
        parser.add_argument(
            '--ignore-missing',
            action='store_true',
            help='Ignore les références manquantes vers les employés'
        )
        parser.add_argument(
            '--skip-validation',
            action='store_true',
            help='Saute la validation des données'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force l\'importation même en cas d\'erreurs'
        )
        parser.add_argument(
            '--show-data',
            action='store_true',
            default=True,
            help='Affiche les données qui seraient intégrées'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche tous les détails'
        )
        parser.add_argument(
            '--create-users',
            action='store_true',
            default=True,
            help='Crée les utilisateurs Django associés'
        )
        parser.add_argument(
            '--report-file',
            type=str,
            help='Nom du fichier de rapport (sans extension)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limite le nombre de lignes à traiter par feuille'
        )

    def handle(self, *args, **options):
        """Gestion principale de la commande"""
        self.file_path = options['file']
        self.dry_run = options['dry_run']
        self.specific_sheet = options['sheet']
        self.ignore_missing = options['ignore_missing']
        self.skip_validation = options['skip_validation']
        self.force = options['force']
        self.show_data = options['show_data']
        self.verbose = options['verbose']
        self.create_users = options['create_users']
        self.report_file = options.get('report_file')
        self.limit = options.get('limit')

        # Initialisation
        self.validation_errors = []
        self.validation_warnings = []
        self.import_stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'by_model': {}
        }

        # Rapports détaillés
        self.detailed_report = {
            'summary': {
                'start_time': datetime.datetime.now(),
                'file': self.file_path,
                'mode': 'SIMULATION' if self.dry_run else 'IMPORTATION RÉELLE'
            },
            'sheet_details': {},  # Détails par feuille
            'data_to_import': [],  # Données qui seraient importées
            'import_results': [],  # Résultats de l'importation
            'validation_details': [],  # Détails de validation
            'users_created': [],
            'specific_errors': [],  # Erreurs spécifiques (chevauchements, etc.)
            'warnings': []
        }

        self.stdout.write(self.style.HTTP_INFO("=" * 80))
        self.stdout.write(self.style.HTTP_INFO("IMPORTATION DES DONNÉES EMPLOYÉS - MODE DÉTAILLÉ"))
        self.stdout.write(self.style.HTTP_INFO("=" * 80))

        try:
            # 1. Charger les données
            self.load_excel_data()

            # 2. Pré-cache des données existantes
            self.pre_cache_existing_data()

            # 3. Analyser les données (toujours fait même en mode simulation)
            self.analyze_all_data()

            # 4. Valider les données
            if not self.skip_validation:
                validation_passed = self.validate_all_data()
                if not validation_passed and not self.force:
                    self.stdout.write(self.style.ERROR("\n❌ Arrêt de l'importation due aux erreurs de validation"))
                    self.print_validation_summary()
                    self.generate_detailed_report()
                    return

            # 5. Déterminer l'ordre d'importation
            sheets_order = self.determine_import_order()

            # 6. Importation ou simulation
            with transaction.atomic():
                if self.dry_run:
                    self.stdout.write(
                        self.style.WARNING("\n🔍 MODE SIMULATION (dry-run) - Aucune donnée ne sera écrite"))
                    transaction.set_rollback(True)
                    # En mode simulation, on simule chaque feuille
                    for sheet_name in sheets_order:
                        self.simulate_sheet_import_detailed(sheet_name)
                else:
                    # Importation réelle
                    for sheet_name in sheets_order:
                        if sheet_name not in self.dataframes:
                            continue
                        try:
                            self.import_sheet_detailed(sheet_name)
                        except Exception as e:
                            self.import_stats['errors'] += 1
                            error_msg = f"Erreur sur {sheet_name}: {e}"
                            self.detailed_report['specific_errors'].append({
                                'sheet': sheet_name,
                                'error': str(e),
                                'type': 'import_error'
                            })
                            self.stdout.write(self.style.ERROR(f"  ❌ {error_msg}"))
                            if not self.force:
                                raise

                if self.dry_run:
                    self.stdout.write(self.style.WARNING("\n🔍 MODE SIMULATION - Transaction annulée"))

            # 7. Afficher les statistiques
            self.print_statistics()

            # 8. Générer le rapport détaillé
            self.generate_detailed_report()

        except FileNotFoundError:
            error_msg = f"Fichier non trouvé: {self.file_path}"
            self.detailed_report['specific_errors'].append({'error': error_msg, 'type': 'file_not_found'})
            self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))
            self.generate_detailed_report()
        except Exception as e:
            error_msg = f"Erreur inattendue: {e}"
            self.detailed_report['specific_errors'].append({'error': error_msg, 'type': 'unexpected_error'})
            self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))
            self.stdout.write(traceback.format_exc())
            self.generate_detailed_report()

    def load_excel_data(self):
        """Charge toutes les feuilles du fichier Excel"""
        try:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"Fichier non trouvé: {self.file_path}")

            excel_file = pd.ExcelFile(self.file_path)
            self.dataframes = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
                df = df.where(pd.notna(df), None)  # Remplace NaN par None
                df.columns = df.columns.str.strip()
                self.dataframes[sheet_name] = df

                # Stocker les informations de la feuille dans le rapport
                self.detailed_report['sheet_details'][sheet_name] = {
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': list(df.columns),
                    'first_rows': df.head(3).to_dict('records') if not df.empty else []
                }

                if self.verbose:
                    self.stdout.write(f"✅ {sheet_name}: {len(df)} ligne(s), {len(df.columns)} colonne(s)")

        except Exception as e:
            raise CommandError(f"Erreur lors du chargement du fichier Excel: {e}")

    def pre_cache_existing_data(self):
        """Pré-cache les données existantes pour optimiser les performances"""
        try:
            from employee.models import ZY00, ZYRO
            from departement.models import ZDPO, ZDDE
            from entreprise.models import Entreprise

            # Cache des employés existants
            employees = ZY00.objects.all()
            for emp in employees:
                self.employee_cache[emp.matricule] = emp

            # Cache des postes existants
            postes = ZDPO.objects.all()
            for poste in postes:
                self.post_cache[poste.CODE] = poste

            # Cache des départements existants
            departements = ZDDE.objects.all()
            for dept in departements:
                self.departement_cache[dept.CODE] = dept

            # Cache des entreprises existantes
            entreprises = Entreprise.objects.all()
            for entreprise in entreprises:
                self.entreprise_cache[entreprise.code.upper()] = entreprise
                self.entreprise_cache[entreprise.code] = entreprise

            # Cache des rôles existants
            roles = ZYRO.objects.filter(actif=True)
            for role in roles:
                self.role_cache[role.CODE] = role

            if self.verbose:
                self.stdout.write(f"📊 Cache initialisé: {len(self.employee_cache)} employés, "
                                  f"{len(self.post_cache)} postes, {len(self.departement_cache)} départements, "
                                  f"{len(self.entreprise_cache)} entreprises, {len(self.role_cache)} rôles")

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Erreur lors du pré-cache: {e}"))

    def analyze_all_data(self):
        """Analyse toutes les données pour le rapport"""
        self.stdout.write("\n🔍 ANALYSE DES DONNÉES")

        for sheet_name in self.determine_import_order():
            df = self.dataframes.get(sheet_name)
            if df is None or df.empty:
                continue

            self.stdout.write(f"  📄 {sheet_name}:")

            # Limiter le nombre de lignes si demandé
            if self.limit:
                df = df.head(self.limit)

            # Analyser chaque ligne
            for idx, row in df.iterrows():
                if self.limit and idx >= self.limit:
                    break

                line_num = idx + 2
                self.analyze_row(sheet_name, row, line_num)

    def analyze_row(self, sheet_name, row, line_num):
        """Analyse une ligne pour le rapport"""
        model_mapping = {
            'ZY00_Employes': ('ZY00', 'Employé'),
            'ZYNP_HistoriqueNoms': ('ZYNP', 'Historique nom/prénom'),
            'ZYCO_Contrats': ('ZYCO', 'Contrat'),
            'ZYTE_Telephones': ('ZYTE', 'Téléphone'),
            'ZYME_Emails': ('ZYME', 'Email'),
            'ZYAF_Affectations': ('ZYAF', 'Affectation'),
            'ZYAD_Adresses': ('ZYAD', 'Adresse'),
            'ZYFA_Famille': ('ZYFA', 'Personne à charge'),
            'ZYPP_PersonnesPrevenir': ('ZYPP', 'Personne à prévenir'),
            'ZYIB_IdentiteBancaire': ('ZYIB', 'Identité bancaire'),
            'ZYRE_RolesEmployes': ('ZYRE', 'Rôle employé'),
            'ZYDO_Documents': ('ZYDO', 'Document'),
        }

        if sheet_name not in model_mapping:
            return

        model_code, model_name = model_mapping[sheet_name]

        # Identifier clé (matricule ou autre)
        if sheet_name == 'ZY00_Employes':
            identifier = self.get_value(row, 'Matricule', f'Ligne {line_num}')
        else:
            identifier = self.get_value(row, 'Employe_MATRICULE', f'Ligne {line_num}')

        # Collecter les données
        row_data = {}
        for col in row.index:
            value = self.get_value(row, col)
            if value:  # N'afficher que les valeurs non vides
                row_data[col] = value

        # Ajouter aux données à importer
        self.detailed_report['data_to_import'].append({
            'sheet': sheet_name,
            'model': model_code,
            'model_name': model_name,
            'line': line_num,
            'identifier': identifier,
            'data': row_data,
            'status': 'pending'  # pending, will_import, imported, error, skipped
        })

    def validate_all_data(self) -> bool:
        """Valide toutes les données selon les règles"""
        self.stdout.write("\n🔍 VALIDATION DES DONNÉES")

        for sheet_name in self.determine_import_order():
            df = self.dataframes.get(sheet_name)
            if df is None or df.empty:
                continue

            self.stdout.write(f"  📄 {sheet_name}: {len(df)} ligne(s)")

            # Limiter le nombre de lignes si demandé
            if self.limit:
                df = df.head(self.limit)

            # Valider chaque ligne
            for idx, row in df.iterrows():
                if self.limit and idx >= self.limit:
                    break

                line_num = idx + 2
                self.validate_row(sheet_name, row, line_num)

        self.print_validation_summary()
        return len(self.validation_errors) == 0

    def validate_row(self, sheet_name, row, line_num):
        """Valide une ligne spécifique"""
        validator_name = f"validate_row_{sheet_name.lower().replace('_', '')}"
        if hasattr(self, validator_name):
            try:
                getattr(self, validator_name)(row, line_num)
            except Exception as e:
                error_msg = f"{sheet_name} Ligne {line_num}: Erreur validation - {e}"
                self.validation_errors.append(error_msg)
                self.detailed_report['validation_details'].append({
                    'sheet': sheet_name,
                    'line': line_num,
                    'type': 'error',
                    'message': error_msg
                })
        else:
            # Validation générique
            self.validate_row_generic(sheet_name, row, line_num)

    def validate_row_generic(self, sheet_name, row, line_num):
        """Validation générique pour une ligne"""
        identifier = self.get_value(row, 'Employe_MATRICULE') or self.get_value(row, 'Matricule', f'Ligne {line_num}')

        # Vérifier les champs obligatoires selon la feuille
        if sheet_name == 'ZY00_Employes':
            required = ['Nom', 'Prenoms', 'Date_naissance', 'Sexe', 'Type_id', 'Numero_id']
            for field in required:
                if not self.get_value(row, field):
                    error_msg = f"{identifier}: {field} manquant"
                    self.validation_errors.append(error_msg)
                    self.detailed_report['validation_details'].append({
                        'sheet': sheet_name,
                        'line': line_num,
                        'type': 'error',
                        'message': error_msg,
                        'field': field
                    })

    def validate_row_zy00_employes(self, row, line_num):
        """Validation spécifique pour ZY00_Employes"""
        matricule = self.get_value(row, 'Matricule', f'Ligne {line_num}')

        # Validation dates ID
        date_validite = self.get_value(row, 'Date_validite_id')
        date_expiration = self.get_value(row, 'Date_expiration_id')
        if date_validite and date_expiration:
            validite = self.parse_date(date_validite)
            expiration = self.parse_date(date_expiration)
            if validite and expiration and expiration <= validite:
                error_msg = f"{matricule}: Date_expiration_id doit être > Date_validite_id"
                self.validation_errors.append(error_msg)
                self.detailed_report['validation_details'].append({
                    'sheet': 'ZY00_Employes',
                    'line': line_num,
                    'type': 'error',
                    'message': error_msg,
                    'field': 'Date_expiration_id'
                })

        # Âge minimum
        birth_date = self.get_value(row, 'Date_naissance')
        if birth_date:
            age = self.calculate_age(birth_date)
            if age < 16:
                error_msg = f"{matricule}: Âge minimum 16 ans non respecté (âge: {age})"
                self.validation_errors.append(error_msg)
                self.detailed_report['validation_details'].append({
                    'sheet': 'ZY00_Employes',
                    'line': line_num,
                    'type': 'error',
                    'message': error_msg,
                    'field': 'Date_naissance'
                })

    def validate_row_zyfa_famille(self, row, line_num):
        """Validation spécifique pour ZYFA_Famille"""
        matricule = self.get_value(row, 'Employe_MATRICULE', f'Ligne {line_num}')

        if not matricule:
            error_msg = f"Ligne {line_num}: Matricule manquant"
            self.validation_errors.append(error_msg)
            return

        # Vérifier l'employé existe
        if not self.employee_exists(matricule) and not self.dry_run and not self.ignore_missing:
            error_msg = f"{matricule}: Employé non trouvé pour personne à charge"
            self.validation_errors.append(error_msg)
            self.detailed_report['validation_details'].append({
                'sheet': 'ZYFA_Famille',
                'line': line_num,
                'type': 'error',
                'message': error_msg
            })

        # Validation dates
        date_debut = self.get_value(row, 'Date_debut_prise_charge')
        date_fin = self.get_value(row, 'Date_fin_prise_charge')
        if date_debut and date_fin:
            debut = self.parse_date(date_debut)
            fin = self.parse_date(date_fin)
            if debut and fin and fin <= debut:
                error_msg = f"{matricule}: Date_fin_prise_charge doit être > Date_debut_prise_charge"
                self.validation_errors.append(error_msg)
                self.detailed_report['validation_details'].append({
                    'sheet': 'ZYFA_Famille',
                    'line': line_num,
                    'type': 'error',
                    'message': error_msg,
                    'field': 'Date_fin_prise_charge'
                })

        # Validation date de naissance
        date_naissance = self.get_value(row, 'Date_naissance')
        if date_naissance:
            naissance = self.parse_date(date_naissance)
            if naissance and naissance > timezone.now().date():
                error_msg = f"{matricule}: Date_naissance doit être dans le passé"
                self.validation_errors.append(error_msg)
                self.detailed_report['validation_details'].append({
                    'sheet': 'ZYFA_Famille',
                    'line': line_num,
                    'type': 'error',
                    'message': error_msg,
                    'field': 'Date_naissance'
                })

    def determine_import_order(self):
        """Détermine l'ordre d'importation des feuilles"""
        if self.specific_sheet:
            return [self.specific_sheet]

        # Ordre logique d'importation
        all_sheets = list(self.dataframes.keys())
        base_order = [
            'ZY00_Employes',  # 1. Employés de base
            'ZYNP_HistoriqueNoms',  # 2. Historique noms
            'ZYCO_Contrats',  # 3. Contrats
            'ZYTE_Telephones',  # 4. Téléphones
            'ZYME_Emails',  # 5. Emails
            'ZYAF_Affectations',  # 6. Affectations
            'ZYAD_Adresses',  # 7. Adresses
            'ZYFA_Famille',  # 8. Famille
            'ZYPP_PersonnesPrevenir',  # 9. Personnes à prévenir
            'ZYIB_IdentiteBancaire',  # 10. Identité bancaire
            'ZYRE_RolesEmployes',  # 11. Rôles
            'ZYDO_Documents',  # 12. Documents
        ]

        # Garder seulement les feuilles qui existent
        return [sheet for sheet in base_order if sheet in all_sheets]

    def simulate_sheet_import_detailed(self, sheet_name: str):
        """Simule l'importation d'une feuille avec détails"""
        df = self.dataframes.get(sheet_name)
        if df is None or df.empty:
            self.stdout.write(f"  ℹ️ Feuille {sheet_name} vide")
            return

        self.stdout.write(f"\n🔍 SIMULATION DÉTAILLÉE: {sheet_name}")
        self.stdout.write(f"  📄 {len(df)} ligne(s) à traiter")

        # Limiter le nombre de lignes si demandé
        if self.limit:
            df = df.head(self.limit)

        model_mapping = {
            'ZY00_Employes': ('ZY00', 'Employé'),
            'ZYNP_HistoriqueNoms': ('ZYNP', 'Historique nom/prénom'),
            'ZYCO_Contrats': ('ZYCO', 'Contrat'),
            'ZYTE_Telephones': ('ZYTE', 'Téléphone'),
            'ZYME_Emails': ('ZYME', 'Email'),
            'ZYAF_Affectations': ('ZYAF', 'Affectation'),
            'ZYAD_Adresses': ('ZYAD', 'Adresse'),
            'ZYFA_Famille': ('ZYFA', 'Personne à charge'),
            'ZYPP_PersonnesPrevenir': ('ZYPP', 'Personne à prévenir'),
            'ZYIB_IdentiteBancaire': ('ZYIB', 'Identité bancaire'),
            'ZYRE_RolesEmployes': ('ZYRE', 'Rôle employé'),
            'ZYDO_Documents': ('ZYDO', 'Document'),
        }

        if sheet_name not in model_mapping:
            self.stdout.write(f"  ⚠️ Modèle inconnu pour {sheet_name}")
            return

        model_code, model_name = model_mapping[sheet_name]
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            self.simulate_row_import(sheet_name, model_code, model_name, row, line_num)

    def simulate_row_import(self, sheet_name, model_code, model_name, row, line_num):
        """Simule l'importation d'une ligne avec détails"""
        if sheet_name == 'ZY00_Employes':
            identifier = self.get_value(row, 'Matricule', f'Ligne {line_num}')
        else:
            identifier = self.get_value(row, 'Employe_MATRICULE', f'Ligne {line_num}')

        self.stdout.write(f"\n    📝 LIGNE {line_num}: {identifier}")
        self.stdout.write(f"    {'─' * 50}")

        # Afficher les données
        row_data = {}
        for col in row.index:
            value = self.get_value(row, col)
            if value:  # N'afficher que les valeurs non vides
                row_data[col] = value
                # Formater spécialement certaines colonnes
                display_value = value
                if 'date' in col.lower() or 'Date' in col:
                    date_val = self.parse_date(value)
                    if date_val:
                        display_value = f"{value} → {date_val}"

                self.stdout.write(f"      {col}: {display_value}")

        # Mettre à jour le statut dans le rapport
        for item in self.detailed_report['data_to_import']:
            if item['sheet'] == sheet_name and item['line'] == line_num:
                item['status'] = 'will_import'
                break

        # Simuler la création d'utilisateur pour ZY00
        if sheet_name == 'ZY00_Employes':
            type_dossier = self.get_value(row, 'Type_dossier', 'PRE')
            if type_dossier == 'SAL':
                nom = self.get_value(row, 'Nom', '').strip().upper()
                prenoms = self.get_value(row, 'Prenoms', '').strip()
                base_username = f"{nom.lower()}.{prenoms.split()[0].lower() if prenoms else 'user'}"
                self.stdout.write(f"      👤 Utilisateur à créer: {base_username}")
                self.stdout.write(f"      🔐 Mot de passe: Hronian2024!")

        # Pour ZYFA, afficher des infos spécifiques
        elif sheet_name == 'ZYFA_Famille':
            personne_charge = self.get_value(row, 'Personne_charge', '')
            nom = self.get_value(row, 'Nom', '')
            prenom = self.get_value(row, 'Prenom', '')
            self.stdout.write(f"      👨‍👩‍👧‍👦 Personne à charge: {prenom} {nom} ({personne_charge})")

        self.import_stats['created'] += 1
        self.import_stats['by_model'][model_code]['created'] += 1

        self.stdout.write(f"    ✅ SERAIT IMPORTÉ DANS {model_name}")

    def import_sheet_detailed(self, sheet_name: str):
        """Importe une feuille avec détails"""
        df = self.dataframes.get(sheet_name)
        if df is None or df.empty:
            return

        self.stdout.write(f"\n📦 IMPORTATION DÉTAILLÉE: {sheet_name}")
        self.stdout.write(f"  📄 {len(df)} ligne(s) à importer")

        # Limiter le nombre de lignes si demandé
        if self.limit:
            df = df.head(self.limit)

        import_methods = {
            'ZY00_Employes': self.import_zy00_employes_detailed,
            'ZYNP_HistoriqueNoms': self.import_zynp_historiquenoms_detailed,
            'ZYCO_Contrats': self.import_zyco_contrats_detailed,
            'ZYTE_Telephones': self.import_zyte_telephones_detailed,
            'ZYME_Emails': self.import_zyme_emails_detailed,
            'ZYAF_Affectations': self.import_zyaf_affectations_detailed,
            'ZYAD_Adresses': self.import_zyad_adresses_detailed,
            'ZYFA_Famille': self.import_zyfa_famille_detailed,
            'ZYPP_PersonnesPrevenir': self.import_zypp_personnesprevenir_detailed,
            'ZYIB_IdentiteBancaire': self.import_zyib_identitebancaire_detailed,
            'ZYRE_RolesEmployes': self.import_zyre_rolesemployes_detailed,
            'ZYDO_Documents': self.import_zydo_documents_detailed,
        }

        if sheet_name in import_methods:
            try:
                import_methods[sheet_name](df)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erreur: {e}"))
                raise
        else:
            self.stdout.write(f"  ⚠️ Importation non implémentée pour {sheet_name}")

    def import_zy00_employes_detailed(self, df):
        """Importe les employés avec détails"""
        from employee.models import ZY00
        from entreprise.models import Entreprise

        model_code = 'ZY00'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Matricule')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                self.stdout.write(f"\n    📝 IMPORTATION: {matricule} (Ligne {line_num})")
                self.stdout.write(f"    {'─' * 40}")

                # Préparation des données avec affichage
                data = {}
                fields_to_show = ['Nom', 'Prenoms', 'Date_naissance', 'Sexe', 'Type_dossier',
                                  'Entreprise_CODE', 'Coefficient_temps_travail']

                for field in fields_to_show:
                    value = self.get_value(row, field, '')
                    if field == 'Entreprise_CODE' and value:
                        data['entreprise_code'] = value
                        self.stdout.write(f"      🏢 Entreprise: {value}")
                    elif value:
                        self.stdout.write(f"      {field}: {value}")

                # Importation réelle
                employe, created = self.import_zy00_row(row, matricule)

                if created:
                    self.stdout.write(f"    ✅ CRÉÉ: {matricule}")

                    # Mettre à jour le rapport
                    for item in self.detailed_report['data_to_import']:
                        if item['sheet'] == 'ZY00_Employes' and item['identifier'] == matricule:
                            item['status'] = 'imported'
                            item['result'] = 'created'
                            break

                    self.detailed_report['import_results'].append({
                        'sheet': 'ZY00_Employes',
                        'line': line_num,
                        'matricule': matricule,
                        'action': 'created',
                        'details': {
                            'nom': employe.nom,
                            'prenoms': employe.prenoms,
                            'uuid': str(employe.uuid),
                            'entreprise': employe.entreprise.code if employe.entreprise else None
                        }
                    })
                else:
                    self.stdout.write(f"    🔄 MIS À JOUR: {matricule}")

                    # Mettre à jour le rapport
                    for item in self.detailed_report['data_to_import']:
                        if item['sheet'] == 'ZY00_Employes' and item['identifier'] == matricule:
                            item['status'] = 'imported'
                            item['result'] = 'updated'
                            break

                    self.detailed_report['import_results'].append({
                        'sheet': 'ZY00_Employes',
                        'line': line_num,
                        'matricule': matricule,
                        'action': 'updated'
                    })

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zy00_row(self, row, matricule):
        """Importe une ligne ZY00"""
        from employee.models import ZY00
        from entreprise.models import Entreprise

        # Préparation des données
        data = {
            'nom': self.get_value(row, 'Nom', '').strip().upper(),
            'prenoms': self.get_value(row, 'Prenoms', '').strip(),
            'date_naissance': self.parse_date(self.get_value(row, 'Date_naissance')),
            'sexe': self.get_value(row, 'Sexe', '').upper(),
            'ville_naissance': self.get_value(row, 'Ville_naissance', '').strip(),
            'pays_naissance': self.get_value(row, 'Pays_naissance', '').strip().upper(),
            'situation_familiale': self.get_value(row, 'Situation_familiale', ''),
            'type_id': self.get_value(row, 'Type_id', ''),
            'numero_id': self.get_value(row, 'Numero_id', ''),
            'date_validite_id': self.parse_date(self.get_value(row, 'Date_validite_id')),
            'date_expiration_id': self.parse_date(self.get_value(row, 'Date_expiration_id')),
            'type_dossier': self.get_value(row, 'Type_dossier', 'PRE'),
            'date_validation_embauche': self.parse_date(self.get_value(row, 'Date_validation_embauche')),
            'etat': self.get_value(row, 'Etat', 'actif'),
            'username': self.get_value(row, 'Username', '') or self.get_value(row, 'Nom', ''),
            'prenomuser': self.get_value(row, 'Prenomuser', '') or self.get_value(row, 'Prenoms', ''),
            'date_entree_entreprise': self.parse_date(self.get_value(row, 'Date_entree_entreprise')),
            'coefficient_temps_travail': float(self.get_value(row, 'Coefficient_temps_travail', '1')),
        }

        # 🔵 GESTION DE L'ENTREPRISE - IMPORTANT : DOIT EXISTER
        entreprise_code = self.get_value(row, 'Entreprise_CODE')
        if entreprise_code:
            entreprise = self.find_entreprise(entreprise_code)
            if entreprise:
                data['entreprise'] = entreprise
                if self.verbose:
                    self.stdout.write(f"      🔗 Entreprise liée: {entreprise.nom} ({entreprise.code})")
            else:
                # Si l'entreprise n'existe pas, on ne peut pas créer l'employé
                error_msg = f"Impossible de créer l'employé {matricule}: Entreprise '{entreprise_code}' non trouvée"
                raise CommandError(error_msg)
        else:
            # Si pas d'entreprise pour un SAL, c'est une erreur
            type_dossier = self.get_value(row, 'Type_dossier', 'PRE')
            if type_dossier == 'SAL':
                warning_msg = f"Employé {matricule} de type SAL sans Entreprise_CODE"
                self.validation_warnings.append(warning_msg)
                self.detailed_report['warnings'].append(warning_msg)

        # Générer un UUID si nouvel employé
        existing_employe = ZY00.objects.filter(matricule=matricule).first()
        if not existing_employe:
            data['uuid'] = uuid.uuid4()
            if self.verbose:
                self.stdout.write(f"      🆔 UUID généré: {data['uuid']}")

        # Nettoyer les données (enlever les valeurs None)
        data = {k: v for k, v in data.items() if v is not None}

        # Créer ou mettre à jour
        employe, created = ZY00.objects.update_or_create(
            matricule=matricule,
            defaults=data
        )

        # Mettre à jour le cache
        self.employee_cache[matricule] = employe

        # Créer l'utilisateur si demandé
        if self.create_users and employe.type_dossier == 'SAL' and not employe.user:
            user_info = self.create_user_for_employee(employe)
            if user_info:
                self.detailed_report['users_created'].append(user_info)

        return employe, created

    def import_zynp_historiquenoms_detailed(self, df):
        """Importe l'historique des noms avec détails"""
        from employee.models import ZYNP

        model_code = 'ZYNP'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'nom': self.get_value(row, 'Nom', '').strip().upper(),
                    'prenoms': self.get_value(row, 'Prenoms', '').strip(),
                    'date_debut_validite': self.parse_date(self.get_value(row, 'Date_debut_validite')),
                    'date_fin_validite': self.parse_date(self.get_value(row, 'Date_fin_validite')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYNP.objects.filter(
                    employe=employe,
                    date_debut_validite=data['date_debut_validite']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Historique mis à jour pour {matricule}")
                else:
                    ZYNP.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Historique créé pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyco_contrats_detailed(self, df):
        """Importe les contrats avec détails"""
        from employee.models import ZYCO

        model_code = 'ZYCO'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'type_contrat': self.get_value(row, 'Type_contrat', ''),
                    'date_debut': self.parse_date(self.get_value(row, 'Date_debut')),
                    'date_fin': self.parse_date(self.get_value(row, 'Date_fin')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYCO.objects.filter(
                    employe=employe,
                    type_contrat=data['type_contrat'],
                    date_debut=data['date_debut']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Contrat mis à jour pour {matricule}")
                else:
                    ZYCO.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Contrat créé pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyte_telephones_detailed(self, df):
        """Importe les téléphones avec détails"""
        from employee.models import ZYTE

        model_code = 'ZYTE'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'numero': self.get_value(row, 'Numero', ''),
                    'date_debut_validite': self.parse_date(self.get_value(row, 'Date_debut_validite')),
                    'date_fin_validite': self.parse_date(self.get_value(row, 'Date_fin_validite')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYTE.objects.filter(
                    employe=employe,
                    numero=data['numero'],
                    date_debut_validite=data['date_debut_validite']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Téléphone mis à jour pour {matricule}")
                else:
                    ZYTE.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Téléphone créé pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyme_emails_detailed(self, df):
        """Importe les emails avec détails"""
        from employee.models import ZYME

        model_code = 'ZYME'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'email': self.get_value(row, 'Email', ''),
                    'date_debut_validite': self.parse_date(self.get_value(row, 'Date_debut_validite')),
                    'date_fin_validite': self.parse_date(self.get_value(row, 'Date_fin_validite')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYME.objects.filter(
                    employe=employe,
                    email=data['email'],
                    date_debut_validite=data['date_debut_validite']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Email mis à jour pour {matricule}")
                else:
                    ZYME.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Email créé pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyaf_affectations_detailed(self, df):
        """Importe les affectations avec détails"""
        from employee.models import ZYAF
        from departement.models import ZDPO

        model_code = 'ZYAF'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                # Trouver le poste
                poste_code = self.get_value(row, 'Poste_CODE')
                if not poste_code:
                    self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Poste_CODE manquant - IGNORÉ")
                    self.import_stats['skipped'] += 1
                    self.import_stats['by_model'][model_code]['skipped'] += 1
                    continue

                poste = self.get_poste(poste_code)
                if not poste:
                    self.stdout.write(f"\n    ⚠️ LIGNE {line_num}: Poste {poste_code} non trouvé - IGNORÉ")
                    self.import_stats['skipped'] += 1
                    self.import_stats['by_model'][model_code]['skipped'] += 1
                    continue

                data = {
                    'poste': poste,
                    'date_debut': self.parse_date(self.get_value(row, 'Date_debut')),
                    'date_fin': self.parse_date(self.get_value(row, 'Date_fin')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYAF.objects.filter(
                    employe=employe,
                    poste=poste,
                    date_debut=data['date_debut']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Affectation mise à jour pour {matricule}")
                else:
                    ZYAF.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Affectation créée pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyad_adresses_detailed(self, df):
        """Importe les adresses avec détails"""
        from employee.models import ZYAD

        model_code = 'ZYAD'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'type_adresse': self.get_value(row, 'Type_adresse', 'PRINCIPALE'),
                    'rue': self.get_value(row, 'Rue', ''),
                    'complement': self.get_value(row, 'Complement', ''),
                    'ville': self.get_value(row, 'Ville', ''),
                    'pays': self.get_value(row, 'Pays', '').upper(),
                    'code_postal': self.get_value(row, 'Code_postal', ''),
                    'date_debut': self.parse_date(self.get_value(row, 'Date_debut')),
                    'date_fin': self.parse_date(self.get_value(row, 'Date_fin')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Formater la ville
                if data['ville']:
                    data['ville'] = data['ville'].title()

                # Vérifier l'unicité
                existing = ZYAD.objects.filter(
                    employe=employe,
                    type_adresse=data['type_adresse'],
                    date_debut=data['date_debut']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Adresse mise à jour pour {matricule}")
                else:
                    ZYAD.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Adresse créée pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zypp_personnesprevenir_detailed(self, df):
        """Importe les personnes à prévenir avec détails"""
        from employee.models import ZYPP

        model_code = 'ZYPP'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'nom': self.get_value(row, 'Nom', '').strip().upper(),
                    'prenom': self.get_value(row, 'Prenom', '').strip(),
                    'lien_parente': self.get_value(row, 'Lien_parente', ''),
                    'telephone_principal': self.get_value(row, 'Telephone_principal', ''),
                    'telephone_secondaire': self.get_value(row, 'Telephone_secondaire', ''),
                    'email': self.get_value(row, 'Email', ''),
                    'adresse': self.get_value(row, 'Adresse', ''),
                    'ordre_priorite': int(self.get_value(row, 'Ordre_priorite', '1')),
                    'date_debut_validite': self.parse_date(self.get_value(row, 'Date_debut_validite')),
                    'date_fin_validite': self.parse_date(self.get_value(row, 'Date_fin_validite')),
                    'actif': self.get_value(row, 'Actif', 'True').upper() == 'TRUE',
                }

                # Vérifier l'unicité
                existing = ZYPP.objects.filter(
                    employe=employe,
                    nom=data['nom'],
                    prenom=data['prenom'],
                    ordre_priorite=data['ordre_priorite']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Personne à prévenir mise à jour pour {matricule}")
                else:
                    ZYPP.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Personne à prévenir créée pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyib_identitebancaire_detailed(self, df):
        """Importe les identités bancaires avec détails"""
        from employee.models import ZYIB

        model_code = 'ZYIB'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                data = {
                    'titulaire_compte': self.get_value(row, 'Titulaire_compte', '').upper(),
                    'nom_banque': self.get_value(row, 'Nom_banque', '').upper(),
                    'code_banque': self.get_value(row, 'Code_banque', ''),
                    'code_guichet': self.get_value(row, 'Code_guichet', ''),
                    'numero_compte': self.get_value(row, 'Numero_compte', ''),
                    'cle_rib': self.get_value(row, 'Cle_rib', ''),
                    'iban': self.get_value(row, 'IBAN', ''),
                    'bic': self.get_value(row, 'BIC', ''),
                    'type_compte': self.get_value(row, 'Type_compte', 'COURANT'),
                    'domiciliation': self.get_value(row, 'Domiciliation', ''),
                    'date_ouverture': self.parse_date(self.get_value(row, 'Date_ouverture')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Nettoyer les champs
                if data['iban']:
                    data['iban'] = data['iban'].replace(' ', '').upper()
                if data['bic']:
                    data['bic'] = data['bic'].replace(' ', '').upper()

                # Mettre à jour ou créer
                existing = getattr(employe, 'identite_bancaire', None)
                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Identité bancaire mise à jour pour {matricule}")
                else:
                    ZYIB.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Identité bancaire créée pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyre_rolesemployes_detailed(self, df):
        """Importe les rôles employés avec détails"""
        from employee.models import ZYRE, ZYRO

        model_code = 'ZYRE'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                # Trouver le rôle
                role_code = self.get_value(row, 'Role_CODE')
                if not role_code:
                    self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Role_CODE manquant - IGNORÉ")
                    self.import_stats['skipped'] += 1
                    self.import_stats['by_model'][model_code]['skipped'] += 1
                    continue

                role = self.get_role(role_code)
                if not role:
                    self.stdout.write(f"\n    ⚠️ LIGNE {line_num}: Rôle {role_code} non trouvé - IGNORÉ")
                    self.import_stats['skipped'] += 1
                    self.import_stats['by_model'][model_code]['skipped'] += 1
                    continue

                data = {
                    'role': role,
                    'date_debut': self.parse_date(self.get_value(row, 'Date_debut')),
                    'date_fin': self.parse_date(self.get_value(row, 'Date_fin')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                    'commentaire': self.get_value(row, 'Commentaire', ''),
                }

                # Vérifier l'unicité
                existing = ZYRE.objects.filter(
                    employe=employe,
                    role=role,
                    date_debut=data['date_debut']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"\n    🔄 LIGNE {line_num}: Rôle mis à jour pour {matricule}")
                else:
                    ZYRE.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"\n    ✅ LIGNE {line_num}: Rôle créé pour {matricule}")

            except Exception as e:
                error_msg = f"Erreur importation {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zyfa_famille_detailed(self, df):
        """Importe la famille avec détails"""
        from employee.models import ZYFA

        model_code = 'ZYFA'
        self.init_model_stats(model_code)

        for idx, row in df.iterrows():
            if self.limit and idx >= self.limit:
                break

            line_num = idx + 2
            matricule = self.get_value(row, 'Employe_MATRICULE')

            if not matricule:
                self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Matricule manquant - IGNORÉ")
                self.import_stats['skipped'] += 1
                self.import_stats['by_model'][model_code]['skipped'] += 1
                continue

            try:
                employe = self.get_employee(matricule)
                if not employe:
                    if self.ignore_missing:
                        self.stdout.write(f"\n    ⏭️ LIGNE {line_num}: Employé {matricule} non trouvé - IGNORÉ")
                        self.import_stats['skipped'] += 1
                        self.import_stats['by_model'][model_code]['skipped'] += 1
                        continue
                    raise CommandError(f"Employé {matricule} non trouvé")

                self.stdout.write(f"\n    📝 IMPORTATION: Personne à charge pour {matricule} (Ligne {line_num})")
                self.stdout.write(f"    {'─' * 40}")

                data = {
                    'personne_charge': self.get_value(row, 'Personne_charge', ''),
                    'nom': self.get_value(row, 'Nom', '').strip().upper(),
                    'prenom': self.get_value(row, 'Prenom', '').strip(),
                    'sexe': self.get_value(row, 'Sexe', '').upper(),
                    'date_naissance': self.parse_date(self.get_value(row, 'Date_naissance')),
                    'date_debut_prise_charge': self.parse_date(self.get_value(row, 'Date_debut_prise_charge')),
                    'date_fin_prise_charge': self.parse_date(self.get_value(row, 'Date_fin_prise_charge')),
                    'actif': self.get_value(row, 'Actif', 'TRUE').upper() == 'TRUE',
                }

                # Afficher les données importantes
                if self.show_data:
                    self.stdout.write(f"      Personne: {data['nom']} {data['prenom']}")
                    self.stdout.write(f"      Type: {data['personne_charge']}")
                    self.stdout.write(f"      Date naissance: {data['date_naissance']}")
                    if data['date_debut_prise_charge']:
                        self.stdout.write(f"      Date début prise charge: {data['date_debut_prise_charge']}")

                # Vérifier l'unicité (basé sur nom, prénom, date de naissance)
                existing = ZYFA.objects.filter(
                    employe=employe,
                    nom=data['nom'],
                    prenom=data['prenom'],
                    date_naissance=data['date_naissance']
                ).first()

                if existing:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.update_stats(model_code, False, f"{matricule}")
                    self.stdout.write(f"    🔄 MIS À JOUR: Personne à charge pour {matricule}")
                else:
                    ZYFA.objects.create(employe=employe, **data)
                    self.update_stats(model_code, True, f"{matricule}")
                    self.stdout.write(f"    ✅ CRÉÉ: Personne à charge pour {matricule}")

                # Mettre à jour le rapport
                for item in self.detailed_report['data_to_import']:
                    if item['sheet'] == 'ZYFA_Famille' and item['line'] == line_num:
                        item['status'] = 'imported'
                        item['result'] = 'updated' if existing else 'created'
                        break

            except Exception as e:
                error_msg = f"Erreur importation personne à charge pour {matricule}: {e}"
                self.stdout.write(self.style.ERROR(f"    ❌ {error_msg}"))
                self.handle_import_error_detailed(model_code, matricule, e, line_num)

    def import_zydo_documents_detailed(self, df):
        """Importe les documents avec détails"""
        from employee.models import ZYDO

        model_code = 'ZYDO'
        self.init_model_stats(model_code)

        self.stdout.write("  ℹ️ Feuille ZYDO_Documents vide ou non traitée (fichiers physiques requis)")

    def handle_import_error_detailed(self, model_code, identifier, error, line_num=None):
        """Gère les erreurs d'importation avec détails"""
        self.import_stats['errors'] += 1
        self.import_stats['by_model'][model_code]['errors'] += 1

        error_details = {
            'model': model_code,
            'identifier': identifier,
            'error': str(error),
            'line': line_num
        }

        # Ajouter aux erreurs spécifiques
        self.detailed_report['specific_errors'].append({
            'type': 'import_error',
            'details': error_details
        })

        # Mettre à jour le statut dans data_to_import
        for item in self.detailed_report['data_to_import']:
            if item.get('line') == line_num or item.get('identifier') == identifier:
                item['status'] = 'error'
                item['error'] = str(error)
                break

    def get_value(self, row, field, default=''):
        """Récupère une valeur d'une ligne avec gestion des valeurs nulles"""
        value = row.get(field, default)
        if pd.isna(value) or value is None:
            return default
        return str(value).strip()

    def parse_date(self, date_str):
        """Parse une date depuis différents formats"""
        if not date_str or pd.isna(date_str):
            return None

        date_str = str(date_str).strip()
        if not date_str:
            return None

        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
        ]

        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        try:
            return pd.to_datetime(date_str).date()
        except:
            return None

    def calculate_age(self, birth_date_str):
        """Calcule l'âge à partir d'une date de naissance"""
        birth_date = self.parse_date(birth_date_str)
        if not birth_date:
            return 0

        today = datetime.date.today()
        age = today.year - birth_date.year

        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age

    def employee_exists(self, matricule):
        """Vérifie si un employé existe"""
        if matricule in self.employee_cache:
            return True

        try:
            from employee.models import ZY00
            exists = ZY00.objects.filter(matricule=matricule).exists()
            if exists and matricule not in self.employee_cache:
                self.employee_cache[matricule] = ZY00.objects.get(matricule=matricule)
            return exists
        except:
            return False

    def get_employee(self, matricule):
        """Récupère un employé"""
        if matricule in self.employee_cache:
            return self.employee_cache[matricule]

        try:
            from employee.models import ZY00
            employe = ZY00.objects.get(matricule=matricule)
            self.employee_cache[matricule] = employe
            return employe
        except ZY00.DoesNotExist:
            return None

    def find_entreprise(self, code):
        """Trouve une entreprise par son code - NE PAS CRÉER AUTOMATIQUEMENT"""
        from entreprise.models import Entreprise

        # Chercher dans le cache
        cache_keys = [code.upper(), code, code.lower()]
        for key in cache_keys:
            if key in self.entreprise_cache:
                return self.entreprise_cache[key]

        # Chercher en base - NE PAS CRÉER SI ELLE N'EXISTE PAS
        try:
            entreprise = Entreprise.objects.get(code__iexact=code)
            self.entreprise_cache[code.upper()] = entreprise
            self.entreprise_cache[code] = entreprise
            return entreprise
        except Entreprise.DoesNotExist:
            # NE PAS CRÉER L'ENTREPRISE AUTOMATIQUEMENT
            # L'entreprise doit exister dans le système
            error_msg = f"Entreprise '{code}' non trouvée. Veuillez d'abord créer cette entreprise dans l'application."
            self.validation_errors.append(error_msg)
            self.detailed_report['specific_errors'].append({
                'type': 'missing_entreprise',
                'message': error_msg,
                'entreprise_code': code
            })
            return None

    def get_poste(self, poste_code):
        """Récupère un poste par son code"""
        if poste_code in self.post_cache:
            return self.post_cache[poste_code]

        try:
            from departement.models import ZDPO
            poste = ZDPO.objects.get(CODE=poste_code)
            self.post_cache[poste_code] = poste
            return poste
        except:
            return None

    def get_role(self, role_code):
        """Récupère un rôle par son code"""
        if role_code in self.role_cache:
            return self.role_cache[role_code]

        try:
            from employee.models import ZYRO
            role = ZYRO.objects.get(CODE=role_code, actif=True)
            self.role_cache[role_code] = role
            return role
        except:
            return None

    def init_model_stats(self, model_code):
        """Initialise les statistiques pour un modèle"""
        if model_code not in self.import_stats['by_model']:
            self.import_stats['by_model'][model_code] = {
                'created': 0,
                'updated': 0,
                'errors': 0,
                'skipped': 0
            }

    def update_stats(self, model_code, created, identifier):
        """Met à jour les statistiques"""
        if created:
            self.import_stats['created'] += 1
            self.import_stats['by_model'][model_code]['created'] += 1
        else:
            self.import_stats['updated'] += 1
            self.import_stats['by_model'][model_code]['updated'] += 1

    def create_user_for_employee(self, employe):
        """Crée un utilisateur Django pour un employé"""
        try:
            # Vérifier si l'utilisateur existe déjà
            if employe.user:
                if self.verbose:
                    self.stdout.write(f"    ℹ️ Utilisateur existe déjà pour {employe.matricule}")
                return None

            # Générer un nom d'utilisateur unique basé sur le nom et prénom
            base_username = f"{employe.nom.lower()}.{employe.prenoms.split()[0].lower() if employe.prenoms else 'user'}"
            username = base_username

            # Vérifier si le username existe déjà et ajouter un suffixe si nécessaire
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # 🔵 MOT DE PASSE FIXE comme dans la vue
            password = "Hronian2024!"

            # 🔵 GÉNÉRER L'EMAIL
            # Chercher d'abord un email actif dans ZYME
            email = None
            from employee.models import ZYME
            email_obj = ZYME.objects.filter(employe=employe, actif=True).first()
            if email_obj:
                email = email_obj.email
            else:
                # Sinon utiliser le format standard
                email = f"{username}@onian-easym.com"

            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=employe.prenomuser or (employe.prenoms.split()[0] if employe.prenoms else ''),
                last_name=employe.username or employe.nom,
                email=email,
                is_active=True
            )

            # Lier l'utilisateur à l'employé
            employe.user = user
            employe.save(update_fields=['user'])

            if self.verbose:
                self.stdout.write(f"    👤 Utilisateur créé: {username} ({email})")

            return {
                'matricule': employe.matricule,
                'username': username,
                'password': password,
                'email': email,
                'full_name': f"{employe.nom} {employe.prenoms}"
            }

        except Exception as e:
            error_msg = f"Erreur création utilisateur pour {employe.matricule}: {e}"
            self.detailed_report['warnings'].append(error_msg)
            self.stdout.write(self.style.WARNING(f"    ⚠️ {error_msg}"))
            return None

    def generate_detailed_report(self):
        """Génère un rapport d'intégration détaillé en fichier TXT"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        # Déterminer le nom du fichier
        if self.report_file:
            filename = f"{self.report_file}.txt"
        elif self.dry_run:
            filename = f"import_simulation_detailed_{timestamp}.txt"
        else:
            filename = f"import_report_detailed_{timestamp}.txt"

        report_lines = [
            "=" * 80,
            "RAPPORT DÉTAILLÉ D'INTÉGRATION DES DONNÉES EMPLOYÉS",
            "=" * 80,
            f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Fichier source: {self.file_path}",
            f"Mode: {self.detailed_report['summary']['mode']}",
            f"Options: dry-run={self.dry_run}, create-users={self.create_users}, limit={self.limit}",
            "",
            "=" * 80,
            "STRUCTURE DU FICHIER IMPORTÉ",
            "=" * 80,
        ]

        # Structure des feuilles
        for sheet_name, details in self.detailed_report['sheet_details'].items():
            if sheet_name == 'REGLES_VALIDATION':
                continue

            report_lines.append(f"\n📋 {sheet_name}:")
            report_lines.append(f"  Lignes: {details['row_count']}")
            report_lines.append(f"  Colonnes: {details['column_count']}")

            # Afficher un échantillon de données
            if details['first_rows'] and self.show_data:
                report_lines.append(f"\n  Échantillon de données (3 premières lignes):")
                for i, row in enumerate(details['first_rows'], 1):
                    report_lines.append(f"\n    Ligne {i}:")
                    for key, value in row.items():
                        if value:
                            report_lines.append(f"      {key}: {value}")

        # =================================================================
        report_lines.append("\n" + "=" * 80)
        report_lines.append("DONNÉES À INTÉGRER PAR MODÈLE")
        report_lines.append("=" * 80)

        # Grouper par modèle
        by_model = {}
        for item in self.detailed_report['data_to_import']:
            model = item['model']
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(item)

        # Afficher par modèle
        for model, items in by_model.items():
            report_lines.append(f"\n📦 MODÈLE: {model} ({len(items)} élément(s))")
            report_lines.append("-" * 40)

            for item in items:
                status_icon = {
                    'pending': '⏳',
                    'will_import': '📝',
                    'imported': '✅',
                    'error': '❌',
                    'skipped': '⏭️'
                }.get(item['status'], '?')

                report_lines.append(
                    f"\n{status_icon} {item['model_name']} - Ligne {item['line']}: {item['identifier']}")
                report_lines.append(f"  Statut: {item['status']}")

                if item.get('error'):
                    report_lines.append(f"  ❌ Erreur: {item['error']}")

                # Afficher les données
                if item['data']:
                    report_lines.append(f"  Données:")
                    for key, value in item['data'].items():
                        # Formater les dates
                        if 'date' in key.lower():
                            date_val = self.parse_date(value)
                            if date_val:
                                value = f"{value} → {date_val}"
                        report_lines.append(f"    {key}: {value}")

        # =================================================================
        report_lines.append("\n" + "=" * 80)
        report_lines.append("RÉSULTATS DE L'IMPORTATION")
        report_lines.append("=" * 80)

        report_lines.append(f"\n📊 STATISTIQUES GLOBALES:")
        report_lines.append(f"  Total éléments analysés: {len(self.detailed_report['data_to_import'])}")
        report_lines.append(f"  Créés: {self.import_stats['created']}")
        report_lines.append(f"  Mis à jour: {self.import_stats['updated']}")
        report_lines.append(f"  Erreurs: {self.import_stats['errors']}")
        report_lines.append(f"  Ignorés: {self.import_stats['skipped']}")

        # Résultats par modèle
        if self.import_stats['by_model']:
            report_lines.append(f"\n📈 PAR MODÈLE:")
            for model, stats in self.import_stats['by_model'].items():
                total = stats['created'] + stats['updated'] + stats['errors'] + stats['skipped']
                if total > 0:
                    report_lines.append(
                        f"  {model}: "
                        f"C={stats['created']} "
                        f"U={stats['updated']} "
                        f"E={stats['errors']} "
                        f"I={stats['skipped']}"
                    )

        # =================================================================
        report_lines.append("\n" + "=" * 80)
        report_lines.append("UTILISATEURS CRÉÉS")
        report_lines.append("=" * 80)

        if self.detailed_report['users_created']:
            report_lines.append("\n⚠️ CONSERVEZ CES INFORMATIONS DANS UN ENDROIT SÉCURISÉ")
            report_lines.append("=" * 40)

            for user in self.detailed_report['users_created']:
                report_lines.append(f"\n👤 {user['full_name']} ({user['matricule']})")
                report_lines.append(f"  Identifiant: {user['username']}")
                report_lines.append(f"  Mot de passe: {user['password']}")
                report_lines.append(f"  Email: {user['email']}")

        # =================================================================
        report_lines.append("\n" + "=" * 80)
        report_lines.append("ERREURS SPÉCIFIQUES")
        report_lines.append("=" * 80)

        if self.detailed_report['specific_errors']:
            for error in self.detailed_report['specific_errors']:
                report_lines.append(f"\n📌 Type: {error['type']}")
                if 'details' in error:
                    details = error['details']
                    report_lines.append(f"  Modèle: {details.get('model', 'N/A')}")
                    report_lines.append(f"  Identifiant: {details.get('identifier', 'N/A')}")
                    report_lines.append(f"  Ligne: {details.get('line', 'N/A')}")
                    report_lines.append(f"  Erreur: {details.get('error', 'N/A')}")
                else:
                    report_lines.append(f"  {error.get('error', 'Erreur inconnue')}")

        # =================================================================
        report_lines.append("\n" + "=" * 80)
        report_lines.append("SYNTHÈSE")
        report_lines.append("=" * 80)

        end_time = datetime.datetime.now()
        duration = end_time - self.detailed_report['summary']['start_time']

        report_lines.append(f"\n⏱️ Durée: {duration}")
        report_lines.append(f"📁 Fichier traité: {self.file_path}")
        report_lines.append(f"🎯 Mode: {self.detailed_report['summary']['mode']}")

        if self.dry_run:
            report_lines.append(f"🔍 Ceci est une simulation - Aucune donnée n'a été modifiée")
        else:
            report_lines.append(f"✅ Importation terminée")

        report_lines.append(f"\n📄 Rapport généré: {filename}")
        report_lines.append("=" * 80)

        # Sauvegarder le rapport
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(report_lines))

            self.stdout.write(f"\n📄 Rapport détaillé sauvegardé: {filename}")
            self.stdout.write(f"   {len(report_lines)} lignes")
        except Exception as e:
            self.stdout.write(f"\n❌ Erreur sauvegarde rapport: {e}")

    def print_statistics(self):
        """Affiche les statistiques"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SYNTHÈSE DES RÉSULTATS")
        self.stdout.write("=" * 80)

        total = (self.import_stats['created'] + self.import_stats['updated'] +
                 self.import_stats['skipped'] + self.import_stats['errors'])

        self.stdout.write(f"📊 Total éléments traités: {total}")
        self.stdout.write(f"✅ Créés: {self.import_stats['created']}")
        self.stdout.write(f"🔄 Mis à jour: {self.import_stats['updated']}")
        self.stdout.write(f"⏭️ Ignorés: {self.import_stats['skipped']}")
        self.stdout.write(f"❌ Erreurs: {self.import_stats['errors']}")

        if self.detailed_report['users_created']:
            self.stdout.write(f"👤 Utilisateurs créés: {len(self.detailed_report['users_created'])}")

        if self.dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 MODE SIMULATION - Aucune donnée n'a été modifiée"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ IMPORTATION TERMINÉE"))

    def print_validation_summary(self):
        """Affiche le résumé des validations"""
        if self.validation_errors:
            self.stdout.write(self.style.ERROR(f"\n❌ ERREURS DE VALIDATION ({len(self.validation_errors)}):"))
            for i, error in enumerate(self.validation_errors[:10], 1):
                self.stdout.write(f"  {i}. {error}")
            if len(self.validation_errors) > 10:
                self.stdout.write(f"  ... et {len(self.validation_errors) - 10} erreur(s) supplémentaire(s)")

        if self.validation_warnings:
            self.stdout.write(self.style.WARNING(f"\n⚠️ AVERTISSEMENTS ({len(self.validation_warnings)}):"))
            for i, warning in enumerate(self.validation_warnings[:10], 1):
                self.stdout.write(f"  {i}. {warning}")
            if len(self.validation_warnings) > 10:
                self.stdout.write(f"  ... et {len(self.validation_warnings) - 10} avertissement(s) supplémentaire(s)")


# Simulation avec rapport détaillé
#python manage.py import_employees --dry-run --verbose --show-data --report-file="simulation_detailed"

# Import réel avec limite (pour test)
#python manage.py import_employees --limit=10 --report-file="test_10_lignes"

# Import complet avec création d'utilisateurs
#python manage.py import_employees --create-users --force --report-file="import_complet"

# Voir les données sans limite
#python manage.py import_employees --dry-run --show-data

# Une feuille spécifique
#python manage.py import_employees --sheet="ZYFA_Famille" --report-file="contrats_only"

# Import réel
#python manage.py import_employees --create-users --force --report-file="import_final"
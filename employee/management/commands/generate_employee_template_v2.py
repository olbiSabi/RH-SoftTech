# employee/management/commands/generate_employee_template_v2.py
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import os
from django.conf import settings
import random


class Command(BaseCommand):
    help = 'Génère un fichier Excel template pour l\'importation des employés avec validation des règles métier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=int,
            default=10,
            help='Nombre d\'exemples à générer (défaut: 10)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='employee_template.xlsx',
            help='Nom du fichier de sortie (défaut: employee_template.xlsx)'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['PRE', 'SAL', 'MIXED'],
            default='MIXED',
            help='Type de dossier: PRE (pré-embauche), SAL (salariés), MIXED (mixte)'
        )
        parser.add_argument(
            '--with-errors',
            action='store_true',
            help='Inclure des exemples avec erreurs pour tester la validation'
        )

    def handle(self, *args, **options):
        nombre = options['nombre']
        output_filename = options['output']
        dossier_type = options['type']
        with_errors = options['with_errors']

        # Créer le dossier File s'il n'existe pas
        file_dir = os.path.join(settings.BASE_DIR, 'File')
        os.makedirs(file_dir, exist_ok=True)
        output_path = os.path.join(file_dir, output_filename)

        self.stdout.write(self.style.SUCCESS(f"🚀 Génération du template Excel pour {nombre} employés..."))
        self.stdout.write(f"📊 Type de dossier: {dossier_type}")
        self.stdout.write(f"⚠️  Exemples avec erreurs: {'OUI' if with_errors else 'NON'}")

        # Date actuelle
        aujourdhui = timezone.now().date()

        # Données de référence pour les choix
        villes_france = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Bordeaux', 'Lille', 'Nice', 'Nantes', 'Strasbourg']
        pays_list = ['FRANCE', 'BELGIQUE', 'SUISSE', 'ESPAGNE', 'ALLEMAGNE']
        entreprises_codes = ['ONI001', 'ONI002', 'ONI003', 'ENT001', 'ENT002']
        conventions_codes = ['CONV001', 'CONV002', 'CONV003', '', '']  # Certains vides
        postes_codes = ['PST001', 'PST002', 'PST003', 'PST004', 'PST005', 'PST006', 'PST007']
        departements_codes = ['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004', 'DEPT005']
        roles_codes = ['DRH', 'MANAGER', 'COMPTABLE', 'TECHNICIEN', 'COMMERCIAL', 'ADMIN', 'SUPPORT']

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # ==============================================
            # FEUILLE 1: ZY00_Employes (Employés principaux)
            # ==============================================
            self.stdout.write("📋 Création feuille ZY00_Employes...")

            data_zy00 = []
            for i in range(1, nombre + 1):
                # Déterminer le type de dossier
                if dossier_type == 'PRE':
                    type_dossier_val = 'PRE'
                elif dossier_type == 'SAL':
                    type_dossier_val = 'SAL'
                else:
                    type_dossier_val = 'PRE' if i % 3 == 0 else 'SAL'  # MIXED: 1/3 PRE, 2/3 SAL

                # Déterminer l'état
                etat_val = 'inactif' if i % 10 == 0 else 'actif'  # 10% inactifs

                # Dates de validité ID
                date_validite = aujourdhui - timedelta(days=365 * 2)
                date_expiration = aujourdhui + timedelta(days=365 * 3)

                # Date de naissance (entre 20 et 60 ans)
                age = random.randint(20, 60)
                date_naissance = aujourdhui - timedelta(days=365 * age)

                # Coefficient temps travail
                coeff = 1.00 if i % 3 != 0 else round(random.uniform(0.5, 0.8), 2)

                # Ajouter des erreurs si demandé
                if with_errors and i % 4 == 0:
                    # Erreur: date expiration avant date validité
                    date_expiration = date_validite - timedelta(days=30)
                elif with_errors and i % 5 == 0:
                    # Erreur: pas de numéro ID
                    numero_id = ''
                elif with_errors and i % 6 == 0:
                    # Erreur: coefficient invalide
                    coeff = 1.50
                else:
                    numero_id = f"ID{str(i).zfill(6)}FR{random.randint(1000, 9999)}"

                employe_data = {
                    # 🔴 CHAMPS OBLIGATOIRES
                    'Matricule': f"MT{i:06d}",
                    'Nom': f"NOM{i}",
                    'Prenoms': f"PRENOM{i}",
                    'Date_naissance': date_naissance.strftime('%Y-%m-%d'),
                    'Sexe': 'M' if i % 2 == 0 else 'F',
                    'Type_id': random.choice(['CNI', 'PASSEPORT', 'AUTRES']),
                    'Numero_id': numero_id if 'numero_id' in locals() else f"ID{str(i).zfill(6)}FR{random.randint(1000, 9999)}",
                    'Date_validite_id': date_validite.strftime('%Y-%m-%d'),
                    'Date_expiration_id': date_expiration.strftime('%Y-%m-%d'),

                    # 🟡 CHAMPS CONDITIONNELS
                    'Type_dossier': type_dossier_val,
                    'Date_validation_embauche': aujourdhui.strftime('%Y-%m-%d') if type_dossier_val == 'SAL' else '',
                    'Etat': etat_val,

                    # 🟢 CHAMPS OPTIONNELS
                    'Username': f"user{i}",
                    'Prenomuser': f"PrenomUser{i}",
                    'Ville_naissance': random.choice(villes_france),
                    'Pays_naissance': random.choice(pays_list),
                    'Situation_familiale': random.choice(['CELIBATAIRE', 'MARIE', 'DIVORCE', 'PACSE', '']),
                    'Entreprise_CODE': random.choice(entreprises_codes) if type_dossier_val == 'SAL' else '',
                    'Convention_CODE': random.choice(conventions_codes),
                    'Date_entree_entreprise': (aujourdhui - timedelta(days=random.randint(0, 365 * 5))).strftime(
                        '%Y-%m-%d'),
                    'Coefficient_temps_travail': coeff,
                    'Photo': 'photo_employe.jpg' if i % 3 == 0 else '',

                    # 🔵 CHAMPS CALCULÉS (non à remplir)
                    '_UUID': f"Généré automatiquement",
                    '_User_id': f"Créé automatiquement si besoin",
                }

                data_zy00.append(employe_data)

            df_zy00 = pd.DataFrame(data_zy00)

            # Ajouter une ligne d'instructions
            instructions = pd.DataFrame([{
                'Matricule': '⚠️ INSTRUCTIONS:',
                'Nom': '1. Le matricule est généré automatiquement si vide',
                'Prenoms': '2. Les dates doivent être au format YYYY-MM-DD',
                'Date_naissance': '3. Sexe: M ou F',
                'Sexe': '4. Type_dossier: PRE ou SAL',
                'Type_id': '5. Pour SAL, Entreprise_CODE est obligatoire',
                'Numero_id': '6. Date_expiration_id > Date_validite_id',
                'Date_validite_id': '7. Coefficient: entre 0 et 1',
                'Date_expiration_id': '8. Photo: nom du fichier seulement',
                'Type_dossier': '',
                'Date_validation_embauche': '',
                'Etat': '',
                'Username': '',
                'Prenomuser': '',
                'Ville_naissance': '',
                'Pays_naissance': '',
                'Situation_familiale': '',
                'Entreprise_CODE': '',
                'Convention_CODE': '',
                'Date_entree_entreprise': '',
                'Coefficient_temps_travail': '',
                'Photo': '',
                '_UUID': '',
                '_User_id': ''
            }])

            df_zy00 = pd.concat([instructions, df_zy00], ignore_index=True)
            df_zy00.to_excel(writer, sheet_name='ZY00_Employes', index=False)

            # ==============================================
            # FEUILLE 2: ZYNP_HistoriqueNoms
            # ==============================================
            self.stdout.write("📋 Création feuille ZYNP_HistoriqueNoms...")

            data_znp = []
            for i in range(1, min(nombre, 8) + 1):  # Historique pour 8 employés max
                matricule = f"MT{i:06d}"

                # Historique actuel
                data_znp.append({
                    'Employe_MATRICULE': matricule,
                    'Nom': f"NOM{i}",
                    'Prenoms': f"PRENOM{i}",
                    'Date_debut_validite': (aujourdhui - timedelta(days=365 * 2)).strftime('%Y-%m-%d'),
                    'Date_fin_validite': '',  # Vide = actuel
                    'Actif': True,
                })

                # Ancien historique (si i pair)
                if i % 2 == 0:
                    data_znp.append({
                        'Employe_MATRICULE': matricule,
                        'Nom': f"ANCIENNOM{i}",
                        'Prenoms': f"ANCIENPRENOM{i}",
                        'Date_debut_validite': (aujourdhui - timedelta(days=365 * 4)).strftime('%Y-%m-%d'),
                        'Date_fin_validite': (aujourdhui - timedelta(days=365 * 2)).strftime('%Y-%m-%d'),
                        'Actif': False,
                    })

            df_znp = pd.DataFrame(data_znp)

            # Instructions
            instructions_np = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Nom': '1. Référence un matricule existant de ZY00',
                'Prenoms': '2. Un seul historique sans date_fin par employé',
                'Date_debut_validite': '3. Pas de chevauchement de dates',
                'Date_fin_validite': '4. Laisser vide pour historique actuel',
                'Actif': '5. Actif=True si pas de date_fin'
            }])

            df_znp = pd.concat([instructions_np, df_znp], ignore_index=True)
            df_znp.to_excel(writer, sheet_name='ZYNP_HistoriqueNoms', index=False)

            # ==============================================
            # FEUILLE 3: ZYCO_Contrats
            # ==============================================
            self.stdout.write("📋 Création feuille ZYCO_Contrats...")

            data_zyco = []
            types_contrat = ['CDI', 'CDD', 'STAGE', 'ALTERNANCE', 'APPRENTISSAGE']

            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"
                type_contrat = random.choice(types_contrat)

                # Contrat actuel
                date_debut = aujourdhui - timedelta(days=random.randint(0, 365))

                contrat_data = {
                    'Employe_MATRICULE': matricule,
                    'Type_contrat': type_contrat,
                    'Date_debut': date_debut.strftime('%Y-%m-%d'),
                    'Date_fin': '',  # Vide pour CDI ou contrat actuel
                    'Actif': True,
                }

                # Pour CDD, ajouter une date de fin
                if type_contrat == 'CDD':
                    contrat_data['Date_fin'] = (date_debut + timedelta(days=180)).strftime('%Y-%m-%d')

                data_zyco.append(contrat_data)

                # Ancien contrat (pour certains)
                if i % 3 == 0:
                    data_zyco.append({
                        'Employe_MATRICULE': matricule,
                        'Type_contrat': 'CDD',
                        'Date_debut': (date_debut - timedelta(days=365)).strftime('%Y-%m-%d'),
                        'Date_fin': (date_debut - timedelta(days=180)).strftime('%Y-%m-%d'),
                        'Actif': False,
                    })

            df_zyco = pd.DataFrame(data_zyco)

            # Instructions
            instructions_co = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Type_contrat': 'CDI, CDD, STAGE, ALTERNANCE, APPRENTISSAGE',
                'Date_debut': '1. Un seul contrat actif (sans date_fin) par employé',
                'Date_fin': '2. Laisser vide pour contrat actuel',
                'Actif': '3. Actif=True si pas de date_fin'
            }])

            # CORRECTION ICI : Utiliser df_zyco au lieu de data_zyco
            df_zyco_with_instructions = pd.concat([instructions_co, df_zyco], ignore_index=True)
            df_zyco_with_instructions.to_excel(writer, sheet_name='ZYCO_Contrats', index=False)

            # ==============================================
            # FEUILLE 4: ZYTE_Telephones
            # ==============================================
            self.stdout.write("📋 Création feuille ZYTE_Telephones...")

            data_zyte = []
            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"

                # Téléphone principal actuel
                data_zyte.append({
                    'Employe_MATRICULE': matricule,
                    'Numero': f"+336{12345678 + i}",
                    'Date_debut_validite': (aujourdhui - timedelta(days=180)).strftime('%Y-%m-%d'),
                    'Date_fin_validite': '',  # Vide = actuel
                    'Actif': True,
                })

                # Ancien téléphone (pour certains)
                if i % 4 == 0:
                    data_zyte.append({
                        'Employe_MATRICULE': matricule,
                        'Numero': f"+336{98765432 + i}",
                        'Date_debut_validite': (aujourdhui - timedelta(days=365)).strftime('%Y-%m-%d'),
                        'Date_fin_validite': (aujourdhui - timedelta(days=180)).strftime('%Y-%m-%d'),
                        'Actif': False,
                    })

            df_zyte = pd.DataFrame(data_zyte)

            # Instructions
            instructions_te = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Numero': 'Format international: +33612345678',
                'Date_debut_validite': '1. Pas de chevauchement de dates',
                'Date_fin_validite': '2. Laisser vide pour téléphone actuel',
                'Actif': '3. Actif=True si pas de date_fin'
            }])

            df_zyte = pd.concat([instructions_te, df_zyte], ignore_index=True)
            df_zyte.to_excel(writer, sheet_name='ZYTE_Telephones', index=False)

            # ==============================================
            # FEUILLE 5: ZYME_Emails
            # ==============================================
            self.stdout.write("📋 Création feuille ZYME_Emails...")

            data_zyme = []
            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"

                # Email principal actuel
                data_zyme.append({
                    'Employe_MATRICULE': matricule,
                    'Email': f"employe{i}@entreprise.com",
                    'Date_debut_validite': aujourdhui.strftime('%Y-%m-%d'),
                    'Date_fin_validite': '',  # Vide = actuel
                    'Actif': True,
                })

                # Ancien email (pour certains)
                if i % 5 == 0:
                    data_zyme.append({
                        'Employe_MATRICULE': matricule,
                        'Email': f"ancien{i}@ancienne-entreprise.com",
                        'Date_debut_validite': (aujourdhui - timedelta(days=365)).strftime('%Y-%m-%d'),
                        'Date_fin_validite': (aujourdhui - timedelta(days=30)).strftime('%Y-%m-%d'),
                        'Actif': False,
                    })

            df_zyme = pd.DataFrame(data_zyme)

            # Instructions
            instructions_me = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Email': 'Format valide: nom@domaine.com',
                'Date_debut_validite': '1. Pas de chevauchement de dates',
                'Date_fin_validite': '2. Laisser vide pour email actuel',
                'Actif': '3. Actif=True si pas de date_fin'
            }])

            df_zyme = pd.concat([instructions_me, df_zyme], ignore_index=True)
            df_zyme.to_excel(writer, sheet_name='ZYME_Emails', index=False)

            # ==============================================
            # FEUILLE 6: ZYAF_Affectations
            # ==============================================
            self.stdout.write("📋 Création feuille ZYAF_Affectations...")

            data_zyaf = []
            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"
                poste_code = postes_codes[i % len(postes_codes)]
                departement_code = departements_codes[i % len(departements_codes)]

                # Affectation actuelle
                data_zyaf.append({
                    'Employe_MATRICULE': matricule,
                    'Poste_CODE': poste_code,
                    'DEPARTEMENT_CODE': departement_code,  # Ajout du département
                    'Date_debut': (aujourdhui - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'Date_fin': '',  # Vide = affectation actuelle
                    'Actif': True,
                })

                # Ancienne affectation (pour certains)
                if i % 3 == 0:
                    data_zyaf.append({
                        'Employe_MATRICULE': matricule,
                        'Poste_CODE': postes_codes[(i + 1) % len(postes_codes)],
                        'DEPARTEMENT_CODE': departements_codes[(i + 1) % len(departements_codes)],
                        'Date_debut': (aujourdhui - timedelta(days=365)).strftime('%Y-%m-%d'),
                        'Date_fin': (aujourdhui - timedelta(days=180)).strftime('%Y-%m-%d'),
                        'Actif': False,
                    })

            df_zyaf = pd.DataFrame(data_zyaf)

            # Instructions
            instructions_af = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Poste_CODE': '1. Code de poste existant dans ZDPO',
                'DEPARTEMENT_CODE': '2. Code de département existant dans ZDDE',
                'Date_debut': '3. Une seule affectation active par employé',
                'Date_fin': '4. Laisser vide pour affectation actuelle',
                'Actif': '5. Actif=True si pas de date_fin'
            }])

            df_zyaf = pd.concat([instructions_af, df_zyaf], ignore_index=True)
            df_zyaf.to_excel(writer, sheet_name='ZYAF_Affectations', index=False)

            # ==============================================
            # FEUILLE 7: ZYAD_Adresses
            # ==============================================
            self.stdout.write("📋 Création feuille ZYAD_Adresses...")

            data_zyad = []
            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"
                ville = random.choice(villes_france)
                code_postal = f"{75000 + (i % 20) * 100}"

                # Adresse principale actuelle
                data_zyad.append({
                    'Employe_MATRICULE': matricule,
                    'Type_adresse': 'PRINCIPALE',
                    'Rue': f"{i * 10} Rue de l'Exemple",
                    'Complement': f"Appartement {i}A" if i % 2 == 0 else '',
                    'Ville': ville,
                    'Pays': 'FRANCE',
                    'Code_postal': code_postal,
                    'Date_debut': (aujourdhui - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
                    'Date_fin': '',  # Vide = adresse actuelle
                    'Actif': True,
                })

                # Adresse secondaire (pour certains)
                if i % 4 == 0:
                    data_zyad.append({
                        'Employe_MATRICULE': matricule,
                        'Type_adresse': 'SECONDAIRE',
                        'Rue': f"{i * 5} Avenue Secondaire",
                        'Complement': '',
                        'Ville': random.choice(villes_france),
                        'Pays': 'FRANCE',
                        'Code_postal': f"{13000 + (i % 10) * 100}",
                        'Date_debut': (aujourdhui - timedelta(days=90)).strftime('%Y-%m-%d'),
                        'Date_fin': '',  # Vide = actuelle
                        'Actif': True,
                    })

            df_zyad = pd.DataFrame(data_zyad)

            # Instructions
            instructions_ad = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Type_adresse': 'PRINCIPALE ou SECONDAIRE',
                'Rue': '1. Une seule adresse PRINCIPALE active par employé',
                'Complement': '2. Optionnel',
                'Ville': '3. Première lettre majuscule automatique',
                'Pays': '4. En majuscules automatiquement',
                'Code_postal': '5. Format: 75000',
                'Date_debut': '6. Pour PRINCIPALE: pas de date_fin = active',
                'Date_fin': '7. Laisser vide pour adresse actuelle',
                'Actif': '8. Actif=True si pas de date_fin'
            }])

            df_zyad = pd.concat([instructions_ad, df_zyad], ignore_index=True)
            df_zyad.to_excel(writer, sheet_name='ZYAD_Adresses', index=False)

            # ==============================================
            # FEUILLE 8: ZYFA_Famille (Personnes à charge)
            # ==============================================
            self.stdout.write("📋 Création feuille ZYFA_Famille...")

            data_zyfa = []
            for i in range(1, min(nombre, 8) + 1):  # Famille pour 8 employés max
                matricule = f"MT{i:06d}"

                # Enfant
                data_zyfa.append({
                    'Employe_MATRICULE': matricule,
                    'Personne_charge': 'ENFANT',
                    'Nom': f"NOM{i}",
                    'Prenom': f"Enfant{i}",
                    'Sexe': 'M' if i % 2 == 0 else 'F',
                    'Date_naissance': (aujourdhui - timedelta(days=365 * random.randint(1, 10))).strftime('%Y-%m-%d'),
                    'Date_debut_prise_charge': (aujourdhui - timedelta(days=365 * random.randint(1, 10))).strftime(
                        '%Y-%m-%d'),
                    'Date_fin_prise_charge': '',  # Vide = prise en charge actuelle
                    'Actif': True,
                })

                # Conjoint (pour certains)
                if i % 3 == 0:
                    data_zyfa.append({
                        'Employe_MATRICULE': matricule,
                        'Personne_charge': 'CONJOINT',
                        'Nom': f"NOM{i}",
                        'Prenom': f"Conjoint{i}",
                        'Sexe': 'F' if i % 2 == 0 else 'M',
                        'Date_naissance': (aujourdhui - timedelta(days=365 * random.randint(25, 40))).strftime(
                            '%Y-%m-%d'),
                        'Date_debut_prise_charge': (aujourdhui - timedelta(days=365 * random.randint(1, 5))).strftime(
                            '%Y-%m-%d'),
                        'Date_fin_prise_charge': '',  # Vide = actuelle
                        'Actif': True,
                    })

            df_zyfa = pd.DataFrame(data_zyfa)

            # Instructions
            instructions_fa = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Personne_charge': 'ENFANT, CONJOINT, PARENT, AUTRE',
                'Nom': '1. En majuscules automatiquement',
                'Prenom': '2. Première lettre majuscule automatique',
                'Sexe': 'M ou F',
                'Date_naissance': '3. Doit être dans le passé',
                'Date_debut_prise_charge': '4. Pour ENFANT = date_naissance si vide',
                'Date_fin_prise_charge': '5. Laisser vide pour prise en charge actuelle',
                'Actif': '6. Actif=True si pas de date_fin'
            }])

            df_zyfa = pd.concat([instructions_fa, df_zyfa], ignore_index=True)
            df_zyfa.to_excel(writer, sheet_name='ZYFA_Famille', index=False)

            # ==============================================
            # FEUILLE 9: ZYPP_PersonnesPrevenir
            # ==============================================
            self.stdout.write("📋 Création feuille ZYPP_PersonnesPrevenir...")

            data_zypp = []
            liens_parente = ['CONJOINT', 'PARENT', 'ENFANT', 'FRERE_SOEUR', 'AMI', 'AUTRE']

            for i in range(1, nombre + 1):
                matricule = f"MT{i:06d}"

                # Contact principal (priorité 1)
                data_zypp.append({
                    'Employe_MATRICULE': matricule,
                    'Nom': f"NOM{i}",
                    'Prenom': f"ContactPrincipal{i}",
                    'Lien_parente': random.choice(liens_parente),
                    'Telephone_principal': f"+336{98765432 + i}",
                    'Telephone_secondaire': f"+337{12345678 + i}" if i % 2 == 0 else '',
                    'Email': f"contact{i}@email.com",
                    'Adresse': f"{i * 10} Rue des Contacts, {75000 + (i % 20) * 100} Paris",
                    'Ordre_priorite': 1,
                    'Date_debut_validite': (aujourdhui - timedelta(days=180)).strftime('%Y-%m-%d'),
                    'Date_fin_validite': '',  # Vide = actuel
                    'Actif': True,
                })

                # Contact secondaire (priorité 2) pour certains
                if i % 2 == 0:
                    data_zypp.append({
                        'Employe_MATRICULE': matricule,
                        'Nom': f"AUTRENOM{i}",
                        'Prenom': f"ContactSecondaire{i}",
                        'Lien_parente': random.choice(liens_parente),
                        'Telephone_principal': f"+336{87654321 + i}",
                        'Telephone_secondaire': '',
                        'Email': f"secondaire{i}@email.com",
                        'Adresse': f"{i * 15} Avenue Secondaire, {69000 + (i % 10) * 100} Lyon",
                        'Ordre_priorite': 2,
                        'Date_debut_validite': (aujourdhui - timedelta(days=90)).strftime('%Y-%m-%d'),
                        'Date_fin_validite': '',  # Vide = actuel
                        'Actif': True,
                    })

            df_zypp = pd.DataFrame(data_zypp)

            # Instructions
            instructions_pp = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Nom': '1. En majuscules automatiquement',
                'Prenom': '2. Première lettre majuscule automatique',
                'Lien_parente': 'CONJOINT, PARENT, ENFANT, FRERE_SOEUR, AMI, AUTRE',
                'Telephone_principal': '3. Format: +33612345678',
                'Telephone_secondaire': '4. Optionnel, différent du principal',
                'Email': '5. Optionnel',
                'Adresse': '6. Optionnel',
                'Ordre_priorite': '7. 1=principal, 2=secondaire, 3=tertiaire',
                'Date_debut_validite': '8. Une seule personne par priorité active',
                'Date_fin_validite': '9. Laisser vide pour contact actuel',
                'Actif': '10. Actif=True si pas de date_fin'
            }])

            df_zypp = pd.concat([instructions_pp, df_zypp], ignore_index=True)
            df_zypp.to_excel(writer, sheet_name='ZYPP_PersonnesPrevenir', index=False)

            # ==============================================
            # FEUILLE 10: ZYIB_IdentiteBancaire
            # ==============================================
            self.stdout.write("📋 Création feuille ZYIB_IdentiteBancaire...")

            data_zyib = []
            for i in range(1, min(nombre, 6) + 1):  # RIB pour 6 employés max
                matricule = f"MT{i:06d}"

                data_zyib.append({
                    'Employe_MATRICULE': matricule,
                    'Titulaire_compte': f"NOM{i} PRENOM{i}",
                    'Nom_banque': random.choice(
                        ['BNP PARIBAS', 'SOCIETE GENERALE', 'CREDIT AGRICOLE', 'LA BANQUE POSTALE']),
                    'Code_banque': f"{10000 + i:05d}"[:5],
                    'Code_guichet': f"{20000 + i:05d}"[:5],
                    'Numero_compte': f"1234567890{i:01d}"[:11],
                    'Cle_rib': f"{10 + (i % 90):02d}",
                    'IBAN': f"FR76{10000 + i:04d}12345678901234567"[:27],
                    'BIC': random.choice(['BNPAFRPP', 'SOGEFRPP', 'AGRIFRPP', 'PSSTFRPP']),
                    'Type_compte': random.choice(['COURANT', 'EPARGNE', 'JOINT']),
                    'Domiciliation': f"Agence {random.choice(['Paris', 'Lyon', 'Marseille'])} Centre",
                    'Date_ouverture': (aujourdhui - timedelta(days=365 * random.randint(1, 5))).strftime('%Y-%m-%d'),
                    'Actif': True,
                })

            df_zyib = pd.DataFrame(data_zyib)

            # Instructions
            instructions_ib = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Titulaire_compte': '1. En majuscules',
                'Nom_banque': '2. En majuscules',
                'Code_banque': '3. 5 chiffres exactement',
                'Code_guichet': '4. 5 chiffres exactement',
                'Numero_compte': '5. 11 caractères exactement',
                'Cle_rib': '6. 2 chiffres exactement',
                'IBAN': '7. Optionnel, max 34 caractères',
                'BIC': '8. Optionnel, 8 ou 11 caractères',
                'Type_compte': 'COURANT, EPARGNE ou JOINT',
                'Domiciliation': '9. Optionnel',
                'Date_ouverture': '10. Optionnel',
                'Actif': '11. Un seul RIB actif par employé'
            }])

            df_zyib = pd.concat([instructions_ib, df_zyib], ignore_index=True)
            df_zyib.to_excel(writer, sheet_name='ZYIB_IdentiteBancaire', index=False)

            # ==============================================
            # FEUILLE 11: ZYRE_RolesEmployes
            # ==============================================
            self.stdout.write("📋 Création feuille ZYRE_RolesEmployes...")

            data_zyre = []
            for i in range(1, min(nombre, 5) + 1):  # Rôles pour 5 employés max
                matricule = f"MT{i:06d}"
                role_code = roles_codes[i % len(roles_codes)]

                data_zyre.append({
                    'Employe_MATRICULE': matricule,
                    'Role_CODE': role_code,
                    'Date_debut': (aujourdhui - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'Date_fin': '',  # Vide = rôle actuel
                    'Actif': True,
                    'Commentaire': f'Rôle {role_code} attribué',
                })

            df_zyre = pd.DataFrame(data_zyre)

            # Instructions
            instructions_re = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Role_CODE': '1. Code de rôle existant dans ZYRO',
                'Date_debut': '2. Un seul rôle actif par combinaison employé/rôle',
                'Date_fin': '3. Laisser vide pour rôle actuel',
                'Actif': '4. Actif=True si pas de date_fin',
                'Commentaire': '5. Optionnel'
            }])

            df_zyre = pd.concat([instructions_re, df_zyre], ignore_index=True)
            df_zyre.to_excel(writer, sheet_name='ZYRE_RolesEmployes', index=False)

            # ==============================================
            # FEUILLE 12: ZYDO_Documents (optionnel)
            # ==============================================
            self.stdout.write("📋 Création feuille ZYDO_Documents...")

            data_zydo = []
            types_document = ['CV', 'LETTRE_MOTIVATION', 'DIPLOME', 'CNI', 'RIB', 'CONTRAT_SIGNE']

            for i in range(1, min(nombre, 4) + 1):  # Documents pour 4 employés max
                matricule = f"MT{i:06d}"

                for doc_type in random.sample(types_document, random.randint(1, 3)):
                    data_zydo.append({
                        'Employe_MATRICULE': matricule,
                        'Type_document': doc_type,
                        'Description': f'Document {doc_type} de {matricule}',
                        'Fichier': f'document_{doc_type.lower()}_{matricule}.pdf',
                        'Actif': True,
                    })

            df_zydo = pd.DataFrame(data_zydo)

            # Instructions
            instructions_do = pd.DataFrame([{
                'Employe_MATRICULE': '⚠️ INSTRUCTIONS:',
                'Type_document': 'CV, LETTRE_MOTIVATION, DIPLOME, CNI, RIB, etc.',
                'Description': '1. Optionnel',
                'Fichier': '2. Nom du fichier uniquement',
                'Actif': '3. Généralement True'
            }])

            df_zydo = pd.concat([instructions_do, df_zydo], ignore_index=True)
            df_zydo.to_excel(writer, sheet_name='ZYDO_Documents', index=False)

            # ==============================================
            # FEUILLE 13: REGLES_VALIDATION
            # ==============================================
            self.stdout.write("📋 Création feuille REGLES_VALIDATION...")

            regles = [
                ("ZY00 - Employés", "Règles de validation pour la table principale"),
                ("", ""),
                ("Champs obligatoires",
                 "Nom, Prénoms, Date_naissance, Sexe, Type_id, Numero_id, Date_validite_id, Date_expiration_id"),
                ("Validation dates ID", "Date_expiration_id doit être > Date_validite_id"),
                ("Âge minimum", "16 ans minimum (calculé depuis Date_naissance)"),
                ("Matricule", "Commence par 'MT', généré automatiquement si vide"),
                ("Type dossier", "PRE (pré-embauche) ou SAL (salarié)"),
                ("Entreprise", "Obligatoire pour SAL, vide pour PRE"),
                ("Coefficient", "Entre 0 et 1 (ex: 1.00 = temps plein, 0.50 = mi-temps)"),
                ("", ""),
                ("ZYNP - Historique noms", "Règles spécifiques"),
                ("Unicité", "Un seul historique sans date_fin par employé"),
                ("Chevauchement", "Pas de chevauchement de dates entre historiques"),
                ("", ""),
                ("ZYCO - Contrats", "Règles spécifiques"),
                ("Unicité", "Un seul contrat actif (sans date_fin) par employé"),
                ("Chevauchement", "Pas de chevauchement de dates entre contrats"),
                ("", ""),
                ("ZYAD - Adresses", "Règles spécifiques"),
                ("Unicité", "Une seule adresse PRINCIPALE active par employé"),
                ("Format", "Ville: première lettre majuscule, Pays: majuscules"),
                ("", ""),
                ("ZYIB - Identité bancaire", "Règles spécifiques"),
                ("Unicité", "Un seul RIB actif par employé"),
                ("Format codes", "Code_banque: 5 chiffres, Code_guichet: 5 chiffres"),
                ("Format compte", "Numero_compte: 11 caractères, Cle_rib: 2 chiffres"),
                ("", ""),
                ("ZYPP - Personnes à prévenir", "Règles spécifiques"),
                ("Priorité", "Une seule personne par priorité (1, 2, 3) active"),
                ("Téléphones", "Secondaire différent du principal si renseigné"),
                ("", ""),
                ("FORMATS DE DATE", "Toutes les dates: YYYY-MM-DD"),
                ("FORMATS TELEPHONE", "+33612345678 (format international)"),
                ("FORMATS EMAIL", "nom@domaine.com"),
            ]

            data_regles = []
            for regle, description in regles:
                data_regles.append({
                    'Règle': regle,
                    'Description': description
                })

            df_regles = pd.DataFrame(data_regles)
            df_regles.to_excel(writer, sheet_name='REGLES_VALIDATION', index=False)

        self.stdout.write(self.style.SUCCESS(f"✅ Fichier généré avec succès : {output_path}"))
        self.stdout.write(f"📁 Emplacement : {output_path}")

        # Afficher le résumé
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 RÉSUMÉ DU TEMPLATE GÉNÉRÉ")
        self.stdout.write("=" * 60)
        self.stdout.write(f"📈 Nombre d'employés générés : {nombre}")
        self.stdout.write(f"📋 Nombre de feuilles : 13")
        self.stdout.write(f"📁 Taille du fichier : {os.path.getsize(output_path) / 1024:.1f} KB")
        self.stdout.write(f"🎯 Type de dossier : {dossier_type}")
        self.stdout.write(f"⚠️  Exemples avec erreurs : {'OUI' if with_errors else 'NON'}")

        # Lister les feuilles
        self.stdout.write("\n📑 FEUILLES DISPONIBLES :")
        feuilles = [
            "1. ZY00_Employes : Données principales des employés",
            "2. ZYNP_HistoriqueNoms : Historique des noms/prénoms",
            "3. ZYCO_Contrats : Contrats des employés",
            "4. ZYTE_Telephones : Numéros de téléphone",
            "5. ZYME_Emails : Adresses email",
            "6. ZYAF_Affectations : Affectations aux postes (avec département)",
            "7. ZYAD_Adresses : Adresses des employés",
            "8. ZYFA_Famille : Personnes à charge",
            "9. ZYPP_PersonnesPrevenir : Personnes à prévenir",
            "10. ZYIB_IdentiteBancaire : RIB/IBAN",
            "11. ZYRE_RolesEmployes : Rôles attribués",
            "12. ZYDO_Documents : Documents joints (optionnel)",
            "13. REGLES_VALIDATION : Règles de validation importantes"
        ]

        for feuille in feuilles:
            self.stdout.write(f"   {feuille}")

        self.stdout.write("\n🔑 CODES DE RÉFÉRENCE À UTILISER :")
        self.stdout.write(f"   Entreprises : {', '.join(entreprises_codes[:3])}")
        self.stdout.write(f"   Postes : {', '.join(postes_codes[:3])}")
        self.stdout.write(f"   Départements : {', '.join(departements_codes[:3])}")
        self.stdout.write(f"   Rôles : {', '.join(roles_codes[:3])}")

        self.stdout.write("\n⚠️  REMARQUES IMPORTANTES :")
        self.stdout.write("   1. Les champs avec '_' sont à ignorer (générés automatiquement)")
        self.stdout.write("   2. Les lignes d'instructions sont à supprimer avant import")
        self.stdout.write("   3. Vérifier les règles dans la feuille REGLES_VALIDATION")

        if with_errors:
            self.stdout.write(self.style.WARNING("\n⚠️  ATTENTION : Le fichier contient des exemples avec erreurs !"))
            self.stdout.write("   Ces lignes seront rejetées lors de l'importation.")
            self.stdout.write("   Elles servent à tester le système de validation.")

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("\n🚀 Le template est prêt pour l'importation !"))
        self.stdout.write("📝 Utilisation : Remplir les données, supprimer les lignes d'instructions,")
        self.stdout.write("                puis importer via votre système d'importation.")


# Générer 10 employés mixte (défaut)
#python manage.py generate_employee_template_v2

# Générer 20 pré-embauches
#python manage.py generate_employee_template_v2 --nombre 20 --type PRE

# Générer 15 salariés avec un nom spécifique
#python manage.py generate_employee_template_v2 --nombre 15 --type SAL --output salaires_template.xlsx

# Générer avec des exemples d'erreurs pour tester la validation
#python manage.py generate_employee_template_v2 --with-errors
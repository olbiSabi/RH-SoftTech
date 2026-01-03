# departement/management/commands/import_departements.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from departement.models import ZDDE
from datetime import datetime


class Command(BaseCommand):
    help = 'Importe les départements depuis un fichier Excel dans le dossier File/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            type=str,
            default='Departement.xlsx',
            help='Nom du fichier Excel dans File/ (défaut: Departement.xlsx)'
        )
        parser.add_argument(
            '--feuille',
            type=str,
            default='Feuil1',
            help='Nom de la feuille Excel (défaut: Feuil1)'
        )
        parser.add_argument(
            '--chemin',
            type=str,
            help='Chemin complet alternatif vers le fichier Excel'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Mettre à jour uniquement les départements existants'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler l\'importation sans sauvegarder'
        )
        parser.add_argument(
            '--show-diff',
            action='store_true',
            help='Afficher les différences entre données existantes et nouvelles'
        )

    def get_chemin_fichier(self, nom_fichier, chemin_personnalise=None):
        """Retourne le chemin complet du fichier"""
        if chemin_personnalise:
            # Utiliser le chemin personnalisé
            if os.path.exists(chemin_personnalise):
                return chemin_personnalise
            else:
                raise FileNotFoundError(f"Chemin personnalisé non trouvé: {chemin_personnalise}")

        # Chercher dans plusieurs emplacements possibles
        emplacements = [
            os.path.join('File', nom_fichier),  # File/ à la racine
            os.path.join(settings.BASE_DIR, 'File', nom_fichier),  # File/ dans BASE_DIR
            os.path.join('..', 'File', nom_fichier),  # File/ un niveau au-dessus
        ]

        for chemin in emplacements:
            if os.path.exists(chemin):
                return chemin

        # Si non trouvé, lister les fichiers disponibles
        fichiers_disponibles = []
        for emplacement in emplacements:
            dossier = os.path.dirname(emplacement)
            if os.path.exists(dossier):
                fichiers_disponibles.extend(os.listdir(dossier))

        raise FileNotFoundError(
            f"Fichier '{nom_fichier}' non trouvé dans File/. "
            f"Fichiers disponibles: {', '.join(fichiers_disponibles) if fichiers_disponibles else 'aucun'}"
        )

    def comparer_donnees(self, existant, nouvelles_donnees):
        """Compare les données existantes avec les nouvelles et retourne les différences"""
        differences = []

        champs = ['LIBELLE', 'STATUT', 'DATEDEB', 'DATEFIN']

        for champ in champs:
            valeur_existante = getattr(existant, champ)
            valeur_nouvelle = nouvelles_donnees.get(champ)

            # Gestion spéciale pour les dates None
            if champ in ['DATEDEB', 'DATEFIN']:
                if valeur_existante and valeur_nouvelle:
                    if valeur_existante != valeur_nouvelle:
                        differences.append(f"{champ}: {valeur_existante} → {valeur_nouvelle}")
                elif valeur_existante and not valeur_nouvelle:
                    differences.append(f"{champ}: {valeur_existante} → (vide)")
                elif not valeur_existante and valeur_nouvelle:
                    differences.append(f"{champ}: (vide) → {valeur_nouvelle}")
            # Gestion pour les booléens
            elif champ == 'STATUT':
                if valeur_existante != valeur_nouvelle:
                    statut_old = "ACTIF" if valeur_existante else "INACTIF"
                    statut_new = "ACTIF" if valeur_nouvelle else "INACTIF"
                    differences.append(f"{champ}: {statut_old} → {statut_new}")
            # Gestion pour les strings
            else:
                if valeur_existante != valeur_nouvelle:
                    differences.append(f"{champ}: '{valeur_existante}' → '{valeur_nouvelle}'")

        return differences

    def afficher_info_existant(self, departement, niveau="INFO"):
        """Affiche les informations d'un département existant"""
        if niveau == "INFO":
            style = self.style.SUCCESS
        else:
            style = self.style.WARNING

        self.stdout.write(style(f"    📍 Code: {departement.CODE}"))
        self.stdout.write(style(f"    📝 Libellé: {departement.LIBELLE}"))
        self.stdout.write(style(f"    🔧 Statut: {'ACTIF' if departement.STATUT else 'INACTIF'}"))
        self.stdout.write(style(f"    📅 Date début: {departement.DATEDEB}"))

        if departement.DATEFIN:
            self.stdout.write(style(f"    📅 Date fin: {departement.DATEFIN}"))
        else:
            self.stdout.write(style("    📅 Date fin: (Non définie)"))

        self.stdout.write(style(f"    🆔 ID: {departement.id}"))

    def handle(self, *args, **options):
        nom_fichier = options['fichier']
        feuille = options['feuille']
        chemin_personnalise = options['chemin']
        update_only = options['update']
        dry_run = options['dry_run']
        show_diff = options['show_diff']
        verbosity = options['verbosity']

        try:
            # Obtenir le chemin complet
            chemin_complet = self.get_chemin_fichier(nom_fichier, chemin_personnalise)

            if verbosity >= 1:
                self.stdout.write(self.style.SUCCESS(
                    f"📁 Chemin du fichier: {chemin_complet}"
                ))

            self.stdout.write(self.style.SUCCESS(
                f"🚀 Début de l'importation depuis '{nom_fichier}' (feuille: '{feuille}')..."
            ))

            if dry_run:
                self.stdout.write(self.style.WARNING("⚠️ Mode simulation activé - aucune donnée ne sera sauvegardée"))

            # Lire le fichier Excel
            df = pd.read_excel(chemin_complet, sheet_name=feuille, dtype=str)

            # Normaliser les noms de colonnes
            df.columns = df.columns.str.upper().str.strip()

            if verbosity >= 1:
                self.stdout.write(f"📋 Colonnes détectées: {', '.join(df.columns)}")
                self.stdout.write(f"📊 Nombre de lignes: {len(df)}")

            # Vérifier les colonnes requises
            colonnes_requises = ['CODE', 'LIBELLE', 'STATUT', 'DATEDEB']
            colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]

            if colonnes_manquantes:
                raise ValueError(
                    f"Colonnes requises manquantes: {', '.join(colonnes_manquantes)}\n"
                    f"Colonnes disponibles: {', '.join(df.columns)}"
                )

            total = 0
            succes = 0
            echecs = 0
            avertissements = 0
            deja_existants = 0
            mis_a_jour = 0
            crees = 0

            # Traiter chaque ligne
            for index, row in df.iterrows():
                total += 1
                ligne_num = index + 2

                try:
                    # Afficher le traitement si verbosité élevée
                    if verbosity >= 2:
                        self.stdout.write(f"\n--- Traitement ligne {ligne_num} ---")

                    # Nettoyage des données
                    code = str(row['CODE']).strip().upper() if pd.notna(row['CODE']) else ''
                    libelle = str(row['LIBELLE']).strip() if pd.notna(row['LIBELLE']) else ''

                    # Validation du code
                    if not code:
                        raise ValidationError("Le code est vide")

                    if len(code) != 3:
                        raise ValidationError(
                            f"Le code '{code}' doit contenir exactement 3 caractères (actuel: {len(code)})")

                    if not code.isalpha():
                        raise ValidationError(f"Le code '{code}' ne doit contenir que des lettres")

                    # Validation du libellé
                    if not libelle:
                        raise ValidationError("Le libellé est vide")

                    # Capitaliser le libellé
                    libelle = libelle[0].upper() + libelle[1:] if len(libelle) > 0 else libelle

                    # Gestion du statut
                    statut_value = str(row['STATUT']).strip().upper() if pd.notna(row['STATUT']) else 'TRUE'
                    statut = statut_value in ['TRUE', '1', 'OUI', 'YES', 'VRAI', 'ACTIF', 'ACTIVE']

                    # Gestion de la date de début
                    if pd.isna(row['DATEDEB']) or str(row['DATEDEB']).strip() == '':
                        datedeb = timezone.now().date()
                        if verbosity >= 2:
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: DATEDEB vide, utilisation de la date actuelle"
                            ))
                            avertissements += 1
                    else:
                        try:
                            datedeb = pd.to_datetime(row['DATEDEB']).date()
                        except Exception as e:
                            datedeb = timezone.now().date()
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: Format DATEDEB invalide '{row['DATEDEB']}', utilisation date actuelle"
                            ))
                            avertissements += 1

                    # Gestion de la date de fin
                    datefin = None
                    if 'DATEFIN' in df.columns and pd.notna(row['DATEFIN']) and str(row['DATEFIN']).strip() != '':
                        try:
                            datefin = pd.to_datetime(row['DATEFIN']).date()
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: Format DATEFIN invalide '{row['DATEFIN']}', ignoré"
                            ))
                            avertissements += 1

                    # Validation cohérence des dates
                    if datefin and datefin <= datedeb:
                        raise ValidationError(
                            f"La date de fin ({datefin}) doit être postérieure à la date de début ({datedeb})"
                        )

                    # Préparer les nouvelles données
                    nouvelles_donnees = {
                        'LIBELLE': libelle,
                        'STATUT': statut,
                        'DATEDEB': datedeb,
                        'DATEFIN': datefin,
                    }

                    # Vérifier si le département existe
                    departement_existant = ZDDE.objects.filter(CODE=code).first()

                    if departement_existant:
                        deja_existants += 1

                        # Afficher les informations du département existant
                        self.stdout.write(self.style.WARNING(
                            f"\n⚠️ Ligne {ligne_num}: Département {code} EXISTE DÉJÀ"
                        ))

                        # Afficher les informations détaillées
                        self.stdout.write(self.style.NOTICE("📋 INFORMATIONS EXISTANTES:"))
                        self.afficher_info_existant(departement_existant)

                        # Afficher les nouvelles données
                        self.stdout.write(self.style.NOTICE("🆕 DONNÉES DU FICHIER:"))
                        self.stdout.write(self.style.NOTICE(f"    📝 Libellé: {libelle}"))
                        self.stdout.write(self.style.NOTICE(f"    🔧 Statut: {'ACTIF' if statut else 'INACTIF'}"))
                        self.stdout.write(self.style.NOTICE(f"    📅 Date début: {datedeb}"))
                        if datefin:
                            self.stdout.write(self.style.NOTICE(f"    📅 Date fin: {datefin}"))
                        else:
                            self.stdout.write(self.style.NOTICE("    📅 Date fin: (Non définie)"))

                        # Comparer et afficher les différences si demandé
                        if show_diff or verbosity >= 2:
                            differences = self.comparer_donnees(departement_existant, nouvelles_donnees)
                            if differences:
                                self.stdout.write(self.style.WARNING("🔀 DIFFÉRENCES DÉTECTÉES:"))
                                for diff in differences:
                                    self.stdout.write(self.style.WARNING(f"    • {diff}"))
                            else:
                                self.stdout.write(self.style.SUCCESS("✅ Aucune différence détectée"))

                        if update_only:
                            # Mode update uniquement
                            if not dry_run:
                                # Vérifier si des modifications sont nécessaires
                                if any([
                                    departement_existant.LIBELLE != libelle,
                                    departement_existant.STATUT != statut,
                                    departement_existant.DATEDEB != datedeb,
                                    departement_existant.DATEFIN != datefin,
                                ]):
                                    departement_existant.LIBELLE = libelle
                                    departement_existant.STATUT = statut
                                    departement_existant.DATEDEB = datedeb
                                    departement_existant.DATEFIN = datefin
                                    departement_existant.save()
                                    action = "MIS À JOUR"
                                    mis_a_jour += 1
                                else:
                                    action = "DÉJÀ À JOUR (aucun changement)"
                            else:
                                action = "SIMULÉ mise à jour"
                        else:
                            # Mode normal (création + mise à jour)
                            if not dry_run:
                                # Utiliser update_or_create pour être sûr
                                obj, created = ZDDE.objects.update_or_create(
                                    CODE=code,
                                    defaults=nouvelles_donnees
                                )
                                if created:
                                    action = "CRÉÉ (remplacé)"
                                    crees += 1
                                else:
                                    action = "MIS À JOUR"
                                    mis_a_jour += 1
                            else:
                                action = "SIMULÉ création/mise à jour"
                    else:
                        # Nouveau département
                        if update_only:
                            self.stdout.write(self.style.NOTICE(
                                f"\nℹ️ Ligne {ligne_num}: Département {code} non trouvé (mode --update)"
                            ))
                            continue

                        if not dry_run:
                            ZDDE.objects.create(
                                CODE=code,
                                **nouvelles_donnees
                            )
                            action = "CRÉÉ"
                            crees += 1
                        else:
                            action = "SIMULÉ création"
                            crees += 1

                        self.stdout.write(self.style.SUCCESS(
                            f"\n✅ Ligne {ligne_num}: Nouveau département {code}"
                        ))
                        self.stdout.write(self.style.SUCCESS(f"    📝 Libellé: {libelle}"))
                        self.stdout.write(self.style.SUCCESS(f"    🔧 Statut: {'ACTIF' if statut else 'INACTIF'}"))

                    succes += 1

                    if verbosity >= 1 and not departement_existant:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Ligne {ligne_num}: {code} - '{libelle}' - {action}"
                        ))

                except ValidationError as e:
                    echecs += 1
                    self.stdout.write(self.style.ERROR(
                        f"\n❌ Ligne {ligne_num}: Erreur de validation - {e}"
                    ))
                except Exception as e:
                    echecs += 1
                    self.stdout.write(self.style.ERROR(
                        f"\n❌ Ligne {ligne_num}: Erreur inattendue - {str(e)}"
                    ))

            # Générer le rapport
            self.generer_rapport(succes, echecs, avertissements, total, deja_existants, mis_a_jour, crees, dry_run)

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"❌ {str(e)}"))
            self.stdout.write(self.style.ERROR("📁 Structure attendue: votre_projet/File/Departement.xlsx"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de l'importation: {str(e)}"))
            if verbosity >= 2:
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def generer_rapport(self, succes, echecs, avertissements, total, deja_existants, mis_a_jour, crees, dry_run):
        """Génère un rapport d'importation détaillé"""
        self.stdout.write("\n" + "=" * 70)

        if dry_run:
            self.stdout.write(self.style.WARNING("⏸️  IMPORTATION SIMULÉE - AUCUNE DONNÉE MODIFIÉE"))

        self.stdout.write(self.style.SUCCESS("📊 RAPPORT DÉTAILLÉ D'IMPORTATION"))
        self.stdout.write("=" * 70)

        self.stdout.write("📈 STATISTIQUES GLOBALES:")
        self.stdout.write(f"   ✅ Succès:              {succes:>4}")
        self.stdout.write(f"   ❌ Échecs:              {echecs:>4}")
        self.stdout.write(f"   ⚠️  Avertissements:      {avertissements:>4}")
        self.stdout.write(f"   📈 Total traité:        {total:>4}")

        if total > 0:
            taux_succes = (succes / total) * 100
            self.stdout.write(f"   📊 Taux de succès:      {taux_succes:>6.1f}%")

        self.stdout.write("\n🏢 RÉPARTITION DES DÉPARTEMENTS:")
        self.stdout.write(f"   🔁 Déjà existants:      {deja_existants:>4}")
        self.stdout.write(f"   ✨ Nouveaux créés:       {crees:>4}")
        self.stdout.write(f"   🔄 Mis à jour:          {mis_a_jour:>4}")

        if deja_existants > 0:
            taux_maj = (mis_a_jour / deja_existants * 100) if deja_existants > 0 else 0
            self.stdout.write(f"   📊 Taux de mise à jour: {taux_maj:>6.1f}%")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n💡 CONSEIL: Exécutez sans '--dry-run' pour appliquer les modifications"
            ))

        if echecs == 0 and succes > 0:
            self.stdout.write(self.style.SUCCESS("\n✨ Importation terminée avec succès !"))
        elif echecs > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {echecs} erreur(s) pendant l'importation"))
        else:
            self.stdout.write(self.style.WARNING("\nℹ️  Aucune donnée importée"))

        self.stdout.write("=" * 70)
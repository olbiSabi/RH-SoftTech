# departement/management/commands/import_postes.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from departement.models import ZDDE, ZDPO
from datetime import datetime


class Command(BaseCommand):
    help = 'Importe les postes depuis un fichier Excel dans le dossier File/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            type=str,
            default='poste.xlsx',
            help='Nom du fichier Excel dans File/ (défaut: poste.xlsx)'
        )
        parser.add_argument(
            '--feuille',
            type=str,
            default='Feuil1',
            help='Nom de la feuille Excel (défaut: Feuil1)'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Mettre à jour uniquement les postes existants'
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
        parser.add_argument(
            '--ignore-missing-dept',
            action='store_true',
            help='Ignorer les lignes avec département inexistant'
        )

    def get_chemin_fichier(self, nom_fichier):
        """Retourne le chemin complet du fichier"""
        # Chercher dans plusieurs emplacements possibles
        emplacements = [
            os.path.join('File', nom_fichier),
            os.path.join(settings.BASE_DIR, 'File', nom_fichier),
            os.path.join('..', 'File', nom_fichier),
            nom_fichier,
        ]

        for chemin in emplacements:
            if os.path.exists(chemin):
                return chemin

        raise FileNotFoundError(f"Fichier '{nom_fichier}' non trouvé")

    def comparer_donnees(self, existant, nouvelles_donnees):
        """Compare les données existantes avec les nouvelles"""
        differences = []

        # Comparer libellé
        if existant.LIBELLE != nouvelles_donnees['LIBELLE']:
            differences.append(f"LIBELLE: '{existant.LIBELLE}' → '{nouvelles_donnees['LIBELLE']}'")

        # Comparer département
        if existant.DEPARTEMENT != nouvelles_donnees['DEPARTEMENT']:
            old_dept = existant.DEPARTEMENT.CODE if existant.DEPARTEMENT else "Aucun"
            new_dept = nouvelles_donnees['DEPARTEMENT'].CODE if nouvelles_donnees['DEPARTEMENT'] else "Aucun"
            differences.append(f"DÉPARTEMENT: {old_dept} → {new_dept}")

        # Comparer statut
        if existant.STATUT != nouvelles_donnees['STATUT']:
            old_statut = "ACTIF" if existant.STATUT else "INACTIF"
            new_statut = "ACTIF" if nouvelles_donnees['STATUT'] else "INACTIF"
            differences.append(f"STATUT: {old_statut} → {new_statut}")

        # Comparer dates
        if existant.DATEDEB != nouvelles_donnees['DATEDEB']:
            differences.append(f"DATEDEB: {existant.DATEDEB} → {nouvelles_donnees['DATEDEB']}")

        if existant.DATEFIN != nouvelles_donnees['DATEFIN']:
            old_fin = existant.DATEFIN if existant.DATEFIN else "Non définie"
            new_fin = nouvelles_donnees['DATEFIN'] if nouvelles_donnees['DATEFIN'] else "Non définie"
            differences.append(f"DATEFIN: {old_fin} → {new_fin}")

        return differences

    def afficher_info_existant(self, poste):
        """Affiche les informations d'un poste existant"""
        self.stdout.write(self.style.WARNING("📋 INFORMATIONS EXISTANTES:"))
        self.stdout.write(f"    📍 Code: {poste.CODE}")
        self.stdout.write(f"    📝 Libellé: {poste.LIBELLE}")
        if poste.DEPARTEMENT:
            self.stdout.write(f"    🏢 Département: {poste.DEPARTEMENT.CODE} - {poste.DEPARTEMENT.LIBELLE}")
        else:
            self.stdout.write(f"    🏢 Département: Aucun")
        self.stdout.write(f"    🔧 Statut: {'ACTIF' if poste.STATUT else 'INACTIF'}")
        self.stdout.write(f"    📅 Date début: {poste.DATEDEB}")
        self.stdout.write(f"    📅 Date fin: {poste.DATEFIN if poste.DATEFIN else 'Non définie'}")

    def trouver_departement(self, code_departement, ligne_num, ignore_missing=False):
        """Trouve un département par son code"""
        if not code_departement or pd.isna(code_departement) or str(code_departement).strip() == '':
            if ignore_missing:
                return None
            else:
                raise ValidationError("Code département vide")

        code_dep = str(code_departement).strip().upper()

        try:
            return ZDDE.objects.get(CODE=code_dep)
        except ZDDE.DoesNotExist:
            if ignore_missing:
                return None
            else:
                raise ValidationError(f"Département '{code_dep}' non trouvé")

    def handle(self, *args, **options):
        nom_fichier = options['fichier']
        feuille = options['feuille']
        update_only = options['update']
        dry_run = options['dry_run']
        show_diff = options['show_diff']
        ignore_missing = options['ignore_missing_dept']
        verbosity = options['verbosity']

        try:
            # Obtenir le chemin complet
            chemin_complet = self.get_chemin_fichier(nom_fichier)

            self.stdout.write(self.style.SUCCESS(
                f"📁 Fichier trouvé: {chemin_complet}"
            ))

            self.stdout.write(self.style.SUCCESS(
                f"🚀 Début de l'importation des postes depuis '{nom_fichier}'..."
            ))

            if dry_run:
                self.stdout.write(self.style.WARNING("⚠️ Mode simulation activé"))

            # Lire le fichier Excel
            df = pd.read_excel(chemin_complet, sheet_name=feuille, dtype=str)

            # Normaliser les noms de colonnes
            df.columns = df.columns.str.upper().str.strip()

            if verbosity >= 1:
                self.stdout.write(f"📋 Colonnes détectées: {', '.join(df.columns)}")
                self.stdout.write(f"📊 Nombre de lignes: {len(df)}")

            # Vérifier les colonnes requises
            colonnes_requises = ['CODE', 'LIBELLE', 'STATUT', 'DATEDEB', 'CODE_ZDDE']
            for col in colonnes_requises:
                if col not in df.columns:
                    raise ValueError(f"Colonne requise manquante: '{col}'")

            total = 0
            succes = 0
            echecs = 0
            avertissements = 0
            deja_existants = 0
            mis_a_jour = 0
            crees = 0
            departements_manquants = 0

            # Traiter chaque ligne
            for index, row in df.iterrows():
                total += 1
                ligne_num = index + 2

                try:
                    if verbosity >= 2:
                        self.stdout.write(f"\n--- Traitement ligne {ligne_num} ---")

                    # Nettoyage des données
                    code = str(row['CODE']).strip().upper() if pd.notna(row['CODE']) else ''
                    libelle = str(row['LIBELLE']).strip() if pd.notna(row['LIBELLE']) else ''
                    code_zdde = row.get('CODE_ZDDE')

                    # Validation du code
                    if not code:
                        raise ValidationError("Le code est vide")

                    if len(code) != 6:
                        raise ValidationError(f"Le code '{code}' doit contenir 6 caractères (actuel: {len(code)})")

                    if not code.isalnum():
                        raise ValidationError(f"Le code '{code}' ne doit contenir que lettres et chiffres")

                    # Validation du libellé
                    if not libelle:
                        raise ValidationError("Le libellé est vide")

                    # Capitaliser le libellé
                    libelle = libelle[0].upper() + libelle[1:] if len(libelle) > 0 else libelle

                    # Trouver le département
                    departement = self.trouver_departement(code_zdde, ligne_num, ignore_missing)

                    if departement is None and ignore_missing:
                        departements_manquants += 1
                        if verbosity >= 1:
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: Département '{code_zdde}' ignoré (option --ignore-missing-dept)"
                            ))
                        continue

                    # Gestion du statut
                    statut_value = str(row['STATUT']).strip().upper() if pd.notna(row['STATUT']) else 'TRUE'
                    statut = statut_value in ['TRUE', '1', 'OUI', 'YES', 'VRAI', 'ACTIF', 'ACTIVE']

                    # Gestion de la date de début
                    if pd.isna(row['DATEDEB']) or str(row['DATEDEB']).strip() == '':
                        datedeb = timezone.now().date()
                        if verbosity >= 2:
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: DATEDEB vide, utilisation date actuelle"
                            ))
                            avertissements += 1
                    else:
                        try:
                            datedeb = pd.to_datetime(row['DATEDEB']).date()
                        except Exception:
                            datedeb = timezone.now().date()
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: Format DATEDEB invalide, utilisation date actuelle"
                            ))
                            avertissements += 1

                    # Gestion de la date de fin
                    datefin = None
                    if 'DATEFIN' in df.columns and pd.notna(row['DATEFIN']) and str(row['DATEFIN']).strip() != '':
                        try:
                            datefin = pd.to_datetime(row['DATEFIN']).date()
                        except Exception:
                            self.stdout.write(self.style.WARNING(
                                f"Ligne {ligne_num}: Format DATEFIN invalide, ignoré"
                            ))
                            avertissements += 1

                    # Validation des dates
                    if datefin and datefin <= datedeb:
                        raise ValidationError(
                            f"Date fin ({datefin}) doit être après date début ({datedeb})"
                        )

                    # Préparer les nouvelles données
                    nouvelles_donnees = {
                        'LIBELLE': libelle,
                        'DEPARTEMENT': departement,
                        'STATUT': statut,
                        'DATEDEB': datedeb,
                        'DATEFIN': datefin,
                    }

                    # Vérifier si le poste existe
                    poste_existant = ZDPO.objects.filter(CODE=code).first()

                    if poste_existant:
                        deja_existants += 1

                        if verbosity >= 1:
                            self.stdout.write(self.style.WARNING(
                                f"\n⚠️ Ligne {ligne_num}: Poste {code} EXISTE DÉJÀ"
                            ))

                            if show_diff or verbosity >= 2:
                                # Afficher les informations existantes
                                self.afficher_info_existant(poste_existant)

                                # Afficher les nouvelles données
                                self.stdout.write(self.style.NOTICE("🆕 DONNÉES DU FICHIER:"))
                                self.stdout.write(f"    📝 Libellé: {libelle}")
                                self.stdout.write(f"    🏢 Département: {departement.CODE if departement else 'Aucun'}")
                                if departement:
                                    self.stdout.write(f"         ↳ {departement.LIBELLE}")
                                self.stdout.write(f"    🔧 Statut: {'ACTIF' if statut else 'INACTIF'}")
                                self.stdout.write(f"    📅 Date début: {datedeb}")
                                self.stdout.write(f"    📅 Date fin: {datefin if datefin else 'Non définie'}")

                                # Comparer les différences
                                differences = self.comparer_donnees(poste_existant, nouvelles_donnees)
                                if differences:
                                    self.stdout.write(self.style.WARNING("🔀 DIFFÉRENCES DÉTECTÉES:"))
                                    for diff in differences:
                                        self.stdout.write(f"    • {diff}")
                                else:
                                    self.stdout.write(self.style.SUCCESS("✅ Aucune différence"))

                        if update_only:
                            # Mode update uniquement
                            if not dry_run:
                                # Vérifier si des modifications sont nécessaires
                                modifications = False

                                if poste_existant.LIBELLE != libelle:
                                    poste_existant.LIBELLE = libelle
                                    modifications = True

                                if poste_existant.DEPARTEMENT != departement:
                                    poste_existant.DEPARTEMENT = departement
                                    modifications = True

                                if poste_existant.STATUT != statut:
                                    poste_existant.STATUT = statut
                                    modifications = True

                                if poste_existant.DATEDEB != datedeb:
                                    poste_existant.DATEDEB = datedeb
                                    modifications = True

                                if poste_existant.DATEFIN != datefin:
                                    poste_existant.DATEFIN = datefin
                                    modifications = True

                                if modifications:
                                    poste_existant.save()
                                    action = "MIS À JOUR"
                                    mis_a_jour += 1
                                else:
                                    action = "DÉJÀ À JOUR"
                            else:
                                action = "SIMULÉ (mise à jour)"
                        else:
                            # Mode normal
                            if not dry_run:
                                obj, created = ZDPO.objects.update_or_create(
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
                                action = "SIMULÉ (création/mise à jour)"
                    else:
                        # Nouveau poste
                        if update_only:
                            if verbosity >= 1:
                                self.stdout.write(self.style.NOTICE(
                                    f"Ligne {ligne_num}: Poste {code} non trouvé (mode --update)"
                                ))
                            continue

                        if not dry_run:
                            ZDPO.objects.create(
                                CODE=code,
                                **nouvelles_donnees
                            )
                            action = "CRÉÉ"
                            crees += 1
                        else:
                            action = "SIMULÉ (création)"
                            crees += 1

                        if verbosity >= 1:
                            self.stdout.write(self.style.SUCCESS(
                                f"\n✅ Ligne {ligne_num}: Nouveau poste {code}"
                            ))
                            self.stdout.write(f"    📝 Libellé: {libelle}")
                            self.stdout.write(f"    🏢 Département: {departement.CODE if departement else 'Aucun'}")

                    succes += 1

                    if verbosity >= 1 and not poste_existant:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Ligne {ligne_num}: {code} - {action}"
                        ))

                except ValidationError as e:
                    echecs += 1
                    self.stdout.write(self.style.ERROR(
                        f"\n❌ Ligne {ligne_num}: Validation - {e}"
                    ))
                except Exception as e:
                    echecs += 1
                    self.stdout.write(self.style.ERROR(
                        f"\n❌ Ligne {ligne_num}: Erreur - {str(e)}"
                    ))

            # Générer le rapport
            self.stdout.write("\n" + "=" * 70)

            if dry_run:
                self.stdout.write(self.style.WARNING("⏸️ IMPORTATION SIMULÉE"))

            self.stdout.write(self.style.SUCCESS("📊 RAPPORT D'IMPORTATION DES POSTES"))
            self.stdout.write("=" * 70)

            self.stdout.write("📈 STATISTIQUES:")
            self.stdout.write(f"   ✅ Succès:           {succes:>4}")
            self.stdout.write(f"   ❌ Échecs:           {echecs:>4}")
            self.stdout.write(f"   ⚠️  Avertissements:   {avertissements:>4}")
            if departements_manquants > 0:
                self.stdout.write(f"   🏢 Dépts ignorés:    {departements_manquants:>4}")
            self.stdout.write(f"   📈 Total traité:     {total:>4}")

            self.stdout.write("\n💼 RÉPARTITION:")
            self.stdout.write(f"   🔁 Déjà existants:   {deja_existants:>4}")
            self.stdout.write(f"   ✨ Nouveaux créés:    {crees:>4}")
            self.stdout.write(f"   🔄 Mis à jour:       {mis_a_jour:>4}")

            if total > 0:
                taux_succes = (succes / total) * 100
                self.stdout.write(f"   📊 Taux de succès:   {taux_succes:>6.1f}%")

            if dry_run:
                self.stdout.write(self.style.WARNING(
                    "\n💡 Exécutez sans '--dry-run' pour appliquer les modifications"
                ))

            if echecs == 0:
                self.stdout.write(self.style.SUCCESS("\n✨ Importation terminée avec succès !"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  {echecs} erreur(s) pendant l'importation"))

            self.stdout.write("=" * 70)

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"❌ {str(e)}"))
            self.stdout.write(self.style.ERROR("Placez le fichier dans le dossier File/"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur: {str(e)}"))
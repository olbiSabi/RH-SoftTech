# departement/management/commands/verifier_postes.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from departement.models import ZDDE


class Command(BaseCommand):
    help = 'Vérifie les références aux départements dans le fichier postes avant importation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            type=str,
            default='poste.xlsx',
            help='Nom du fichier Excel dans File/ (défaut: poste.xlsx)'
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

    def handle(self, *args, **options):
        fichier = options['fichier']

        try:
            chemin_fichier = self.get_chemin_fichier(fichier)

            # Lire le fichier
            df = pd.read_excel(chemin_fichier, dtype=str)

            # Normaliser les colonnes
            df.columns = df.columns.str.upper().str.strip()

            if 'CODE_ZDDE' not in df.columns:
                self.stdout.write(self.style.ERROR("Colonne CODE_ZDDE non trouvée"))
                return

            # Récupérer tous les codes de département du fichier
            codes_departements_fichier = df['CODE_ZDDE'].dropna().str.strip().str.upper().unique()

            # Récupérer les départements existants
            departements_existants = ZDDE.objects.filter(CODE__in=codes_departements_fichier)
            codes_departements_existants = set(departements_existants.values_list('CODE', flat=True))

            self.stdout.write(self.style.SUCCESS("🔍 VÉRIFICATION DES DÉPARTEMENTS"))
            self.stdout.write("=" * 50)
            self.stdout.write(f"📊 Total de codes uniques dans le fichier: {len(codes_departements_fichier)}")
            self.stdout.write(f"🏢 Départements trouvés en base: {len(codes_departements_existants)}")

            # Identifier les départements manquants
            departements_manquants = set(codes_departements_fichier) - codes_departements_existants

            if departements_manquants:
                self.stdout.write(self.style.ERROR(f"\n❌ DÉPARTEMENTS MANQUANTS ({len(departements_manquants)}):"))
                for code in sorted(departements_manquants):
                    self.stdout.write(f"   • {code}")

                # Compter les postes affectés
                postes_affectes = df[df['CODE_ZDDE'].str.strip().str.upper().isin(departements_manquants)]
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  {len(postes_affectes)} poste(s) concerné(s) par des départements manquants"
                ))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ Tous les départements référencés existent !"))

            self.stdout.write("\n📋 LISTE DES DÉPARTEMENTS RÉFÉRENCÉS:")
            for code in sorted(codes_departements_fichier):
                status = "✅" if code in codes_departements_existants else "❌"
                # Compter les postes pour ce département
                nb_postes = len(df[df['CODE_ZDDE'].str.strip().str.upper() == code])
                dept = ZDDE.objects.filter(CODE=code).first()
                libelle = f" - {dept.LIBELLE}" if dept else ""
                self.stdout.write(f"   {status} {code}{libelle} ({nb_postes} poste(s))")

            self.stdout.write("=" * 50)

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"❌ {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur: {str(e)}"))
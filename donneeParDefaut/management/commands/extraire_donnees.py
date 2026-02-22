# donneeParDefaut/management/commands/extraire_donnees.py
"""
Commande Django pour extraire les données de référence et les sauvegarder
en fichiers JSON pour le déploiement sur de nouveaux environnements.

Tables extraites :
    - ZDDE (Départements)
    - ZDPO (Postes)
    - TypeAbsence (Types d'absence)
    - NFCA (Catégories de frais)
    - ZYRO (Rôles)
    - GACCategorie (Catégories d'articles)

Usage:
    python manage.py extraire_donnees
    python manage.py extraire_donnees --tables ZDDE ZDPO
    python manage.py extraire_donnees --output /chemin/custom/
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_OUTPUT_DIR = Path(settings.BASE_DIR) / 'donneeParDefaut' / 'data'

TABLES_DISPONIBLES = ['ZDDE', 'ZDPO', 'TypeAbsence', 'NFCA', 'ZYRO', 'GACCategorie']


class Command(BaseCommand):
    help = 'Extrait les données de référence vers des fichiers JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables',
            nargs='+',
            choices=TABLES_DISPONIBLES,
            default=TABLES_DISPONIBLES,
            help='Tables à extraire (défaut: toutes)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=str(DEFAULT_OUTPUT_DIR),
            help='Dossier de sortie (défaut: donneeParDefaut/data/)'
        )

    def handle(self, *args, **options):
        tables = options['tables']
        output_dir = Path(options['output'])
        output_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("  EXTRACTION DES DONNEES DE REFERENCE")
        self.stdout.write(f"{'='*60}\n")

        extracteurs = {
            'ZDDE': self._extraire_zdde,
            'ZDPO': self._extraire_zdpo,
            'TypeAbsence': self._extraire_type_absence,
            'NFCA': self._extraire_nfca,
            'ZYRO': self._extraire_zyro,
            'GACCategorie': self._extraire_gac_categorie,
        }

        total = 0
        for table in tables:
            extracteur = extracteurs[table]
            data = extracteur()
            fichier = output_dir / f"{table.lower()}.json"

            with open(fichier, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            nb = len(data)
            total += nb
            self.stdout.write(self.style.SUCCESS(
                f"  {table:20s} : {nb:4d} enregistrement(s) -> {fichier.name}"
            ))

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  Total : {total} enregistrements extraits")
        self.stdout.write(f"  Dossier : {output_dir}")
        self.stdout.write(f"{'='*60}\n")

    def _extraire_zdde(self):
        from departement.models import ZDDE
        data = []
        for obj in ZDDE.objects.all().order_by('CODE'):
            data.append({
                'CODE': obj.CODE,
                'LIBELLE': obj.LIBELLE,
                'STATUT': obj.STATUT,
                'DATEDEB': obj.DATEDEB.isoformat() if obj.DATEDEB else None,
                'DATEFIN': obj.DATEFIN.isoformat() if obj.DATEFIN else None,
            })
        return data

    def _extraire_zdpo(self):
        from departement.models import ZDPO
        data = []
        for obj in ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE'):
            data.append({
                'CODE': obj.CODE,
                'LIBELLE': obj.LIBELLE,
                'DEPARTEMENT_CODE': obj.DEPARTEMENT.CODE,
                'STATUT': obj.STATUT,
                'DATEDEB': obj.DATEDEB.isoformat() if obj.DATEDEB else None,
                'DATEFIN': obj.DATEFIN.isoformat() if obj.DATEFIN else None,
            })
        return data

    def _extraire_type_absence(self):
        from absence.models import TypeAbsence
        data = []
        for obj in TypeAbsence.objects.all().order_by('ordre', 'code'):
            data.append({
                'code': obj.code,
                'libelle': obj.libelle,
                'categorie': obj.categorie,
                'paye': obj.paye,
                'decompte_solde': obj.decompte_solde,
                'justificatif_obligatoire': obj.justificatif_obligatoire,
                'couleur': obj.couleur,
                'ordre': obj.ordre,
                'actif': obj.actif,
            })
        return data

    def _extraire_nfca(self):
        from frais.models import NFCA
        data = []
        for obj in NFCA.objects.all().order_by('ORDRE', 'CODE'):
            data.append({
                'CODE': obj.CODE,
                'LIBELLE': obj.LIBELLE,
                'DESCRIPTION': obj.DESCRIPTION or '',
                'JUSTIFICATIF_OBLIGATOIRE': obj.JUSTIFICATIF_OBLIGATOIRE,
                'PLAFOND_DEFAUT': str(obj.PLAFOND_DEFAUT) if obj.PLAFOND_DEFAUT else None,
                'ICONE': obj.ICONE or '',
                'STATUT': obj.STATUT,
                'ORDRE': obj.ORDRE,
            })
        return data

    def _extraire_zyro(self):
        from employee.models import ZYRO
        data = []
        for obj in ZYRO.objects.all().order_by('CODE'):
            entry = {
                'CODE': obj.CODE,
                'LIBELLE': obj.LIBELLE,
                'DESCRIPTION': obj.DESCRIPTION or '',
                'PERMISSIONS_CUSTOM': obj.PERMISSIONS_CUSTOM or {},
                'actif': obj.actif,
            }
            # Sauvegarder le nom du groupe Django associé (pas l'ID)
            if obj.django_group:
                entry['django_group_name'] = obj.django_group.name
            else:
                entry['django_group_name'] = None
            data.append(entry)
        return data

    def _extraire_gac_categorie(self):
        from gestion_achats.models import GACCategorie
        data = []
        for obj in GACCategorie.objects.select_related('parent').all().order_by('code'):
            data.append({
                'code': obj.code,
                'nom': obj.nom,
                'description': obj.description or '',
                'parent_code': obj.parent.code if obj.parent else None,
                'ordre': obj.ordre,
            })
        return data

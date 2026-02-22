# donneeParDefaut/management/commands/charger_donnees.py
"""
Commande Django pour charger les données de référence par défaut
à partir des fichiers JSON extraits.

Utilisé lors du déploiement sur un nouvel environnement.

Tables chargées (dans l'ordre des dépendances) :
    1. ZDDE (Départements)
    2. ZDPO (Postes) - dépend de ZDDE
    3. TypeAbsence (Types d'absence)
    4. NFCA (Catégories de frais)
    5. ZYRO (Rôles) - crée les Groups Django associés
    6. GACCategorie (Catégories d'articles) - auto-référence parent

Usage:
    python manage.py charger_donnees
    python manage.py charger_donnees --tables ZDDE TypeAbsence
    python manage.py charger_donnees --dry-run
    python manage.py charger_donnees --force
"""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

DATA_DIR = Path(settings.BASE_DIR) / 'donneeParDefaut' / 'data'

# Ordre de chargement (respect des dépendances FK)
ORDRE_CHARGEMENT = ['ZDDE', 'ZDPO', 'TypeAbsence', 'NFCA', 'ZYRO', 'GACCategorie']


class Command(BaseCommand):
    help = 'Charge les données de référence par défaut depuis les fichiers JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables',
            nargs='+',
            choices=ORDRE_CHARGEMENT,
            default=ORDRE_CHARGEMENT,
            help='Tables à charger (défaut: toutes)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans écriture en base'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Met à jour les enregistrements existants au lieu de les ignorer'
        )
        parser.add_argument(
            '--input',
            type=str,
            default=str(DATA_DIR),
            help='Dossier source des fichiers JSON (défaut: donneeParDefaut/data/)'
        )

    def handle(self, *args, **options):
        tables = options['tables']
        dry_run = options['dry_run']
        force = options['force']
        data_dir = Path(options['input'])

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("  CHARGEMENT DES DONNEES DE REFERENCE")
        if dry_run:
            self.stdout.write(self.style.WARNING("  MODE SIMULATION"))
        if force:
            self.stdout.write(self.style.WARNING("  MODE FORCE (mise a jour)"))
        self.stdout.write(f"{'='*60}\n")

        chargeurs = {
            'ZDDE': self._charger_zdde,
            'ZDPO': self._charger_zdpo,
            'TypeAbsence': self._charger_type_absence,
            'NFCA': self._charger_nfca,
            'ZYRO': self._charger_zyro,
            'GACCategorie': self._charger_gac_categorie,
        }

        # Respecter l'ordre des dépendances
        tables_ordonnees = [t for t in ORDRE_CHARGEMENT if t in tables]

        resultats = {'crees': 0, 'existants': 0, 'mis_a_jour': 0, 'erreurs': 0}

        for table in tables_ordonnees:
            fichier = data_dir / f"{table.lower()}.json"

            if not fichier.exists():
                self.stdout.write(self.style.WARNING(
                    f"  {table:20s} : fichier {fichier.name} introuvable, ignore"
                ))
                continue

            with open(fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                self.stdout.write(f"  {table:20s} : aucune donnee")
                continue

            chargeur = chargeurs[table]
            stats = chargeur(data, dry_run, force)

            resultats['crees'] += stats['crees']
            resultats['existants'] += stats['existants']
            resultats['mis_a_jour'] += stats['mis_a_jour']
            resultats['erreurs'] += stats['erreurs']

            self._afficher_stats(table, stats)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("  RESUME")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"  Crees       : {resultats['crees']}"))
        self.stdout.write(f"  Existants   : {resultats['existants']}")
        if force:
            self.stdout.write(self.style.WARNING(f"  Mis a jour  : {resultats['mis_a_jour']}"))
        if resultats['erreurs']:
            self.stdout.write(self.style.ERROR(f"  Erreurs     : {resultats['erreurs']}"))
        self.stdout.write(f"{'='*60}\n")

    def _afficher_stats(self, table, stats):
        parts = [f"{stats['crees']} cree(s)"]
        if stats['existants']:
            parts.append(f"{stats['existants']} existant(s)")
        if stats['mis_a_jour']:
            parts.append(f"{stats['mis_a_jour']} maj")
        if stats['erreurs']:
            parts.append(f"{stats['erreurs']} erreur(s)")
        self.stdout.write(f"  {table:20s} : {', '.join(parts)}")

    def _stats(self):
        return {'crees': 0, 'existants': 0, 'mis_a_jour': 0, 'erreurs': 0}

    @transaction.atomic
    def _charger_zdde(self, data, dry_run, force):
        from departement.models import ZDDE
        stats = self._stats()

        for item in data:
            try:
                existing = ZDDE.objects.filter(CODE=item['CODE']).first()
                if existing:
                    if force and not dry_run:
                        existing.LIBELLE = item['LIBELLE']
                        existing.STATUT = item['STATUT']
                        if item.get('DATEDEB'):
                            existing.DATEDEB = date.fromisoformat(item['DATEDEB'])
                        if item.get('DATEFIN'):
                            existing.DATEFIN = date.fromisoformat(item['DATEFIN'])
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        kwargs = {
                            'CODE': item['CODE'],
                            'LIBELLE': item['LIBELLE'],
                            'STATUT': item['STATUT'],
                        }
                        if item.get('DATEDEB'):
                            kwargs['DATEDEB'] = date.fromisoformat(item['DATEDEB'])
                        if item.get('DATEFIN'):
                            kwargs['DATEFIN'] = date.fromisoformat(item['DATEFIN'])
                        ZDDE.objects.create(**kwargs)
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur ZDDE [{item.get('CODE')}]: {e}"
                ))

        return stats

    @transaction.atomic
    def _charger_zdpo(self, data, dry_run, force):
        from departement.models import ZDDE, ZDPO
        stats = self._stats()

        for item in data:
            try:
                dept = ZDDE.objects.filter(CODE=item['DEPARTEMENT_CODE']).first()
                if not dept:
                    self.stderr.write(self.style.WARNING(
                        f"    ZDPO [{item['CODE']}]: departement {item['DEPARTEMENT_CODE']} introuvable, ignore"
                    ))
                    stats['erreurs'] += 1
                    continue

                existing = ZDPO.objects.filter(CODE=item['CODE']).first()
                if existing:
                    if force and not dry_run:
                        existing.LIBELLE = item['LIBELLE']
                        existing.DEPARTEMENT = dept
                        existing.STATUT = item['STATUT']
                        if item.get('DATEDEB'):
                            existing.DATEDEB = date.fromisoformat(item['DATEDEB'])
                        if item.get('DATEFIN'):
                            existing.DATEFIN = date.fromisoformat(item['DATEFIN'])
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        kwargs = {
                            'CODE': item['CODE'],
                            'LIBELLE': item['LIBELLE'],
                            'DEPARTEMENT': dept,
                            'STATUT': item['STATUT'],
                        }
                        if item.get('DATEDEB'):
                            kwargs['DATEDEB'] = date.fromisoformat(item['DATEDEB'])
                        if item.get('DATEFIN'):
                            kwargs['DATEFIN'] = date.fromisoformat(item['DATEFIN'])
                        ZDPO.objects.create(**kwargs)
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur ZDPO [{item.get('CODE')}]: {e}"
                ))

        return stats

    @transaction.atomic
    def _charger_type_absence(self, data, dry_run, force):
        from absence.models import TypeAbsence
        stats = self._stats()

        for item in data:
            try:
                existing = TypeAbsence.objects.filter(code=item['code']).first()
                if existing:
                    if force and not dry_run:
                        existing.libelle = item['libelle']
                        existing.categorie = item['categorie']
                        existing.paye = item['paye']
                        existing.decompte_solde = item['decompte_solde']
                        existing.justificatif_obligatoire = item['justificatif_obligatoire']
                        existing.couleur = item['couleur']
                        existing.ordre = item['ordre']
                        existing.actif = item['actif']
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        TypeAbsence.objects.create(
                            code=item['code'],
                            libelle=item['libelle'],
                            categorie=item['categorie'],
                            paye=item['paye'],
                            decompte_solde=item['decompte_solde'],
                            justificatif_obligatoire=item['justificatif_obligatoire'],
                            couleur=item['couleur'],
                            ordre=item['ordre'],
                            actif=item['actif'],
                        )
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur TypeAbsence [{item.get('code')}]: {e}"
                ))

        return stats

    @transaction.atomic
    def _charger_nfca(self, data, dry_run, force):
        from frais.models import NFCA
        stats = self._stats()

        for item in data:
            try:
                existing = NFCA.objects.filter(CODE=item['CODE']).first()
                if existing:
                    if force and not dry_run:
                        existing.LIBELLE = item['LIBELLE']
                        existing.DESCRIPTION = item.get('DESCRIPTION', '')
                        existing.JUSTIFICATIF_OBLIGATOIRE = item['JUSTIFICATIF_OBLIGATOIRE']
                        existing.PLAFOND_DEFAUT = Decimal(item['PLAFOND_DEFAUT']) if item.get('PLAFOND_DEFAUT') else None
                        existing.ICONE = item.get('ICONE', '')
                        existing.STATUT = item['STATUT']
                        existing.ORDRE = item['ORDRE']
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        kwargs = {
                            'CODE': item['CODE'],
                            'LIBELLE': item['LIBELLE'],
                            'DESCRIPTION': item.get('DESCRIPTION', ''),
                            'JUSTIFICATIF_OBLIGATOIRE': item['JUSTIFICATIF_OBLIGATOIRE'],
                            'ICONE': item.get('ICONE', ''),
                            'STATUT': item['STATUT'],
                            'ORDRE': item['ORDRE'],
                        }
                        if item.get('PLAFOND_DEFAUT'):
                            kwargs['PLAFOND_DEFAUT'] = Decimal(item['PLAFOND_DEFAUT'])
                        NFCA.objects.create(**kwargs)
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur NFCA [{item.get('CODE')}]: {e}"
                ))

        return stats

    @transaction.atomic
    def _charger_zyro(self, data, dry_run, force):
        from employee.models import ZYRO
        stats = self._stats()

        for item in data:
            try:
                # Créer ou récupérer le Group Django associé
                django_group = None
                group_name = item.get('django_group_name')
                if group_name and not dry_run:
                    django_group, _ = Group.objects.get_or_create(name=group_name)

                existing = ZYRO.objects.filter(CODE=item['CODE']).first()
                if existing:
                    if force and not dry_run:
                        existing.LIBELLE = item['LIBELLE']
                        existing.DESCRIPTION = item.get('DESCRIPTION', '')
                        existing.PERMISSIONS_CUSTOM = item.get('PERMISSIONS_CUSTOM', {})
                        existing.actif = item['actif']
                        if django_group:
                            existing.django_group = django_group
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        ZYRO.objects.create(
                            CODE=item['CODE'],
                            LIBELLE=item['LIBELLE'],
                            DESCRIPTION=item.get('DESCRIPTION', ''),
                            django_group=django_group,
                            PERMISSIONS_CUSTOM=item.get('PERMISSIONS_CUSTOM', {}),
                            actif=item['actif'],
                        )
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur ZYRO [{item.get('CODE')}]: {e}"
                ))

        return stats

    @transaction.atomic
    def _charger_gac_categorie(self, data, dry_run, force):
        from gestion_achats.models import GACCategorie
        stats = self._stats()

        # Premier passage : créer les catégories sans parent
        for item in data:
            if item.get('parent_code'):
                continue
            try:
                existing = GACCategorie.objects.filter(code=item['code']).first()
                if existing:
                    if force and not dry_run:
                        existing.nom = item['nom']
                        existing.description = item.get('description', '')
                        existing.ordre = item['ordre']
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        GACCategorie.objects.create(
                            code=item['code'],
                            nom=item['nom'],
                            description=item.get('description', ''),
                            ordre=item['ordre'],
                        )
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur GACCategorie [{item.get('code')}]: {e}"
                ))

        # Second passage : créer les sous-catégories (avec parent)
        for item in data:
            if not item.get('parent_code'):
                continue
            try:
                parent = GACCategorie.objects.filter(code=item['parent_code']).first()
                if not parent:
                    self.stderr.write(self.style.WARNING(
                        f"    GACCategorie [{item['code']}]: parent {item['parent_code']} introuvable, ignore"
                    ))
                    stats['erreurs'] += 1
                    continue

                existing = GACCategorie.objects.filter(code=item['code']).first()
                if existing:
                    if force and not dry_run:
                        existing.nom = item['nom']
                        existing.description = item.get('description', '')
                        existing.parent = parent
                        existing.ordre = item['ordre']
                        existing.save()
                        stats['mis_a_jour'] += 1
                    else:
                        stats['existants'] += 1
                else:
                    if not dry_run:
                        GACCategorie.objects.create(
                            code=item['code'],
                            nom=item['nom'],
                            description=item.get('description', ''),
                            parent=parent,
                            ordre=item['ordre'],
                        )
                    stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(
                    f"    Erreur GACCategorie [{item.get('code')}]: {e}"
                ))

        return stats

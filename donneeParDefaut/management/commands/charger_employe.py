# donneeParDefaut/management/commands/charger_employe.py
"""
Commande Django pour charger un employé par défaut avec toutes ses données
associées à partir du fichier JSON extrait.

Ordre de chargement (respect des dépendances) :
    1. User (compte Django)
    2. ZY00 (fiche employé) -> lié à User + Entreprise
    3. ZYNP (historique noms/prénoms)
    4. ZYCO (contrats)
    5. ZYTE (téléphones)
    6. ZYME (emails)
    7. ZYAF (affectations) -> lié à ZDPO
    8. ZYAD (adresses)
    9. ZYDO (documents - métadonnées)
    10. ZYFA (personnes à charge)
    11. ZYPP (personnes à prévenir)
    12. ZYIB (identité bancaire)
    13. ZYRE (rôles attribués) -> lié à ZYRO

Prérequis : charger_donnees doit être exécuté avant (ZDPO, ZYRO, etc.)

Usage:
    python manage.py charger_employe
    python manage.py charger_employe --fichier employe_mt000001.json
    python manage.py charger_employe --dry-run
    python manage.py charger_employe --password MonMotDePasse123
"""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()
DATA_DIR = Path(settings.BASE_DIR) / 'donneeParDefaut' / 'data'


class Command(BaseCommand):
    help = "Charge un employé par défaut avec toutes ses données associées"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            type=str,
            default='employe_mt000001.json',
            help='Nom du fichier JSON (défaut: employe_mt000001.json)'
        )
        parser.add_argument(
            '--input',
            type=str,
            default=str(DATA_DIR),
            help='Dossier source (défaut: donneeParDefaut/data/)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans écriture en base'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Mot de passe en clair pour le User (sinon utilise le hash sauvegardé)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Met à jour les données si elles existent déjà'
        )

    def handle(self, *args, **options):
        fichier = Path(options['input']) / options['fichier']
        dry_run = options['dry_run']
        password = options['password']
        force = options['force']

        if not fichier.exists():
            self.stderr.write(self.style.ERROR(
                f"  Fichier introuvable : {fichier}"
            ))
            return

        with open(fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)

        matricule = data['matricule']

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  CHARGEMENT EMPLOYE PAR DEFAUT : {matricule}")
        if dry_run:
            self.stdout.write(self.style.WARNING("  MODE SIMULATION"))
        self.stdout.write(f"{'='*60}\n")

        stats = {'crees': 0, 'existants': 0, 'mis_a_jour': 0, 'erreurs': 0}

        try:
            with transaction.atomic():
                if dry_run:
                    # En dry-run, on simule sans écrire
                    self._simuler(data, stats)
                    raise _DryRunRollback()
                else:
                    self._charger_tout(data, stats, password, force)
        except _DryRunRollback:
            pass

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("  RESUME")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"  Crees       : {stats['crees']}"))
        self.stdout.write(f"  Existants   : {stats['existants']}")
        if stats['mis_a_jour']:
            self.stdout.write(self.style.WARNING(f"  Mis a jour  : {stats['mis_a_jour']}"))
        if stats['erreurs']:
            self.stdout.write(self.style.ERROR(f"  Erreurs     : {stats['erreurs']}"))
        self.stdout.write(f"{'='*60}\n")

    def _simuler(self, data, stats):
        """Simule le chargement et compte les opérations."""
        from employee.models import ZY00

        # User
        user_data = data.get('user')
        if user_data:
            if User.objects.filter(username=user_data['username']).exists():
                stats['existants'] += 1
                self.stdout.write(f"  User         : existant ({user_data['username']})")
            else:
                stats['crees'] += 1
                self.stdout.write(f"  User         : a creer ({user_data['username']})")

        # ZY00
        zy00_data = data.get('zy00')
        if zy00_data:
            if ZY00.objects.filter(matricule=zy00_data['matricule']).exists():
                stats['existants'] += 1
                self.stdout.write(f"  ZY00         : existant ({zy00_data['matricule']})")
            else:
                stats['crees'] += 1
                self.stdout.write(f"  ZY00         : a creer ({zy00_data['matricule']})")

        # Tables enfants
        tables_enfants = [
            ('ZYNP', 'zynp'), ('ZYCO', 'zyco'), ('ZYTE', 'zyte'),
            ('ZYME', 'zyme'), ('ZYAF', 'zyaf'), ('ZYAD', 'zyad'),
            ('ZYDO', 'zydo'), ('ZYFA', 'zyfa'), ('ZYPP', 'zypp'),
            ('ZYRE', 'zyre'),
        ]
        for label, key in tables_enfants:
            items = data.get(key, [])
            if items:
                stats['crees'] += len(items)
                self.stdout.write(f"  {label:12s} : {len(items)} a creer")

        # ZYIB (OneToOne)
        zyib_data = data.get('zyib')
        if zyib_data:
            stats['crees'] += 1
            self.stdout.write(f"  ZYIB         : a creer")

    def _charger_tout(self, data, stats, password, force):
        """Charge toutes les données en base."""
        from employee.models import ZY00

        matricule = data['matricule']

        # 1. User
        user = self._charger_user(data.get('user'), stats, password, force)

        # 2. ZY00
        employe = self._charger_zy00(data.get('zy00'), user, stats, force)
        if not employe:
            self.stderr.write(self.style.ERROR("  Impossible de créer l'employé, abandon"))
            return

        # 3. Tables enfants
        self._charger_zynp(employe, data.get('zynp', []), stats, force)
        self._charger_zyco(employe, data.get('zyco', []), stats, force)
        self._charger_zyte(employe, data.get('zyte', []), stats, force)
        self._charger_zyme(employe, data.get('zyme', []), stats, force)
        self._charger_zyaf(employe, data.get('zyaf', []), stats, force)
        self._charger_zyad(employe, data.get('zyad', []), stats, force)
        self._charger_zydo(employe, data.get('zydo', []), stats, force)
        self._charger_zyfa(employe, data.get('zyfa', []), stats, force)
        self._charger_zypp(employe, data.get('zypp', []), stats, force)
        self._charger_zyib(employe, data.get('zyib'), stats, force)
        self._charger_zyre(employe, data.get('zyre', []), stats, force)

    def _charger_user(self, user_data, stats, password, force):
        if not user_data:
            return None

        existing = User.objects.filter(username=user_data['username']).first()
        if existing:
            if force:
                existing.email = user_data['email']
                existing.first_name = user_data['first_name']
                existing.last_name = user_data['last_name']
                existing.is_active = user_data['is_active']
                existing.is_staff = user_data['is_staff']
                existing.is_superuser = user_data['is_superuser']
                if password:
                    existing.set_password(password)
                existing.save()
                stats['mis_a_jour'] += 1
                self.stdout.write(f"  User         : mis a jour ({existing.username})")
            else:
                stats['existants'] += 1
                self.stdout.write(f"  User         : existant ({existing.username})")
            return existing

        user = User(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            is_active=user_data['is_active'],
            is_staff=user_data['is_staff'],
            is_superuser=user_data['is_superuser'],
        )

        if password:
            user.set_password(password)
        else:
            # Utiliser le hash sauvegardé
            user.password = user_data['password']

        user.save()

        # Ajouter aux groupes
        for group_name in user_data.get('groups', []):
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        stats['crees'] += 1
        self.stdout.write(self.style.SUCCESS(f"  User         : cree ({user.username})"))
        return user

    def _charger_zy00(self, zy00_data, user, stats, force):
        from employee.models import ZY00
        from entreprise.models import Entreprise

        if not zy00_data:
            return None

        existing = ZY00.objects.filter(matricule=zy00_data['matricule']).first()
        if existing:
            if force:
                self._update_zy00_fields(existing, zy00_data, user)
                existing.save()
                stats['mis_a_jour'] += 1
                self.stdout.write(f"  ZY00         : mis a jour ({existing.matricule})")
            else:
                stats['existants'] += 1
                self.stdout.write(f"  ZY00         : existant ({existing.matricule})")
            return existing

        # Résoudre l'entreprise
        entreprise = None
        if zy00_data.get('entreprise_id'):
            entreprise = Entreprise.objects.filter(id=zy00_data['entreprise_id']).first()
            if not entreprise:
                entreprise = Entreprise.objects.first()

        # Résoudre la convention
        convention = None
        if zy00_data.get('convention_code'):
            from absence.models import ConfigurationConventionnelle
            convention = ConfigurationConventionnelle.objects.filter(
                code=zy00_data['convention_code']
            ).first()

        kwargs = {
            'matricule': zy00_data['matricule'],
            'nom': zy00_data['nom'],
            'prenoms': zy00_data['prenoms'],
            'username': zy00_data.get('username', ''),
            'prenomuser': zy00_data.get('prenomuser', ''),
            'sexe': zy00_data['sexe'],
            'ville_naissance': zy00_data.get('ville_naissance', ''),
            'pays_naissance': zy00_data.get('pays_naissance', ''),
            'situation_familiale': zy00_data.get('situation_familiale', 'CELIBATAIRE'),
            'type_id': zy00_data['type_id'],
            'numero_id': zy00_data['numero_id'],
            'type_dossier': zy00_data.get('type_dossier', 'SAL'),
            'etat': zy00_data.get('etat', 'actif'),
            'coefficient_temps_travail': Decimal(zy00_data.get('coefficient_temps_travail', '1.00')),
        }

        if user:
            kwargs['user'] = user
        if entreprise:
            kwargs['entreprise'] = entreprise
        if convention:
            kwargs['convention_personnalisee'] = convention

        # Dates
        for field in ['date_naissance', 'date_validite_id', 'date_expiration_id',
                       'date_validation_embauche', 'date_entree_entreprise']:
            if zy00_data.get(field):
                kwargs[field] = date.fromisoformat(zy00_data[field])

        employe = ZY00(**kwargs)
        employe.save()

        stats['crees'] += 1
        self.stdout.write(self.style.SUCCESS(
            f"  ZY00         : cree ({employe.matricule} - {employe.nom} {employe.prenoms})"
        ))
        return employe

    def _update_zy00_fields(self, employe, zy00_data, user):
        employe.nom = zy00_data['nom']
        employe.prenoms = zy00_data['prenoms']
        employe.sexe = zy00_data['sexe']
        employe.etat = zy00_data.get('etat', 'actif')
        if user:
            employe.user = user

    def _charger_zynp(self, employe, items, stats, force):
        from employee.models import ZYNP
        for item in items:
            try:
                existing = ZYNP.objects.filter(
                    employe=employe,
                    nom=item['nom'],
                    prenoms=item['prenoms'],
                    date_debut_validite=date.fromisoformat(item['date_debut_validite'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYNP.objects.create(
                    employe=employe,
                    nom=item['nom'],
                    prenoms=item['prenoms'],
                    date_debut_validite=date.fromisoformat(item['date_debut_validite']),
                    date_fin_validite=date.fromisoformat(item['date_fin_validite']) if item.get('date_fin_validite') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYNP: {e}"))
        if items:
            self.stdout.write(f"  ZYNP         : {len(items)} traite(s)")

    def _charger_zyco(self, employe, items, stats, force):
        from employee.models import ZYCO
        for item in items:
            try:
                existing = ZYCO.objects.filter(
                    employe=employe,
                    type_contrat=item['type_contrat'],
                    date_debut=date.fromisoformat(item['date_debut'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYCO.objects.create(
                    employe=employe,
                    type_contrat=item['type_contrat'],
                    date_debut=date.fromisoformat(item['date_debut']),
                    date_fin=date.fromisoformat(item['date_fin']) if item.get('date_fin') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYCO: {e}"))
        if items:
            self.stdout.write(f"  ZYCO         : {len(items)} traite(s)")

    def _charger_zyte(self, employe, items, stats, force):
        from employee.models import ZYTE
        for item in items:
            try:
                existing = ZYTE.objects.filter(
                    employe=employe,
                    numero=item['numero']
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYTE.objects.create(
                    employe=employe,
                    numero=item['numero'],
                    date_debut_validite=date.fromisoformat(item['date_debut_validite']),
                    date_fin_validite=date.fromisoformat(item['date_fin_validite']) if item.get('date_fin_validite') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYTE: {e}"))
        if items:
            self.stdout.write(f"  ZYTE         : {len(items)} traite(s)")

    def _charger_zyme(self, employe, items, stats, force):
        from employee.models import ZYME
        for item in items:
            try:
                existing = ZYME.objects.filter(
                    employe=employe,
                    email=item['email']
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYME.objects.create(
                    employe=employe,
                    email=item['email'],
                    date_debut_validite=date.fromisoformat(item['date_debut_validite']),
                    date_fin_validite=date.fromisoformat(item['date_fin_validite']) if item.get('date_fin_validite') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYME: {e}"))
        if items:
            self.stdout.write(f"  ZYME         : {len(items)} traite(s)")

    def _charger_zyaf(self, employe, items, stats, force):
        from employee.models import ZYAF
        from departement.models import ZDPO
        for item in items:
            try:
                poste = ZDPO.objects.filter(CODE=item['poste_code']).first()
                if not poste:
                    self.stderr.write(self.style.WARNING(
                        f"    ZYAF: poste {item['poste_code']} introuvable, ignore"
                    ))
                    stats['erreurs'] += 1
                    continue
                existing = ZYAF.objects.filter(
                    employe=employe,
                    poste=poste,
                    date_debut=date.fromisoformat(item['date_debut'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYAF.objects.create(
                    employe=employe,
                    poste=poste,
                    date_debut=date.fromisoformat(item['date_debut']),
                    date_fin=date.fromisoformat(item['date_fin']) if item.get('date_fin') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYAF: {e}"))
        if items:
            self.stdout.write(f"  ZYAF         : {len(items)} traite(s)")

    def _charger_zyad(self, employe, items, stats, force):
        from employee.models import ZYAD
        for item in items:
            try:
                existing = ZYAD.objects.filter(
                    employe=employe,
                    type_adresse=item['type_adresse'],
                    date_debut=date.fromisoformat(item['date_debut'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYAD.objects.create(
                    employe=employe,
                    rue=item['rue'],
                    complement=item.get('complement', ''),
                    ville=item['ville'],
                    pays=item['pays'],
                    code_postal=item['code_postal'],
                    type_adresse=item['type_adresse'],
                    date_debut=date.fromisoformat(item['date_debut']),
                    date_fin=date.fromisoformat(item['date_fin']) if item.get('date_fin') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYAD: {e}"))
        if items:
            self.stdout.write(f"  ZYAD         : {len(items)} traite(s)")

    def _charger_zydo(self, employe, items, stats, force):
        """Charge les métadonnées des documents (sans fichiers physiques)."""
        from employee.models import ZYDO
        for item in items:
            try:
                existing = ZYDO.objects.filter(
                    employe=employe,
                    type_document=item['type_document'],
                    description=item.get('description', '')
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYDO.objects.create(
                    employe=employe,
                    type_document=item['type_document'],
                    description=item.get('description', ''),
                    taille_fichier=item.get('taille_fichier'),
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYDO: {e}"))
        if items:
            self.stdout.write(f"  ZYDO         : {len(items)} traite(s)")

    def _charger_zyfa(self, employe, items, stats, force):
        from employee.models import ZYFA
        for item in items:
            try:
                existing = ZYFA.objects.filter(
                    employe=employe,
                    nom=item['nom'],
                    prenom=item['prenom'],
                    date_naissance=date.fromisoformat(item['date_naissance'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYFA.objects.create(
                    employe=employe,
                    personne_charge=item['personne_charge'],
                    nom=item['nom'],
                    prenom=item['prenom'],
                    sexe=item['sexe'],
                    date_naissance=date.fromisoformat(item['date_naissance']),
                    date_debut_prise_charge=date.fromisoformat(item['date_debut_prise_charge']),
                    date_fin_prise_charge=date.fromisoformat(item['date_fin_prise_charge']) if item.get('date_fin_prise_charge') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYFA: {e}"))
        if items:
            self.stdout.write(f"  ZYFA         : {len(items)} traite(s)")

    def _charger_zypp(self, employe, items, stats, force):
        from employee.models import ZYPP
        for item in items:
            try:
                existing = ZYPP.objects.filter(
                    employe=employe,
                    nom=item['nom'],
                    prenom=item['prenom'],
                    telephone_principal=item['telephone_principal']
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYPP.objects.create(
                    employe=employe,
                    nom=item['nom'],
                    prenom=item['prenom'],
                    lien_parente=item['lien_parente'],
                    telephone_principal=item['telephone_principal'],
                    telephone_secondaire=item.get('telephone_secondaire', ''),
                    email=item.get('email', ''),
                    adresse=item.get('adresse', ''),
                    ordre_priorite=item['ordre_priorite'],
                    remarques=item.get('remarques', ''),
                    date_debut_validite=date.fromisoformat(item['date_debut_validite']),
                    date_fin_validite=date.fromisoformat(item['date_fin_validite']) if item.get('date_fin_validite') else None,
                    actif=item['actif'],
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYPP: {e}"))
        if items:
            self.stdout.write(f"  ZYPP         : {len(items)} traite(s)")

    def _charger_zyib(self, employe, zyib_data, stats, force):
        if not zyib_data:
            return
        from employee.models import ZYIB
        try:
            existing = ZYIB.objects.filter(employe=employe).first()
            if existing:
                if force:
                    for field in ['titulaire_compte', 'nom_banque', 'code_banque',
                                  'code_guichet', 'numero_compte', 'cle_rib',
                                  'type_compte', 'actif']:
                        setattr(existing, field, zyib_data[field])
                    existing.iban = zyib_data.get('iban', '')
                    existing.bic = zyib_data.get('bic', '')
                    existing.domiciliation = zyib_data.get('domiciliation', '')
                    existing.remarques = zyib_data.get('remarques', '')
                    if zyib_data.get('date_ouverture'):
                        existing.date_ouverture = date.fromisoformat(zyib_data['date_ouverture'])
                    existing.save()
                    stats['mis_a_jour'] += 1
                    self.stdout.write(f"  ZYIB         : mis a jour")
                else:
                    stats['existants'] += 1
                    self.stdout.write(f"  ZYIB         : existant")
                return

            kwargs = {
                'employe': employe,
                'titulaire_compte': zyib_data['titulaire_compte'],
                'nom_banque': zyib_data['nom_banque'],
                'code_banque': zyib_data['code_banque'],
                'code_guichet': zyib_data['code_guichet'],
                'numero_compte': zyib_data['numero_compte'],
                'cle_rib': zyib_data['cle_rib'],
                'iban': zyib_data.get('iban', ''),
                'bic': zyib_data.get('bic', ''),
                'type_compte': zyib_data.get('type_compte', 'COURANT'),
                'domiciliation': zyib_data.get('domiciliation', ''),
                'actif': zyib_data['actif'],
                'remarques': zyib_data.get('remarques', ''),
            }
            if zyib_data.get('date_ouverture'):
                kwargs['date_ouverture'] = date.fromisoformat(zyib_data['date_ouverture'])

            ZYIB.objects.create(**kwargs)
            stats['crees'] += 1
            self.stdout.write(self.style.SUCCESS(f"  ZYIB         : cree"))
        except Exception as e:
            stats['erreurs'] += 1
            self.stderr.write(self.style.ERROR(f"    Erreur ZYIB: {e}"))

    def _charger_zyre(self, employe, items, stats, force):
        from employee.models import ZYRO, ZYRE
        for item in items:
            try:
                role = ZYRO.objects.filter(CODE=item['role_code']).first()
                if not role:
                    self.stderr.write(self.style.WARNING(
                        f"    ZYRE: role {item['role_code']} introuvable, ignore"
                    ))
                    stats['erreurs'] += 1
                    continue
                existing = ZYRE.objects.filter(
                    employe=employe,
                    role=role,
                    date_debut=date.fromisoformat(item['date_debut'])
                ).first()
                if existing:
                    stats['existants'] += 1
                    continue
                ZYRE.objects.create(
                    employe=employe,
                    role=role,
                    date_debut=date.fromisoformat(item['date_debut']),
                    date_fin=date.fromisoformat(item['date_fin']) if item.get('date_fin') else None,
                    actif=item['actif'],
                    commentaire=item.get('commentaire', ''),
                )
                stats['crees'] += 1
            except Exception as e:
                stats['erreurs'] += 1
                self.stderr.write(self.style.ERROR(f"    Erreur ZYRE: {e}"))
        if items:
            self.stdout.write(f"  ZYRE         : {len(items)} traite(s)")


class _DryRunRollback(Exception):
    """Exception pour rollback en mode dry-run."""
    pass

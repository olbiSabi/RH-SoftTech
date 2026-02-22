# donneeParDefaut/management/commands/extraire_employe.py
"""
Commande Django pour extraire les données complètes d'un employé
et de toutes ses tables liées pour constituer un employé par défaut.

Tables extraites :
    - User (compte Django)
    - ZY00 (fiche employé)
    - ZYNP (historique noms/prénoms)
    - ZYCO (contrats)
    - ZYTE (téléphones)
    - ZYME (emails)
    - ZYAF (affectations)
    - ZYAD (adresses)
    - ZYDO (documents - métadonnées uniquement)
    - ZYFA (personnes à charge)
    - ZYPP (personnes à prévenir)
    - ZYIB (identité bancaire)
    - ZYRE (rôles attribués)

Usage:
    python manage.py extraire_employe MT000001
    python manage.py extraire_employe MT000001 --output /chemin/custom/
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_OUTPUT_DIR = Path(settings.BASE_DIR) / 'donneeParDefaut' / 'data'


class Command(BaseCommand):
    help = "Extrait les données complètes d'un employé vers un fichier JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            'matricule',
            type=str,
            help="Matricule de l'employé à extraire (ex: MT000001)"
        )
        parser.add_argument(
            '--output',
            type=str,
            default=str(DEFAULT_OUTPUT_DIR),
            help='Dossier de sortie (défaut: donneeParDefaut/data/)'
        )

    def handle(self, *args, **options):
        from employee.models import ZY00

        matricule = options['matricule']
        output_dir = Path(options['output'])
        output_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  EXTRACTION EMPLOYE : {matricule}")
        self.stdout.write(f"{'='*60}\n")

        try:
            employe = ZY00.objects.get(matricule=matricule)
        except ZY00.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"  Employé {matricule} introuvable"
            ))
            return

        data = {
            'matricule': matricule,
            'user': self._extraire_user(employe),
            'zy00': self._extraire_zy00(employe),
            'zynp': self._extraire_zynp(employe),
            'zyco': self._extraire_zyco(employe),
            'zyte': self._extraire_zyte(employe),
            'zyme': self._extraire_zyme(employe),
            'zyaf': self._extraire_zyaf(employe),
            'zyad': self._extraire_zyad(employe),
            'zydo': self._extraire_zydo(employe),
            'zyfa': self._extraire_zyfa(employe),
            'zypp': self._extraire_zypp(employe),
            'zyib': self._extraire_zyib(employe),
            'zyre': self._extraire_zyre(employe),
        }

        fichier = output_dir / f"employe_{matricule.lower()}.json"
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # Résumé
        self.stdout.write(self.style.SUCCESS(
            f"  Employe  : {employe.nom} {employe.prenoms} ({matricule})"
        ))
        self._afficher_compteurs(data)
        self.stdout.write(f"\n  Fichier  : {fichier}")
        self.stdout.write(f"{'='*60}\n")

    def _afficher_compteurs(self, data):
        tables = [
            ('User', 'user', lambda d: 1 if d else 0),
            ('ZY00', 'zy00', lambda d: 1 if d else 0),
            ('ZYNP', 'zynp', len),
            ('ZYCO', 'zyco', len),
            ('ZYTE', 'zyte', len),
            ('ZYME', 'zyme', len),
            ('ZYAF', 'zyaf', len),
            ('ZYAD', 'zyad', len),
            ('ZYDO', 'zydo', len),
            ('ZYFA', 'zyfa', len),
            ('ZYPP', 'zypp', len),
            ('ZYIB', 'zyib', lambda d: 1 if d else 0),
            ('ZYRE', 'zyre', len),
        ]
        total = 0
        for label, key, counter in tables:
            nb = counter(data[key])
            total += nb
            if nb > 0:
                self.stdout.write(f"  {label:10s} : {nb} enregistrement(s)")
        self.stdout.write(f"  {'':10s}   ----")
        self.stdout.write(f"  {'Total':10s} : {total} enregistrement(s)")

    def _extraire_user(self, employe):
        user = employe.user
        if not user:
            return None
        return {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'password': user.password,  # Hash du mot de passe
            'groups': [g.name for g in user.groups.all()],
        }

    def _extraire_zy00(self, employe):
        return {
            'matricule': employe.matricule,
            'nom': employe.nom,
            'prenoms': employe.prenoms,
            'username': employe.username,
            'prenomuser': employe.prenomuser,
            'date_naissance': employe.date_naissance.isoformat() if employe.date_naissance else None,
            'sexe': employe.sexe,
            'ville_naissance': employe.ville_naissance or '',
            'pays_naissance': employe.pays_naissance or '',
            'situation_familiale': employe.situation_familiale,
            'type_id': employe.type_id,
            'numero_id': employe.numero_id,
            'date_validite_id': employe.date_validite_id.isoformat() if employe.date_validite_id else None,
            'date_expiration_id': employe.date_expiration_id.isoformat() if employe.date_expiration_id else None,
            'type_dossier': employe.type_dossier,
            'date_validation_embauche': employe.date_validation_embauche.isoformat() if employe.date_validation_embauche else None,
            'etat': employe.etat,
            'entreprise_id': employe.entreprise_id,
            'convention_code': employe.convention_personnalisee.code if employe.convention_personnalisee else None,
            'date_entree_entreprise': employe.date_entree_entreprise.isoformat() if employe.date_entree_entreprise else None,
            'coefficient_temps_travail': str(employe.coefficient_temps_travail),
        }

    def _extraire_zynp(self, employe):
        data = []
        for obj in employe.historique_noms_prenoms.all().order_by('-date_debut_validite'):
            data.append({
                'nom': obj.nom,
                'prenoms': obj.prenoms,
                'date_debut_validite': obj.date_debut_validite.isoformat(),
                'date_fin_validite': obj.date_fin_validite.isoformat() if obj.date_fin_validite else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyco(self, employe):
        data = []
        for obj in employe.contrats.all().order_by('-date_debut'):
            data.append({
                'type_contrat': obj.type_contrat,
                'date_debut': obj.date_debut.isoformat(),
                'date_fin': obj.date_fin.isoformat() if obj.date_fin else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyte(self, employe):
        data = []
        for obj in employe.telephones.all().order_by('-date_debut_validite'):
            data.append({
                'numero': obj.numero,
                'date_debut_validite': obj.date_debut_validite.isoformat(),
                'date_fin_validite': obj.date_fin_validite.isoformat() if obj.date_fin_validite else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyme(self, employe):
        data = []
        for obj in employe.emails.all().order_by('-date_debut_validite'):
            data.append({
                'email': obj.email,
                'date_debut_validite': obj.date_debut_validite.isoformat(),
                'date_fin_validite': obj.date_fin_validite.isoformat() if obj.date_fin_validite else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyaf(self, employe):
        data = []
        for obj in employe.affectations.select_related('poste').all().order_by('-date_debut'):
            data.append({
                'poste_code': obj.poste.CODE,
                'date_debut': obj.date_debut.isoformat(),
                'date_fin': obj.date_fin.isoformat() if obj.date_fin else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyad(self, employe):
        data = []
        for obj in employe.adresses.all().order_by('-date_debut'):
            data.append({
                'rue': obj.rue,
                'complement': obj.complement or '',
                'ville': obj.ville,
                'pays': obj.pays,
                'code_postal': obj.code_postal,
                'type_adresse': obj.type_adresse,
                'date_debut': obj.date_debut.isoformat(),
                'date_fin': obj.date_fin.isoformat() if obj.date_fin else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zydo(self, employe):
        """Extrait les métadonnées des documents (sans les fichiers)."""
        data = []
        for obj in employe.documents.all().order_by('-date_ajout'):
            data.append({
                'type_document': obj.type_document,
                'description': obj.description or '',
                'taille_fichier': obj.taille_fichier,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyfa(self, employe):
        data = []
        for obj in employe.personnes_charge.all().order_by('-date_debut_prise_charge'):
            data.append({
                'personne_charge': obj.personne_charge,
                'nom': obj.nom,
                'prenom': obj.prenom,
                'sexe': obj.sexe,
                'date_naissance': obj.date_naissance.isoformat(),
                'date_debut_prise_charge': obj.date_debut_prise_charge.isoformat(),
                'date_fin_prise_charge': obj.date_fin_prise_charge.isoformat() if obj.date_fin_prise_charge else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zypp(self, employe):
        data = []
        for obj in employe.personnes_prevenir.all().order_by('ordre_priorite'):
            data.append({
                'nom': obj.nom,
                'prenom': obj.prenom,
                'lien_parente': obj.lien_parente,
                'telephone_principal': obj.telephone_principal,
                'telephone_secondaire': obj.telephone_secondaire or '',
                'email': obj.email or '',
                'adresse': obj.adresse or '',
                'ordre_priorite': obj.ordre_priorite,
                'remarques': obj.remarques or '',
                'date_debut_validite': obj.date_debut_validite.isoformat(),
                'date_fin_validite': obj.date_fin_validite.isoformat() if obj.date_fin_validite else None,
                'actif': obj.actif,
            })
        return data

    def _extraire_zyib(self, employe):
        try:
            obj = employe.identite_bancaire
        except Exception:
            return None

        return {
            'titulaire_compte': obj.titulaire_compte,
            'nom_banque': obj.nom_banque,
            'code_banque': obj.code_banque,
            'code_guichet': obj.code_guichet,
            'numero_compte': obj.numero_compte,
            'cle_rib': obj.cle_rib,
            'iban': obj.iban or '',
            'bic': obj.bic or '',
            'type_compte': obj.type_compte,
            'domiciliation': obj.domiciliation or '',
            'date_ouverture': obj.date_ouverture.isoformat() if obj.date_ouverture else None,
            'actif': obj.actif,
            'remarques': obj.remarques or '',
        }

    def _extraire_zyre(self, employe):
        data = []
        for obj in employe.roles_attribues.select_related('role').all().order_by('-date_debut'):
            data.append({
                'role_code': obj.role.CODE,
                'date_debut': obj.date_debut.isoformat(),
                'date_fin': obj.date_fin.isoformat() if obj.date_fin else None,
                'actif': obj.actif,
                'commentaire': obj.commentaire or '',
            })
        return data

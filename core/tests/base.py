# core/tests/base.py
"""
Classe de base partagée pour les tests de tous les modules.
Étend EmployeeTestCase avec des helpers spécifiques à chaque module.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone

from employee.tests.base import EmployeeTestCase


class BaseTestCase(EmployeeTestCase):
    """
    Classe de base pour les tests nécessitant un utilisateur authentifié
    avec un employé lié.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Créer un employé de base et son utilisateur
        from employee.models import ZY00
        cls.employe = ZY00.objects.create(
            matricule='BASE0001',
            nom='Dupont',
            prenoms='Jean',
            date_naissance=date(1990, 5, 15),
            sexe='M',
            type_id='CNI',
            numero_id='IDBASE0001',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            type_dossier='SAL',
            etat='actif',
        )
        cls.user = User.objects.create_user(
            username='BASE0001',
            email='base0001@test.com',
            password='testpass123'
        )
        cls.employe.user = cls.user
        cls.employe.save()

    def setUp(self):
        """Connecter le client à chaque test."""
        self.client = Client()
        self.client.login(username='BASE0001', password='testpass123')

    # ==========================================
    # Helpers Absence
    # ==========================================

    def create_type_absence(self, code='CPN', libelle='Congés payés', **kwargs):
        """Créer un type d'absence de test."""
        from absence.models import TypeAbsence
        defaults = {
            'code': code,
            'libelle': libelle,
            'categorie': 'CONGES_PAYES',
            'paye': True,
            'decompte_solde': True,
            'actif': True,
        }
        defaults.update(kwargs)
        return TypeAbsence.objects.create(**defaults)

    def create_absence(self, employe=None, type_absence=None, **kwargs):
        """Créer une absence de test."""
        from absence.models import Absence
        if employe is None:
            employe = self.employe
        if type_absence is None:
            type_absence = self.create_type_absence()

        defaults = {
            'employe': employe,
            'type_absence': type_absence,
            'date_debut': date.today() + timedelta(days=10),
            'date_fin': date.today() + timedelta(days=15),
            'periode': 'JOURNEE_COMPLETE',
            'motif': 'Test absence',
            'statut': 'BROUILLON',
            'created_by': employe,
        }
        defaults.update(kwargs)
        return Absence.objects.create(**defaults)

    def create_jour_ferie(self, nom='Jour de test', date_ferie=None, **kwargs):
        """Créer un jour férié de test."""
        from absence.models import JourFerie
        if date_ferie is None:
            date_ferie = date.today() + timedelta(days=30)
        defaults = {
            'nom': nom,
            'date': date_ferie,
            'type_ferie': 'LEGAL',
            'actif': True,
        }
        defaults.update(kwargs)
        return JourFerie.objects.create(**defaults)

    # ==========================================
    # Helpers Frais
    # ==========================================

    def create_categorie_frais(self, code='TRN', libelle='Transport', **kwargs):
        """Créer une catégorie de frais de test."""
        from frais.models import NFCA
        defaults = {
            'CODE': code,
            'LIBELLE': libelle,
            'DESCRIPTION': 'Catégorie test',
            'STATUT': True,
        }
        defaults.update(kwargs)
        return NFCA.objects.create(**defaults)

    def create_note_frais(self, employe=None, **kwargs):
        """Créer une note de frais de test."""
        from frais.models import NFNF
        if employe is None:
            employe = self.employe
        defaults = {
            'EMPLOYE': employe,
            'PERIODE_DEBUT': date.today() - timedelta(days=30),
            'PERIODE_FIN': date.today(),
            'OBJET': 'Note de test',
            'STATUT': 'BROUILLON',
        }
        defaults.update(kwargs)
        return NFNF.objects.create(**defaults)

    # ==========================================
    # Helpers Gestion Achats
    # ==========================================

    def create_entreprise(self, code='TST', **kwargs):
        """Créer une entreprise de test."""
        from entreprise.models import Entreprise
        defaults = {
            'code': code,
            'nom': 'Entreprise Test',
            'adresse': '123 Rue Test',
            'ville': 'Lomé',
            'pays': 'TOGO',
        }
        defaults.update(kwargs)
        return Entreprise.objects.create(**defaults)

    def create_fournisseur(self, raison_sociale='Fournisseur Test', **kwargs):
        """Créer un fournisseur de test."""
        from gestion_achats.models import GACFournisseur
        defaults = {
            'raison_sociale': raison_sociale,
            'email': 'fournisseur@test.com',
            'telephone': '+228 90 00 00 00',
            'adresse': 'Lomé, Togo',
            'pays': 'Togo',
            'statut': 'ACTIF',
        }
        defaults.update(kwargs)
        return GACFournisseur.objects.create(**defaults)

    def create_categorie_achat(self, nom='Fournitures', **kwargs):
        """Créer une catégorie d'achat de test."""
        from gestion_achats.models import GACCategorie
        defaults = {
            'nom': nom,
            'description': 'Catégorie test',
            'actif': True,
        }
        defaults.update(kwargs)
        return GACCategorie.objects.create(**defaults)

    def create_demande_achat(self, demandeur=None, **kwargs):
        """Créer une demande d'achat de test."""
        from gestion_achats.models import GACDemandeAchat
        if demandeur is None:
            demandeur = self.employe
        defaults = {
            'demandeur': demandeur,
            'objet': 'Demande de test',
            'justification': 'Justification de test',
            'priorite': 'NORMALE',
            'statut': 'BROUILLON',
        }
        defaults.update(kwargs)
        return GACDemandeAchat.objects.create(**defaults)

    # ==========================================
    # Helpers Matériel
    # ==========================================

    def create_categorie_materiel(self, code='INF', libelle='Informatique', **kwargs):
        """Créer une catégorie de matériel de test."""
        from materiel.models import MTCA
        defaults = {
            'CODE': code,
            'LIBELLE': libelle,
            'STATUT': True,
        }
        defaults.update(kwargs)
        return MTCA.objects.create(**defaults)

    def create_fournisseur_materiel(self, raison_sociale='Fournisseur Mat', **kwargs):
        """Créer un fournisseur de matériel de test."""
        from materiel.models import MTFO
        defaults = {
            'RAISON_SOCIALE': raison_sociale,
            'CONTACT': 'Contact Test',
            'TELEPHONE': '+228 90 00 00 00',
            'EMAIL': 'fournisseur@mat.com',
            'STATUT': True,
        }
        defaults.update(kwargs)
        return MTFO.objects.create(**defaults)

    # ==========================================
    # Helpers rôles
    # ==========================================

    def create_drh_user(self):
        """Créer un utilisateur avec le rôle DRH."""
        employe_drh = self.create_employee(
            matricule='DRH00001',
            nom='Martin',
            prenoms='Pierre',
        )
        user_drh = self.create_user_for_employee(employe_drh)
        self.assign_role(employe_drh, self.role_drh)
        return employe_drh, user_drh

    def create_manager_user(self):
        """Créer un utilisateur avec le rôle MANAGER."""
        employe_mgr = self.create_employee(
            matricule='MGR00001',
            nom='Bernard',
            prenoms='Alain',
        )
        user_mgr = self.create_user_for_employee(employe_mgr)
        self.assign_role(employe_mgr, self.role_manager)
        self.assign_as_manager(employe_mgr)
        return employe_mgr, user_mgr

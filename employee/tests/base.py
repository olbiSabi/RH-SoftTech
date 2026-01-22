# employee/tests/base.py
"""
Classes et helpers de base pour les tests de l'application employee.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User

from employee.models import ZY00, ZYRO, ZYRE, ZYCO, ZYAF
from departement.models import ZDDE, ZDPO, ZYMA


class EmployeeTestCase(TestCase):
    """Classe de base pour les tests employee avec helpers de création."""

    @classmethod
    def setUpTestData(cls):
        """Créer les données de test une seule fois pour toute la classe."""
        # Créer un département de test
        cls.departement = ZDDE.objects.create(
            CODE='TST',
            LIBELLE='Département Test',
            STATUT=True
        )

        # Créer un poste de test
        cls.poste = ZDPO.objects.create(
            CODE='POST01',
            LIBELLE='Poste Test',
            DEPARTEMENT=cls.departement,
            STATUT=True
        )

        # Créer les rôles de base
        cls.role_drh = ZYRO.objects.create(
            CODE='DRH',
            LIBELLE='Directeur des Ressources Humaines',
            actif=True
        )
        cls.role_manager = ZYRO.objects.create(
            CODE='MANAGER',
            LIBELLE='Manager',
            actif=True
        )
        cls.role_assistant_rh = ZYRO.objects.create(
            CODE='ASSISTANT_RH',
            LIBELLE='Assistant RH',
            actif=True
        )

    def create_employee(self, matricule=None, nom='Test', prenoms='Employe',
                        etat='actif', type_dossier='SAL', **kwargs):
        """Helper pour créer un employé de test."""
        if matricule is None:
            # Générer un matricule unique
            count = ZY00.objects.count()
            matricule = f'TEST{count:04d}'

        defaults = {
            'matricule': matricule,
            'nom': nom,
            'prenoms': prenoms,
            'date_naissance': date(1990, 1, 1),
            'sexe': 'M',
            'type_id': 'CNI',
            'numero_id': f'ID{matricule}',
            'date_validite_id': date(2020, 1, 1),
            'date_expiration_id': date(2030, 1, 1),
            'type_dossier': type_dossier,
            'etat': etat,
        }
        defaults.update(kwargs)

        return ZY00.objects.create(**defaults)

    def create_user_for_employee(self, employee, password='testpass123'):
        """Helper pour créer un utilisateur Django lié à un employé."""
        user = User.objects.create_user(
            username=employee.matricule,
            email=f'{employee.matricule}@test.com',
            password=password
        )
        employee.user = user
        employee.save()
        return user

    def create_contract(self, employee, type_contrat='CDI', date_debut=None,
                        date_fin=None, actif=True):
        """Helper pour créer un contrat de test."""
        if date_debut is None:
            date_debut = date.today() - timedelta(days=365)

        return ZYCO.objects.create(
            employe=employee,
            type_contrat=type_contrat,
            date_debut=date_debut,
            date_fin=date_fin,
            actif=actif
        )

    def create_affectation(self, employee, poste=None, date_debut=None,
                           date_fin=None):
        """Helper pour créer une affectation de test."""
        if poste is None:
            poste = self.poste
        if date_debut is None:
            date_debut = date.today() - timedelta(days=365)

        return ZYAF.objects.create(
            employe=employee,
            poste=poste,
            date_debut=date_debut,
            date_fin=date_fin
        )

    def assign_role(self, employee, role, date_debut=None, actif=True):
        """Helper pour attribuer un rôle à un employé."""
        if date_debut is None:
            date_debut = date.today()

        return ZYRE.objects.create(
            employe=employee,
            role=role,
            date_debut=date_debut,
            actif=actif
        )

    def assign_as_manager(self, employee, departement=None, date_debut=None, actif=True):
        """Helper pour assigner un employé comme manager d'un département via ZYMA."""
        if departement is None:
            departement = self.departement
        if date_debut is None:
            date_debut = date.today()

        return ZYMA.objects.create(
            employe=employee,
            departement=departement,
            date_debut=date_debut,
            date_fin=None,
            actif=actif
        )

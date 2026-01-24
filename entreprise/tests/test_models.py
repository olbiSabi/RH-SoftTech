# entreprise/tests/test_models.py
"""Tests pour le modèle Entreprise."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date

from entreprise.models import Entreprise


class EntrepriseModelTest(TestCase):
    """Tests pour le modèle Entreprise."""

    def test_create_entreprise(self):
        """Test création d'une entreprise."""
        entreprise = Entreprise.objects.create(
            code='ENT001',
            nom='Test Entreprise',
            adresse='123 Rue Test',
            ville='Lomé',
            pays='TOGO'
        )
        self.assertEqual(entreprise.code, 'ENT001')
        self.assertEqual(entreprise.nom, 'TEST ENTREPRISE')  # Majuscules
        self.assertTrue(entreprise.actif)

    def test_nom_uppercase(self):
        """Test que le nom est converti en majuscules."""
        entreprise = Entreprise.objects.create(
            code='ENT002',
            nom='entreprise test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertEqual(entreprise.nom, 'ENTREPRISE TEST')

    def test_pays_uppercase(self):
        """Test que le pays est converti en majuscules."""
        entreprise = Entreprise.objects.create(
            code='ENT003',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé',
            pays='togo'
        )
        self.assertEqual(entreprise.pays, 'TOGO')

    def test_pays_default(self):
        """Test la valeur par défaut du pays."""
        entreprise = Entreprise.objects.create(
            code='ENT004',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertEqual(entreprise.pays, 'TOGO')

    def test_uuid_generated(self):
        """Test que l'UUID est généré automatiquement."""
        entreprise = Entreprise.objects.create(
            code='ENT005',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertIsNotNone(entreprise.uuid)

    def test_code_unique(self):
        """Test que le code est unique."""
        Entreprise.objects.create(
            code='UNIQUE',
            nom='Test 1',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        with self.assertRaises(Exception):  # IntegrityError
            Entreprise.objects.create(
                code='UNIQUE',
                nom='Test 2',
                adresse='456 Rue Test',
                ville='Lomé'
            )

    def test_str_representation(self):
        """Test la représentation string."""
        entreprise = Entreprise.objects.create(
            code='STR001',
            nom='Ma Société',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertEqual(str(entreprise), 'MA SOCIÉTÉ (STR001)')

    def test_db_table_name(self):
        """Test le nom de la table en base."""
        self.assertEqual(Entreprise._meta.db_table, 'ENTREPRISE')

    def test_ordering(self):
        """Test l'ordre par défaut."""
        self.assertEqual(Entreprise._meta.ordering, ['nom'])

    def test_effectif_total_sans_employes(self):
        """Test l'effectif total sans employés."""
        entreprise = Entreprise.objects.create(
            code='EFF001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertEqual(entreprise.effectif_total, 0)

    def test_convention_en_vigueur_sans_convention(self):
        """Test la convention en vigueur sans convention."""
        entreprise = Entreprise.objects.create(
            code='CNV001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertIsNone(entreprise.convention_en_vigueur)

    def test_actif_default(self):
        """Test que actif est True par défaut."""
        entreprise = Entreprise.objects.create(
            code='ACT001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertTrue(entreprise.actif)

    def test_optional_fields_blank(self):
        """Test que les champs optionnels peuvent être vides."""
        entreprise = Entreprise.objects.create(
            code='OPT001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertEqual(entreprise.raison_sociale, '')
        self.assertEqual(entreprise.sigle, '')
        self.assertEqual(entreprise.telephone, '')
        self.assertEqual(entreprise.email, '')
        self.assertEqual(entreprise.site_web, '')
        self.assertEqual(entreprise.rccm, '')
        self.assertEqual(entreprise.numero_impot, '')
        self.assertEqual(entreprise.numero_cnss, '')
        self.assertEqual(entreprise.description, '')

    def test_date_creation_nullable(self):
        """Test que date_creation peut être null."""
        entreprise = Entreprise.objects.create(
            code='DAT001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertIsNone(entreprise.date_creation)

    def test_date_creation_with_value(self):
        """Test date_creation avec une valeur."""
        entreprise = Entreprise.objects.create(
            code='DAT002',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé',
            date_creation=date(2020, 1, 1)
        )
        self.assertEqual(entreprise.date_creation, date(2020, 1, 1))

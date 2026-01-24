# departement/tests/test_models.py
"""Tests pour les modèles de l'application departement."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from departement.models import ZDDE, ZDPO, ZYMA


class ZDDEModelTest(TestCase):
    """Tests pour le modèle ZDDE (Département)."""

    def test_create_departement(self):
        """Test création d'un département."""
        dept = ZDDE.objects.create(
            CODE='RHU',
            LIBELLE='Ressources Humaines',
            STATUT=True
        )
        self.assertEqual(dept.CODE, 'RHU')
        self.assertEqual(dept.LIBELLE, 'Ressources Humaines')
        self.assertTrue(dept.STATUT)

    def test_code_uppercase(self):
        """Test que le code est converti en majuscules."""
        dept = ZDDE.objects.create(
            CODE='abc',
            LIBELLE='Test',
            STATUT=True
        )
        self.assertEqual(dept.CODE, 'ABC')

    def test_code_stripped(self):
        """Test que le code est nettoyé des espaces."""
        dept = ZDDE.objects.create(
            CODE=' DEF ',
            LIBELLE='Test',
            STATUT=True
        )
        self.assertEqual(dept.CODE, 'DEF')

    def test_code_must_be_3_chars(self):
        """Test que le code doit avoir exactement 3 caractères."""
        with self.assertRaises(ValidationError) as context:
            ZDDE.objects.create(CODE='AB', LIBELLE='Test')
        self.assertIn('CODE', str(context.exception))

    def test_code_must_be_alpha(self):
        """Test que le code ne doit contenir que des lettres."""
        with self.assertRaises(ValidationError) as context:
            ZDDE.objects.create(CODE='AB1', LIBELLE='Test')
        self.assertIn('CODE', str(context.exception))

    def test_libelle_first_char_uppercase(self):
        """Test que le premier caractère du libellé est en majuscule."""
        dept = ZDDE.objects.create(
            CODE='TST',
            LIBELLE='test département',
            STATUT=True
        )
        self.assertEqual(dept.LIBELLE, 'Test département')

    def test_date_fin_must_be_after_date_debut(self):
        """Test que la date de fin doit être après la date de début."""
        with self.assertRaises(ValidationError) as context:
            ZDDE.objects.create(
                CODE='TST',
                LIBELLE='Test',
                DATEDEB=date.today(),
                DATEFIN=date.today() - timedelta(days=1)
            )
        self.assertIn('DATEFIN', str(context.exception))

    def test_str_representation(self):
        """Test la représentation string du département."""
        dept = ZDDE.objects.create(
            CODE='TST',
            LIBELLE='Test Département',
            STATUT=True
        )
        self.assertEqual(str(dept), 'Test Département')

    def test_db_table_name(self):
        """Test le nom de la table en base."""
        self.assertEqual(ZDDE._meta.db_table, 'ZDDE')


class ZDPOModelTest(TestCase):
    """Tests pour le modèle ZDPO (Poste)."""

    @classmethod
    def setUpTestData(cls):
        """Créer un département pour les tests."""
        cls.departement = ZDDE.objects.create(
            CODE='TST',
            LIBELLE='Test Département',
            STATUT=True
        )

    def test_create_poste(self):
        """Test création d'un poste."""
        poste = ZDPO.objects.create(
            CODE='PST001',
            LIBELLE='Développeur',
            DEPARTEMENT=self.departement,
            STATUT=True
        )
        self.assertEqual(poste.CODE, 'PST001')
        self.assertEqual(poste.LIBELLE, 'Développeur')
        self.assertEqual(poste.DEPARTEMENT, self.departement)

    def test_code_uppercase(self):
        """Test que le code est converti en majuscules."""
        poste = ZDPO.objects.create(
            CODE='pst002',
            LIBELLE='Test',
            DEPARTEMENT=self.departement
        )
        self.assertEqual(poste.CODE, 'PST002')

    def test_code_must_be_6_chars(self):
        """Test que le code doit avoir exactement 6 caractères."""
        with self.assertRaises(ValidationError) as context:
            ZDPO.objects.create(
                CODE='PST',
                LIBELLE='Test',
                DEPARTEMENT=self.departement
            )
        self.assertIn('CODE', str(context.exception))

    def test_code_must_be_alphanumeric(self):
        """Test que le code doit être alphanumérique."""
        with self.assertRaises(ValidationError) as context:
            ZDPO.objects.create(
                CODE='PST-01',
                LIBELLE='Test',
                DEPARTEMENT=self.departement
            )
        self.assertIn('CODE', str(context.exception))

    def test_libelle_first_char_uppercase(self):
        """Test que le premier caractère du libellé est en majuscule."""
        poste = ZDPO.objects.create(
            CODE='PST003',
            LIBELLE='développeur senior',
            DEPARTEMENT=self.departement
        )
        self.assertEqual(poste.LIBELLE, 'Développeur senior')

    def test_date_fin_must_be_after_date_debut(self):
        """Test que la date de fin doit être après la date de début."""
        with self.assertRaises(ValidationError) as context:
            ZDPO.objects.create(
                CODE='PST004',
                LIBELLE='Test',
                DEPARTEMENT=self.departement,
                DATEDEB=date.today(),
                DATEFIN=date.today() - timedelta(days=1)
            )
        self.assertIn('DATEFIN', str(context.exception))

    def test_str_representation(self):
        """Test la représentation string du poste."""
        poste = ZDPO.objects.create(
            CODE='PST005',
            LIBELLE='Analyste',
            DEPARTEMENT=self.departement
        )
        self.assertEqual(str(poste), 'PST005 - Analyste')

    def test_db_table_name(self):
        """Test le nom de la table en base."""
        self.assertEqual(ZDPO._meta.db_table, 'ZDPO')

    def test_related_name_postes(self):
        """Test la relation inverse avec le département."""
        poste = ZDPO.objects.create(
            CODE='PST006',
            LIBELLE='Chef de projet',
            DEPARTEMENT=self.departement
        )
        self.assertIn(poste, self.departement.postes.all())

    def test_ordering(self):
        """Test l'ordre par défaut."""
        self.assertEqual(ZDPO._meta.ordering, ['CODE'])


class ZYMAModelTest(TestCase):
    """Tests pour le modèle ZYMA (Manager)."""

    @classmethod
    def setUpTestData(cls):
        """Créer les données de test."""
        cls.departement = ZDDE.objects.create(
            CODE='TST',
            LIBELLE='Test Département',
            STATUT=True
        )
        cls.departement2 = ZDDE.objects.create(
            CODE='DEV',
            LIBELLE='Développement',
            STATUT=True
        )

    def test_db_table_name(self):
        """Test le nom de la table en base."""
        self.assertEqual(ZYMA._meta.db_table, 'ZYMA')

    def test_verbose_name(self):
        """Test les noms verbeux."""
        self.assertEqual(ZYMA._meta.verbose_name, 'Manager de département')
        self.assertEqual(ZYMA._meta.verbose_name_plural, 'Managers de département')

    def test_ordering(self):
        """Test l'ordre par défaut."""
        self.assertEqual(ZYMA._meta.ordering, ['-date_debut', 'departement__LIBELLE'])

    def test_classmethod_get_departements_sans_manager(self):
        """Test récupération des départements sans manager."""
        # Aucun manager, les 2 départements sont sans manager
        depts_sans_manager = ZYMA.get_departements_sans_manager()
        self.assertEqual(depts_sans_manager.count(), 2)
        self.assertIn(self.departement, depts_sans_manager)
        self.assertIn(self.departement2, depts_sans_manager)

    def test_classmethod_get_manager_actif_none(self):
        """Test récupération du manager actif quand aucun."""
        manager = ZYMA.get_manager_actif(self.departement)
        self.assertIsNone(manager)

# entreprise/tests/test_services.py
"""Tests pour les services de l'application entreprise."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from unittest.mock import Mock, patch

from entreprise.models import Entreprise
from entreprise.services import EntrepriseService


class EntrepriseServiceTest(TestCase):
    """Tests pour EntrepriseService."""

    def test_entreprise_existe_false(self):
        """Test entreprise_existe quand aucune entreprise."""
        self.assertFalse(EntrepriseService.entreprise_existe())

    def test_entreprise_existe_true(self):
        """Test entreprise_existe quand une entreprise existe."""
        Entreprise.objects.create(
            code='TST001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        self.assertTrue(EntrepriseService.entreprise_existe())

    def test_get_entreprise_none(self):
        """Test get_entreprise quand aucune entreprise."""
        self.assertIsNone(EntrepriseService.get_entreprise())

    def test_get_entreprise_exists(self):
        """Test get_entreprise quand une entreprise existe."""
        created = Entreprise.objects.create(
            code='TST002',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        entreprise = EntrepriseService.get_entreprise()
        self.assertEqual(entreprise.pk, created.pk)

    def test_create_entreprise(self):
        """Test création d'une entreprise via service."""
        entreprise = EntrepriseService.create_entreprise(
            code='NEW001',
            nom='Nouvelle Entreprise',
            adresse='456 Rue Nouvelle',
            ville='Lomé'
        )
        self.assertIsNotNone(entreprise)
        self.assertEqual(entreprise.code, 'NEW001')

    def test_create_entreprise_duplicate(self):
        """Test création d'une entreprise quand une existe déjà."""
        Entreprise.objects.create(
            code='DUP001',
            nom='Existante',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        with self.assertRaises(ValidationError) as context:
            EntrepriseService.create_entreprise(
                code='DUP002',
                nom='Nouvelle',
                adresse='456 Rue Test',
                ville='Lomé'
            )
        self.assertIn('existe déjà', str(context.exception))

    def test_update_entreprise(self):
        """Test mise à jour d'une entreprise."""
        entreprise = Entreprise.objects.create(
            code='UPD001',
            nom='Original',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        updated = EntrepriseService.update_entreprise(
            entreprise,
            nom='Modifié',
            ville='Kara'
        )
        self.assertEqual(updated.nom, 'MODIFIÉ')
        self.assertEqual(updated.ville, 'Kara')

    def test_get_entreprise_by_uuid(self):
        """Test récupération par UUID."""
        created = Entreprise.objects.create(
            code='UUID01',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        entreprise = EntrepriseService.get_entreprise_by_uuid(created.uuid)
        self.assertEqual(entreprise.pk, created.pk)

    def test_get_entreprise_by_uuid_not_found(self):
        """Test récupération par UUID inexistant."""
        import uuid
        entreprise = EntrepriseService.get_entreprise_by_uuid(uuid.uuid4())
        self.assertIsNone(entreprise)

    def test_get_entreprise_by_code(self):
        """Test récupération par code."""
        Entreprise.objects.create(
            code='COD001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        entreprise = EntrepriseService.get_entreprise_by_code('COD001')
        self.assertIsNotNone(entreprise)
        self.assertEqual(entreprise.code, 'COD001')

    def test_get_entreprise_by_code_not_found(self):
        """Test récupération par code inexistant."""
        entreprise = EntrepriseService.get_entreprise_by_code('XXXXX')
        self.assertIsNone(entreprise)

    def test_activer_entreprise(self):
        """Test activation d'une entreprise."""
        entreprise = Entreprise.objects.create(
            code='ACT001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé',
            actif=False
        )
        result = EntrepriseService.activer_entreprise(entreprise)
        entreprise.refresh_from_db()

        self.assertTrue(result)
        self.assertTrue(entreprise.actif)

    def test_desactiver_entreprise(self):
        """Test désactivation d'une entreprise."""
        entreprise = Entreprise.objects.create(
            code='DES001',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé',
            actif=True
        )
        result = EntrepriseService.desactiver_entreprise(entreprise)
        entreprise.refresh_from_db()

        self.assertTrue(result)
        self.assertFalse(entreprise.actif)

    def test_valider_code_valid(self):
        """Test validation d'un code valide."""
        is_valid, errors = EntrepriseService.valider_code('NEWCODE')
        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_valider_code_empty(self):
        """Test validation d'un code vide."""
        is_valid, errors = EntrepriseService.valider_code('')
        self.assertFalse(is_valid)
        self.assertIn('code', errors)

    def test_valider_code_too_long(self):
        """Test validation d'un code trop long."""
        is_valid, errors = EntrepriseService.valider_code('A' * 15)
        self.assertFalse(is_valid)
        self.assertIn('code', errors)

    def test_valider_code_duplicate(self):
        """Test validation d'un code déjà existant."""
        Entreprise.objects.create(
            code='EXIST',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        is_valid, errors = EntrepriseService.valider_code('EXIST')
        self.assertFalse(is_valid)
        self.assertIn('code', errors)

    def test_valider_code_exclude_pk(self):
        """Test validation avec exclusion du pk courant."""
        entreprise = Entreprise.objects.create(
            code='EXCL01',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        is_valid, errors = EntrepriseService.valider_code('EXCL01', exclude_pk=entreprise.pk)
        self.assertTrue(is_valid)

    def test_get_statistiques_sans_entreprise(self):
        """Test statistiques sans entreprise."""
        stats = EntrepriseService.get_statistiques()

        self.assertFalse(stats['entreprise_existe'])
        self.assertEqual(stats['effectif_total'], 0)

    def test_get_statistiques_avec_entreprise(self):
        """Test statistiques avec entreprise."""
        entreprise = Entreprise.objects.create(
            code='STAT01',
            nom='Test Stats',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        stats = EntrepriseService.get_statistiques(entreprise)

        self.assertTrue(stats['entreprise_existe'])
        self.assertEqual(stats['nom'], 'TEST STATS')
        self.assertEqual(stats['code'], 'STAT01')
        self.assertEqual(stats['effectif_total'], 0)

    def test_to_dict(self):
        """Test conversion en dictionnaire."""
        entreprise = Entreprise.objects.create(
            code='DICT01',
            nom='Test Dict',
            adresse='123 Rue Test',
            ville='Lomé',
            pays='TOGO'
        )
        data = EntrepriseService.to_dict(entreprise)

        self.assertEqual(data['code'], 'DICT01')
        self.assertEqual(data['nom'], 'TEST DICT')
        self.assertEqual(data['ville'], 'Lomé')
        self.assertEqual(data['pays'], 'TOGO')
        self.assertIn('uuid', data)
        self.assertIn('effectif_total', data)

    def test_get_convention_en_vigueur_sans_entreprise(self):
        """Test convention en vigueur sans entreprise."""
        convention = EntrepriseService.get_convention_en_vigueur()
        self.assertIsNone(convention)

    def test_get_convention_en_vigueur_sans_convention(self):
        """Test convention en vigueur sans convention définie."""
        entreprise = Entreprise.objects.create(
            code='CONV01',
            nom='Test',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        convention = EntrepriseService.get_convention_en_vigueur(entreprise)
        self.assertIsNone(convention)

    def test_delete_entreprise_sans_employes(self):
        """Test suppression d'une entreprise sans employés."""
        entreprise = Entreprise.objects.create(
            code='DEL001',
            nom='A Supprimer',
            adresse='123 Rue Test',
            ville='Lomé'
        )
        pk = entreprise.pk

        result = EntrepriseService.delete_entreprise(entreprise)

        self.assertTrue(result)
        self.assertFalse(Entreprise.objects.filter(pk=pk).exists())


class EntrepriseServiceConventionTest(TestCase):
    """Tests pour les méthodes liées aux conventions."""

    def test_get_conventions_disponibles_empty(self):
        """Test récupération conventions quand aucune."""
        # Le test ne crée pas de conventions, donc le résultat dépend
        # de l'état de la base de données
        conventions = EntrepriseService.get_conventions_disponibles()
        # Vérifie juste que ça ne lève pas d'exception
        self.assertIsNotNone(conventions)

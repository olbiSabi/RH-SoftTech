# frais/test_forms.py
"""
Tests pour les formulaires du module Notes de Frais.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from core.tests.base import BaseTestCase
from frais.models import NFCA, NFPL, NFNF, NFLF, NFAV
from frais.forms import (
    NoteFraisForm,
    LigneFraisForm,
    AvanceForm,
    CategorieForm,
    PlafondForm,
    ValidationLigneForm,
    RejetForm,
    RemboursementForm,
    VersementAvanceForm,
    FiltreNotesForm,
    FiltreAvancesForm,
)


# =============================================
# Tests NoteFraisForm
# =============================================

class TestNoteFraisForm(BaseTestCase):
    """Tests pour le formulaire NoteFrais."""

    def get_valid_data(self):
        return {
            'PERIODE_DEBUT': date.today() - timedelta(days=30),
            'PERIODE_FIN': date.today(),
            'OBJET': 'Mission Lomé du 1er au 30 janvier',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = NoteFraisForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_fin_before_debut(self):
        """Test date fin antérieure à date début."""
        data = self.get_valid_data()
        data['PERIODE_FIN'] = date.today() - timedelta(days=60)
        form = NoteFraisForm(data=data)
        self.assertFalse(form.is_valid())

    def test_same_dates_valid(self):
        """Test mêmes dates début/fin (une seule journée)."""
        data = self.get_valid_data()
        data['PERIODE_DEBUT'] = date.today()
        data['PERIODE_FIN'] = date.today()
        form = NoteFraisForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests LigneFraisForm
# =============================================

class TestLigneFraisForm(BaseTestCase):
    """Tests pour le formulaire LigneFrais."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.categorie = NFCA.objects.create(
            CODE='TRN',
            LIBELLE='Transport',
            DESCRIPTION='Frais de transport',
            JUSTIFICATIF_OBLIGATOIRE=False,
            STATUT=True,
        )
        cls.categorie_justif = NFCA.objects.create(
            CODE='HTL',
            LIBELLE='Hébergement',
            DESCRIPTION='Frais hôtel',
            JUSTIFICATIF_OBLIGATOIRE=True,
            STATUT=True,
        )

    def setUp(self):
        super().setUp()
        self.note = self.create_note_frais()

    def get_valid_data(self):
        return {
            'CATEGORIE': self.categorie.pk,
            'DATE_DEPENSE': date.today() - timedelta(days=15),
            'DESCRIPTION': 'Taxi aéroport',
            'MONTANT': Decimal('5000'),
            'DEVISE': 'XOF',
            'NUMERO_FACTURE': 'FAC001',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = LigneFraisForm(data=self.get_valid_data(), note_frais=self.note)
        self.assertTrue(form.is_valid(), form.errors)

    def test_montant_zero_invalid(self):
        """Test montant zéro invalide."""
        data = self.get_valid_data()
        data['MONTANT'] = Decimal('0')
        form = LigneFraisForm(data=data, note_frais=self.note)
        self.assertFalse(form.is_valid())
        self.assertIn('MONTANT', form.errors)

    def test_montant_negative_invalid(self):
        """Test montant négatif invalide."""
        data = self.get_valid_data()
        data['MONTANT'] = Decimal('-100')
        form = LigneFraisForm(data=data, note_frais=self.note)
        self.assertFalse(form.is_valid())
        self.assertIn('MONTANT', form.errors)

    def test_date_outside_period_invalid(self):
        """Test date en dehors de la période de la note."""
        data = self.get_valid_data()
        data['DATE_DEPENSE'] = date.today() + timedelta(days=30)
        form = LigneFraisForm(data=data, note_frais=self.note)
        self.assertFalse(form.is_valid())
        self.assertIn('DATE_DEPENSE', form.errors)

    def test_date_within_period_valid(self):
        """Test date dans la période de la note."""
        data = self.get_valid_data()
        data['DATE_DEPENSE'] = date.today() - timedelta(days=10)
        form = LigneFraisForm(data=data, note_frais=self.note)
        self.assertTrue(form.is_valid(), form.errors)

    def test_justificatif_required_for_category(self):
        """Test justificatif obligatoire selon catégorie."""
        data = self.get_valid_data()
        data['CATEGORIE'] = self.categorie_justif.pk
        form = LigneFraisForm(data=data, note_frais=self.note)
        self.assertFalse(form.is_valid())

    def test_only_active_categories_shown(self):
        """Test seules les catégories actives sont affichées."""
        inactive = NFCA.objects.create(
            CODE='INA', LIBELLE='Inactive',
            DESCRIPTION='Cat inactive', STATUT=False,
        )
        form = LigneFraisForm(note_frais=self.note)
        qs_pks = list(form.fields['CATEGORIE'].queryset.values_list('pk', flat=True))
        self.assertNotIn(inactive.pk, qs_pks)
        self.assertIn(self.categorie.pk, qs_pks)


# =============================================
# Tests AvanceForm
# =============================================

class TestAvanceForm(BaseTestCase):
    """Tests pour le formulaire Avance."""

    def get_valid_data(self):
        return {
            'MONTANT_DEMANDE': Decimal('50000'),
            'MOTIF': 'Mission à Kara - frais de déplacement',
            'DATE_MISSION_DEBUT': date.today() + timedelta(days=5),
            'DATE_MISSION_FIN': date.today() + timedelta(days=10),
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = AvanceForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_montant_below_minimum(self):
        """Test montant en dessous du minimum (1000 XOF)."""
        data = self.get_valid_data()
        data['MONTANT_DEMANDE'] = Decimal('500')
        form = AvanceForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('MONTANT_DEMANDE', form.errors)

    def test_montant_exact_minimum(self):
        """Test montant exactement au minimum."""
        data = self.get_valid_data()
        data['MONTANT_DEMANDE'] = Decimal('1000')
        form = AvanceForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_fin_before_debut(self):
        """Test date fin mission avant début."""
        data = self.get_valid_data()
        data['DATE_MISSION_FIN'] = date.today() + timedelta(days=2)
        data['DATE_MISSION_DEBUT'] = date.today() + timedelta(days=10)
        form = AvanceForm(data=data)
        self.assertFalse(form.is_valid())


# =============================================
# Tests CategorieForm
# =============================================

class TestCategorieForm(BaseTestCase):
    """Tests pour le formulaire Catégorie de frais."""

    def get_valid_data(self):
        return {
            'CODE': 'REP',
            'LIBELLE': 'Repas',
            'DESCRIPTION': 'Frais de repas',
            'JUSTIFICATIF_OBLIGATOIRE': False,
            'PLAFOND_DEFAUT': Decimal('15000'),
            'ICONE': 'fa-utensils',
            'ORDRE': 1,
            'STATUT': True,
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = CategorieForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_code_empty_invalid(self):
        """Test code vide invalide."""
        data = self.get_valid_data()
        data['CODE'] = ''
        form = CategorieForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('CODE', form.errors)


# =============================================
# Tests ValidationLigneForm
# =============================================

class TestValidationLigneForm(BaseTestCase):
    """Tests pour le formulaire de validation de ligne de frais."""

    def test_valid_validation(self):
        """Test validation valide."""
        form = ValidationLigneForm(data={
            'action': 'valider',
            'commentaire': 'OK',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_reject_without_comment(self):
        """Test rejet sans commentaire invalide."""
        form = ValidationLigneForm(data={
            'action': 'rejeter',
            'commentaire': '',
        })
        self.assertFalse(form.is_valid())

    def test_reject_with_comment(self):
        """Test rejet avec commentaire valide."""
        form = ValidationLigneForm(data={
            'action': 'rejeter',
            'commentaire': 'Montant non justifié',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_without_comment(self):
        """Test validation sans commentaire autorisée."""
        form = ValidationLigneForm(data={
            'action': 'valider',
            'commentaire': '',
        })
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests RejetForm
# =============================================

class TestRejetForm(BaseTestCase):
    """Tests pour le formulaire de rejet."""

    def test_comment_required(self):
        """Test commentaire obligatoire pour rejet."""
        form = RejetForm(data={'commentaire': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('commentaire', form.errors)

    def test_valid_rejection(self):
        """Test rejet valide avec commentaire."""
        form = RejetForm(data={'commentaire': 'Justificatif manquant'})
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests FiltreNotesForm et FiltreAvancesForm
# =============================================

class TestFiltreFormsForm(BaseTestCase):
    """Tests pour les formulaires de filtrage."""

    def test_filtre_notes_empty_valid(self):
        """Test formulaire filtre notes vide est valide."""
        form = FiltreNotesForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_filtre_notes_with_statut(self):
        """Test filtre par statut."""
        form = FiltreNotesForm(data={'statut': 'BROUILLON'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_filtre_avances_empty_valid(self):
        """Test formulaire filtre avances vide est valide."""
        form = FiltreAvancesForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

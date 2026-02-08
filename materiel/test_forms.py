# materiel/test_forms.py
"""
Tests pour les formulaires du module Matériel.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from core.tests.base import BaseTestCase
from materiel.models import MTCA, MTFO, MTMT, MTAF, MTMA
from materiel.forms import (
    MTCAForm,
    MTFOForm,
    MTMTForm,
    AffectationForm,
    RetourForm,
    MTMAForm,
    ReformeForm,
    FiltresMaterielForm,
    FiltresMaintenanceForm,
)


# =============================================
# Tests MTCAForm (Catégorie)
# =============================================

class TestMTCAForm(BaseTestCase):
    """Tests pour le formulaire Catégorie de matériel."""

    def get_valid_data(self):
        return {
            'CODE': 'MOB',
            'LIBELLE': 'Mobilier',
            'DESCRIPTION': 'Mobilier de bureau',
            'DUREE_AMORTISSEMENT': 36,
            'ICONE': 'fa-chair',
            'STATUT': True,
            'ORDRE': 0,
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = MTCAForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_code_required(self):
        """Test code obligatoire."""
        data = self.get_valid_data()
        data['CODE'] = ''
        form = MTCAForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('CODE', form.errors)

    def test_libelle_required(self):
        """Test libellé obligatoire."""
        data = self.get_valid_data()
        data['LIBELLE'] = ''
        form = MTCAForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('LIBELLE', form.errors)


# =============================================
# Tests MTFOForm (Fournisseur)
# =============================================

class TestMTFOForm(BaseTestCase):
    """Tests pour le formulaire Fournisseur matériel."""

    def get_valid_data(self):
        return {
            'RAISON_SOCIALE': 'Bureau Plus SARL',
            'CONTACT': 'M. Koffi',
            'TELEPHONE': '+228 90 00 00 00',
            'EMAIL': 'contact@bureauplus.tg',
            'ADRESSE': 'Lomé, Togo',
            'STATUT': True,
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = MTFOForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_raison_sociale_required(self):
        """Test raison sociale obligatoire."""
        data = self.get_valid_data()
        data['RAISON_SOCIALE'] = ''
        form = MTFOForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('RAISON_SOCIALE', form.errors)

    def test_email_format_validation(self):
        """Test validation format email."""
        data = self.get_valid_data()
        data['EMAIL'] = 'pas-un-email'
        form = MTFOForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('EMAIL', form.errors)


# =============================================
# Tests MTMTForm (Matériel)
# =============================================

class TestMTMTForm(BaseTestCase):
    """Tests pour le formulaire Matériel."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.categorie_mat = MTCA.objects.create(
            CODE='INF', LIBELLE='Informatique', STATUT=True,
        )
        cls.fournisseur_mat = MTFO.objects.create(
            RAISON_SOCIALE='Tech Store', CONTACT='Contact',
            TELEPHONE='+228 90 00 00 00', STATUT=True,
        )

    def get_valid_data(self):
        return {
            'CATEGORIE': self.categorie_mat.pk,
            'DESIGNATION': 'Ordinateur portable HP',
            'NUMERO_SERIE': 'SN123456789',
            'DATE_ACQUISITION': date.today().isoformat(),
            'PRIX_ACQUISITION': Decimal('450000'),
            'ETAT': 'NEUF',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = MTMTForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_designation_required(self):
        """Test désignation obligatoire."""
        data = self.get_valid_data()
        data['DESIGNATION'] = ''
        form = MTMTForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('DESIGNATION', form.errors)

    def test_categorie_required(self):
        """Test catégorie obligatoire."""
        data = self.get_valid_data()
        data['CATEGORIE'] = ''
        form = MTMTForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('CATEGORIE', form.errors)


# =============================================
# Tests AffectationForm
# =============================================

class TestAffectationForm(BaseTestCase):
    """Tests pour le formulaire Affectation."""

    def get_valid_data(self):
        return {
            'employe_id': self.employe.matricule,
            'type_affectation': 'AFFECTATION',
            'motif': 'Attribution poste de travail',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = AffectationForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_employe_id_required(self):
        """Test employe_id obligatoire."""
        data = self.get_valid_data()
        data['employe_id'] = ''
        form = AffectationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_pret_requires_date_retour(self):
        """Test prêt nécessite date de retour."""
        data = self.get_valid_data()
        data['type_affectation'] = 'PRET'
        data['date_retour_prevue'] = ''
        form = AffectationForm(data=data)
        self.assertFalse(form.is_valid())


# =============================================
# Tests MTMAForm (Maintenance)
# =============================================

class TestMTMAForm(BaseTestCase):
    """Tests pour le formulaire Maintenance."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.categorie_mat = MTCA.objects.create(
            CODE='MNT', LIBELLE='Informatique', STATUT=True,
        )

    def get_valid_data(self):
        return {
            'TYPE_MAINTENANCE': 'CORRECTIVE',
            'DESCRIPTION': 'Remplacement cartouche',
            'DATE_PLANIFIEE': date.today().isoformat(),
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = MTMAForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_description_required(self):
        """Test description obligatoire."""
        data = self.get_valid_data()
        data['DESCRIPTION'] = ''
        form = MTMAForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('DESCRIPTION', form.errors)


# =============================================
# Tests Filtres
# =============================================

class TestFiltresMaterielForm(BaseTestCase):
    """Tests pour le formulaire de filtres matériel."""

    def test_empty_form_valid(self):
        """Test formulaire vide est valide."""
        form = FiltresMaterielForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_filter_by_statut(self):
        """Test filtre par statut."""
        form = FiltresMaterielForm(data={'statut': 'DISPONIBLE'})
        self.assertTrue(form.is_valid(), form.errors)


class TestFiltresMaintenanceForm(BaseTestCase):
    """Tests pour le formulaire de filtres maintenance."""

    def test_empty_form_valid(self):
        """Test formulaire vide est valide."""
        form = FiltresMaintenanceForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_filter_by_type(self):
        """Test filtre par type de maintenance."""
        form = FiltresMaintenanceForm(data={'type_maintenance': 'CORRECTIVE'})
        self.assertTrue(form.is_valid(), form.errors)

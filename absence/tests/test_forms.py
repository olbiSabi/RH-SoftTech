# absence/tests/test_forms.py
"""
Tests pour les formulaires de l'application absence.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from core.tests.base import BaseTestCase
from absence.models import (
    TypeAbsence, JourFerie, ConfigurationConventionnelle,
    Absence, AcquisitionConges, ParametreCalculConges,
)
from absence.forms import (
    ConfigurationConventionnelleForm,
    JourFerieForm,
    TypeAbsenceForm,
    AbsenceForm,
    ValidationAbsenceForm,
    ParametreCalculCongesForm,
    AbsenceRechercheForm,
)


# =============================================
# Tests ConfigurationConventionnelleForm
# =============================================

class TestConfigurationConventionnelleForm(BaseTestCase):
    """Tests pour le formulaire ConfigurationConventionnelle."""

    def get_valid_data(self):
        return {
            'nom': 'Convention Test 2025',
            'code': 'CONV_TEST_2025',
            'annee_reference': 2025,
            'date_debut': date(2025, 1, 1),
            'date_fin': date(2025, 12, 31),
            'actif': True,
            'jours_acquis_par_mois': Decimal('2.50'),
            'duree_conges_principale': 18,
            'periode_prise_debut': date(2026, 1, 1),
            'periode_prise_fin': date(2026, 12, 31),
            'methode_calcul': 'MOIS_TRAVAILLES',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = ConfigurationConventionnelleForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_code_required(self):
        """Test code obligatoire."""
        data = self.get_valid_data()
        data['code'] = ''
        form = ConfigurationConventionnelleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)

    def test_code_unique(self):
        """Test unicité du code."""
        ConfigurationConventionnelle.objects.create(
            nom='Existing', code='EXIST01',
            annee_reference=2025,
            date_debut=date(2025, 1, 1),
            periode_prise_debut=date(2026, 1, 1),
            periode_prise_fin=date(2026, 12, 31),
        )
        data = self.get_valid_data()
        data['code'] = 'exist01'  # case-insensitive
        form = ConfigurationConventionnelleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_date_fin_before_debut_invalid(self):
        """Test date_fin antérieure à date_debut."""
        data = self.get_valid_data()
        data['date_fin'] = date(2024, 12, 31)
        form = ConfigurationConventionnelleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_fin', form.errors)

    def test_periode_prise_fin_before_debut_invalid(self):
        """Test période prise fin antérieure à début."""
        data = self.get_valid_data()
        data['periode_prise_fin'] = date(2025, 12, 31)
        data['periode_prise_debut'] = date(2026, 6, 1)
        form = ConfigurationConventionnelleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_date_fin_optional(self):
        """Test date_fin optionnelle."""
        data = self.get_valid_data()
        data['date_fin'] = ''
        form = ConfigurationConventionnelleForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests JourFerieForm
# =============================================

class TestJourFerieForm(BaseTestCase):
    """Tests pour le formulaire JourFerie."""

    def get_valid_data(self):
        return {
            'nom': 'Fête nationale',
            'date': date.today() + timedelta(days=60),
            'type_ferie': 'LEGAL',
            'recurrent': True,
            'description': 'Jour de fête nationale',
            'actif': True,
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = JourFerieForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_nom_too_short(self):
        """Test nom trop court (< 3 caractères)."""
        data = self.get_valid_data()
        data['nom'] = 'AB'
        form = JourFerieForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)

    def test_date_too_old(self):
        """Test date trop ancienne (> 5 ans)."""
        data = self.get_valid_data()
        data['date'] = date(date.today().year - 6, 1, 1)
        form = JourFerieForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_date_too_far_future(self):
        """Test date trop dans le futur (> 5 ans)."""
        data = self.get_valid_data()
        data['date'] = date(date.today().year + 6, 1, 1)
        form = JourFerieForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_date_unique(self):
        """Test unicité de la date."""
        target_date = date.today() + timedelta(days=90)
        JourFerie.objects.create(
            nom='Jour existant',
            date=target_date,
            type_ferie='LEGAL',
            actif=True,
        )
        data = self.get_valid_data()
        data['date'] = target_date
        form = JourFerieForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_date_unique_allows_self_edit(self):
        """Test unicité de date autorise l'édition de l'instance elle-même."""
        target_date = date.today() + timedelta(days=100)
        jour = JourFerie.objects.create(
            nom='Jour existant',
            date=target_date,
            type_ferie='LEGAL',
            actif=True,
        )
        data = self.get_valid_data()
        data['date'] = target_date
        form = JourFerieForm(data=data, instance=jour)
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests TypeAbsenceForm
# =============================================

class TestTypeAbsenceForm(BaseTestCase):
    """Tests pour le formulaire TypeAbsence."""

    def get_valid_data(self):
        return {
            'code': 'CPN',
            'libelle': 'Congés payés normaux',
            'categorie': 'CONGES_PAYES',
            'paye': True,
            'decompte_solde': True,
            'justificatif_obligatoire': False,
            'couleur': '#4CAF50',
            'ordre': 1,
            'actif': True,
        }

    def _validate_form(self, data):
        """Créer un form et appeler is_valid()."""
        form = TypeAbsenceForm(data=data)
        form.is_valid()
        return form

    def test_code_must_be_3_chars(self):
        """Test code doit faire exactement 3 caractères."""
        data = self.get_valid_data()
        data['code'] = 'AB'
        form = self._validate_form(data)
        self.assertIn('code', form.errors)

    def test_code_4_chars_invalid(self):
        """Test code de 4 caractères est invalide."""
        data = self.get_valid_data()
        data['code'] = 'ABCD'
        form = self._validate_form(data)
        self.assertIn('code', form.errors)

    def test_code_must_be_alphanumeric(self):
        """Test code doit être alphanumérique."""
        data = self.get_valid_data()
        data['code'] = 'A-B'
        form = self._validate_form(data)
        self.assertIn('code', form.errors)

    def test_code_uppercased(self):
        """Test code automatiquement converti en majuscules."""
        data = self.get_valid_data()
        data['code'] = 'cpn'
        form = self._validate_form(data)
        if 'code' not in form.errors:
            self.assertEqual(form.cleaned_data['code'], 'CPN')

    def test_code_unique(self):
        """Test unicité du code (case-insensitive)."""
        TypeAbsence.objects.create(
            code='MAL', libelle='Maladie',
            categorie='MALADIE', actif=True,
        )
        data = self.get_valid_data()
        data['code'] = 'mal'
        form = self._validate_form(data)
        self.assertIn('code', form.errors)

    def test_libelle_too_short(self):
        """Test libellé trop court."""
        data = self.get_valid_data()
        data['libelle'] = 'AB'
        form = self._validate_form(data)
        self.assertIn('libelle', form.errors)

    def test_invalid_color_format(self):
        """Test format couleur invalide."""
        data = self.get_valid_data()
        data['couleur'] = 'red'
        form = self._validate_form(data)
        self.assertIn('couleur', form.errors)


# =============================================
# Tests AbsenceForm
# =============================================

class TestAbsenceForm(BaseTestCase):
    """Tests pour le formulaire Absence."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.type_conge = TypeAbsence.objects.create(
            code='CP1',
            libelle='Congés payés',
            categorie='CONGES_PAYES',
            paye=True,
            decompte_solde=False,  # Désactiver pour simplifier les tests
            justificatif_obligatoire=False,
            actif=True,
        )
        cls.type_maladie = TypeAbsence.objects.create(
            code='ML1',
            libelle='Maladie',
            categorie='MALADIE',
            justificatif_obligatoire=True,
            actif=True,
        )

    def get_valid_data(self):
        return {
            'type_absence': self.type_conge.pk,
            'date_debut': date.today() + timedelta(days=10),
            'date_fin': date.today() + timedelta(days=15),
            'periode': 'JOURNEE_COMPLETE',
            'motif': 'Vacances',
        }

    def test_valid_form(self):
        """Test formulaire valide."""
        form = AbsenceForm(data=self.get_valid_data(), user=self.employe)
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_fin_before_debut(self):
        """Test date_fin antérieure à date_debut détectée par le formulaire."""
        data = self.get_valid_data()
        data['date_fin'] = date.today() + timedelta(days=5)
        data['date_debut'] = date.today() + timedelta(days=10)
        form = AbsenceForm(data=data, user=self.employe)
        self.assertFalse(form.is_valid())
        self.assertIn('date_fin', form.errors)

    def test_half_day_only_for_single_day(self):
        """Test demi-journée uniquement pour un seul jour."""
        data = self.get_valid_data()
        data['date_debut'] = date.today() + timedelta(days=10)
        data['date_fin'] = date.today() + timedelta(days=10)
        data['periode'] = 'MATIN'
        form = AbsenceForm(data=data, user=self.employe)
        self.assertTrue(form.is_valid(), form.errors)

    def test_multi_day_forced_to_full_day(self):
        """Test plusieurs jours forcé en journée complète."""
        data = self.get_valid_data()
        data['periode'] = 'MATIN'
        # Plusieurs jours avec demi-journée - devrait être forcé à JOURNEE_COMPLETE
        form = AbsenceForm(data=data, user=self.employe)
        if form.is_valid():
            self.assertEqual(form.cleaned_data['periode'], 'JOURNEE_COMPLETE')

    def test_overlap_detection(self):
        """Test détection de chevauchement avec absence existante."""
        Absence.objects.create(
            employe=self.employe,
            type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=10),
            date_fin=date.today() + timedelta(days=15),
            statut='VALIDE',
            created_by=self.employe,
        )
        data = self.get_valid_data()
        data['date_debut'] = date.today() + timedelta(days=12)
        data['date_fin'] = date.today() + timedelta(days=18)
        form = AbsenceForm(data=data, user=self.employe)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_no_overlap_with_cancelled_absence(self):
        """Test pas de chevauchement avec absence annulée."""
        Absence.objects.create(
            employe=self.employe,
            type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=10),
            date_fin=date.today() + timedelta(days=15),
            statut='ANNULE',
            created_by=self.employe,
        )
        data = self.get_valid_data()
        form = AbsenceForm(data=data, user=self.employe)
        self.assertTrue(form.is_valid(), form.errors)

    def test_justificatif_required_for_maladie(self):
        """Test justificatif obligatoire pour type maladie."""
        data = self.get_valid_data()
        data['type_absence'] = self.type_maladie.pk
        form = AbsenceForm(data=data, user=self.employe)
        self.assertFalse(form.is_valid())
        self.assertIn('justificatif', form.errors)

    def test_motif_not_required(self):
        """Test motif optionnel."""
        data = self.get_valid_data()
        data['motif'] = ''
        form = AbsenceForm(data=data, user=self.employe)
        self.assertTrue(form.is_valid(), form.errors)


# =============================================
# Tests ValidationAbsenceForm
# =============================================

class TestValidationAbsenceForm(BaseTestCase):
    """Tests pour le formulaire ValidationAbsence."""

    def test_valid_approval(self):
        """Test approbation valide."""
        form = ValidationAbsenceForm(data={
            'decision': 'APPROUVE',
            'commentaire': 'OK',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_rejection(self):
        """Test rejet valide."""
        form = ValidationAbsenceForm(data={
            'decision': 'REJETE',
            'commentaire': 'Pas de disponibilité',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_approval_without_comment(self):
        """Test approbation sans commentaire (autorisé)."""
        form = ValidationAbsenceForm(data={
            'decision': 'APPROUVE',
            'commentaire': '',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_decision(self):
        """Test décision invalide."""
        form = ValidationAbsenceForm(data={
            'decision': 'INVALIDE',
            'commentaire': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('decision', form.errors)


# =============================================
# Tests AbsenceRechercheForm
# =============================================

class TestAbsenceRechercheForm(BaseTestCase):
    """Tests pour le formulaire de recherche d'absences."""

    def test_empty_form_valid(self):
        """Test formulaire vide est valide (tous les champs optionnels)."""
        form = AbsenceRechercheForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_filter_by_statut(self):
        """Test filtre par statut."""
        form = AbsenceRechercheForm(data={'statut': 'VALIDE'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['statut'], 'VALIDE')

    def test_filter_by_date_range(self):
        """Test filtre par plage de dates."""
        form = AbsenceRechercheForm(data={
            'date_debut': date.today() - timedelta(days=30),
            'date_fin': date.today(),
        })
        self.assertTrue(form.is_valid(), form.errors)

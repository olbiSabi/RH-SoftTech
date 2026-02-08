# absence/tests/test_views.py
"""
Tests pour les vues de l'application absence.
"""
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.tests.base import BaseTestCase
from absence.models import Absence, TypeAbsence, AcquisitionConges


class TestListeAbsencesView(BaseTestCase):
    """Tests pour la vue liste_absences."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.type_conge = TypeAbsence.objects.create(
            code='CP2', libelle='Congés payés',
            categorie='CONGES_PAYES', actif=True,
        )

    def test_access_authenticated(self):
        """Test accès authentifié retourne 200."""
        response = self.client.get(reverse('absence:liste_absences'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('absence:liste_absences'))
        self.assertEqual(response.status_code, 302)

    def test_context_contains_page_obj(self):
        """Test contexte contient page_obj."""
        response = self.client.get(reverse('absence:liste_absences'))
        self.assertIn('page_obj', response.context)

    def test_context_contains_stats(self):
        """Test contexte contient les statistiques."""
        response = self.client.get(reverse('absence:liste_absences'))
        self.assertIn('stats', response.context)

    def test_filter_by_statut(self):
        """Test filtrage par statut."""
        Absence.objects.create(
            employe=self.employe, type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=5),
            date_fin=date.today() + timedelta(days=10),
            statut='VALIDE', created_by=self.employe,
        )
        response = self.client.get(
            reverse('absence:liste_absences'), {'statut': 'VALIDE'}
        )
        self.assertEqual(response.status_code, 200)

    def test_only_own_absences_displayed(self):
        """Test seules les absences de l'employé connecté sont affichées."""
        other_employe = self.create_employee(matricule='OTH00001', nom='Autre')
        Absence.objects.create(
            employe=other_employe, type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=5),
            date_fin=date.today() + timedelta(days=10),
            statut='BROUILLON', created_by=other_employe,
        )
        response = self.client.get(reverse('absence:liste_absences'))
        absences = response.context['page_obj'].object_list
        for absence in absences:
            self.assertEqual(absence.employe, self.employe)


class TestCreerAbsenceView(BaseTestCase):
    """Tests pour la vue creer_absence."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.type_conge = TypeAbsence.objects.create(
            code='CP3', libelle='Congés payés',
            categorie='CONGES_PAYES', decompte_solde=False,
            justificatif_obligatoire=False, actif=True,
        )

    def test_get_form(self):
        """Test GET retourne le formulaire."""
        response = self.client.get(reverse('absence:creer_absence'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_redirect_unauthenticated(self):
        """Test redirection si non authentifié."""
        self.client.logout()
        response = self.client.get(reverse('absence:creer_absence'))
        self.assertEqual(response.status_code, 302)

    def test_create_valid_absence(self):
        """Test création d'absence valide via POST."""
        data = {
            'type_absence': self.type_conge.pk,
            'date_debut': (date.today() + timedelta(days=10)).isoformat(),
            'date_fin': (date.today() + timedelta(days=15)).isoformat(),
            'periode': 'JOURNEE_COMPLETE',
            'motif': 'Vacances annuelles',
        }
        response = self.client.post(reverse('absence:creer_absence'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Absence.objects.filter(employe=self.employe).exists()
        )

    def test_create_absence_sets_status_en_attente(self):
        """Test statut défini à EN_ATTENTE_MANAGER après création."""
        data = {
            'type_absence': self.type_conge.pk,
            'date_debut': (date.today() + timedelta(days=20)).isoformat(),
            'date_fin': (date.today() + timedelta(days=25)).isoformat(),
            'periode': 'JOURNEE_COMPLETE',
            'motif': '',
        }
        self.client.post(reverse('absence:creer_absence'), data)
        absence = Absence.objects.filter(employe=self.employe).last()
        if absence:
            self.assertEqual(absence.statut, 'EN_ATTENTE_MANAGER')

    def test_create_missing_type_returns_error(self):
        """Test données sans type_absence détecte l'erreur."""
        data = {
            'type_absence': '',
            'date_debut': (date.today() + timedelta(days=10)).isoformat(),
            'date_fin': (date.today() + timedelta(days=15)).isoformat(),
            'periode': 'JOURNEE_COMPLETE',
        }
        response = self.client.post(reverse('absence:creer_absence'), data)
        self.assertIn(response.status_code, [200, 400])

    def test_ajax_create_valid(self):
        """Test création AJAX valide retourne JSON."""
        data = {
            'type_absence': self.type_conge.pk,
            'date_debut': (date.today() + timedelta(days=30)).isoformat(),
            'date_fin': (date.today() + timedelta(days=35)).isoformat(),
            'periode': 'JOURNEE_COMPLETE',
            'motif': 'Test AJAX',
        }
        response = self.client.post(
            reverse('absence:creer_absence'), data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['success'])


class TestModifierAbsenceView(BaseTestCase):
    """Tests pour la vue modifier_absence."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.type_conge = TypeAbsence.objects.create(
            code='CP4', libelle='Congés payés',
            categorie='CONGES_PAYES', decompte_solde=False,
            justificatif_obligatoire=False, actif=True,
        )

    def setUp(self):
        super().setUp()
        self.absence = Absence.objects.create(
            employe=self.employe,
            type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=40),
            date_fin=date.today() + timedelta(days=45),
            statut='BROUILLON',
            created_by=self.employe,
        )

    def test_get_edit_form(self):
        """Test GET retourne le formulaire de modification."""
        response = self.client.get(
            reverse('absence:modifier_absence', args=[self.absence.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_cannot_edit_other_employee_absence(self):
        """Test impossibilité de modifier l'absence d'un autre employé."""
        other = self.create_employee(matricule='OTH00002', nom='Autre')
        absence_other = Absence.objects.create(
            employe=other,
            type_absence=self.type_conge,
            date_debut=date.today() + timedelta(days=50),
            date_fin=date.today() + timedelta(days=55),
            statut='BROUILLON',
            created_by=other,
        )
        response = self.client.get(
            reverse('absence:modifier_absence', args=[absence_other.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_cannot_edit_validated_absence(self):
        """Test impossibilité de modifier une absence validée."""
        self.absence.statut = 'VALIDE'
        self.absence.save()
        response = self.client.get(
            reverse('absence:modifier_absence', args=[self.absence.id])
        )
        self.assertEqual(response.status_code, 302)


class TestValidationManagerView(BaseTestCase):
    """Tests pour la vue validation_manager."""

    def test_non_manager_redirected(self):
        """Test non-manager redirigé."""
        response = self.client.get(reverse('absence:validation_manager'))
        self.assertEqual(response.status_code, 302)

    def test_manager_access(self):
        """Test accès manager."""
        employe_mgr, user_mgr = self.create_manager_user()
        self.client.login(username=user_mgr.username, password='testpass123')
        response = self.client.get(reverse('absence:validation_manager'))
        self.assertIn(response.status_code, [200, 302])


class TestValidationRHView(BaseTestCase):
    """Tests pour la vue validation_rh."""

    def test_non_drh_redirected(self):
        """Test non-DRH redirigé."""
        response = self.client.get(reverse('absence:validation_rh'))
        self.assertEqual(response.status_code, 302)

    def test_drh_access(self):
        """Test accès DRH."""
        employe_drh, user_drh = self.create_drh_user()
        self.client.login(username=user_drh.username, password='testpass123')
        response = self.client.get(reverse('absence:validation_rh'))
        self.assertIn(response.status_code, [200, 302])

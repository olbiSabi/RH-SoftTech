# absence/tests/test_workflows.py
"""
Tests d'intégration E2E des workflows critiques du module absence.

Couvre le cycle complet :
  - Employé dépose → Manager valide → RH valide (happy path)
  - Rejet par le manager
  - Annulation par l'employé
  - Tentative de validation par un non-habilité
  - Création avec données invalides
"""
import json
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from absence.models import Absence, TypeAbsence
from core.tests.base import BaseTestCase
from departement.models import ZYMA
from employee.models import ZYAF, ZY00, ZYRE


class TestWorkflowValidationAbsence(BaseTestCase):
    """
    Workflow E2E complet : dépôt d'absence → validation manager → validation RH.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # crée cls.departement, cls.poste, cls.employe, cls.user, cls.role_*

        # Rattacher l'employé de base au département TST (requis pour la validation manager)
        ZYAF.objects.create(
            employe=cls.employe,
            poste=cls.poste,
            date_debut=date.today() - timedelta(days=365),
        )

        # ── Manager ─────────────────────────────────────────────────────────────
        cls.employe_manager = ZY00.objects.create(
            matricule='MGR00001', nom='Kamga', prenoms='Paul',
            date_naissance=date(1985, 6, 15), sexe='M',
            type_id='CNI', numero_id='IDMGR0001',
            date_validite_id=date(2020, 1, 1), date_expiration_id=date(2030, 1, 1),
            type_dossier='SAL', etat='actif',
        )
        cls.user_manager = User.objects.create_user(username='MGR00001', password='testpass123')
        cls.employe_manager.user = cls.user_manager
        cls.employe_manager.save()
        ZYRE.objects.create(
            employe=cls.employe_manager, role=cls.role_manager,
            date_debut=date.today(), actif=True,
        )
        ZYMA.objects.create(
            employe=cls.employe_manager, departement=cls.departement,
            date_debut=date.today(), date_fin=None, actif=True,
        )

        # ── DRH (valideur RH) ───────────────────────────────────────────────────
        # can_validate_absence_as_rh() exige le rôle CODE='RH_VALIDATION'
        from employee.models import ZYRO
        cls.role_rh_validation = ZYRO.objects.create(
            CODE='RH_VALIDATION',
            LIBELLE='Valideur RH absences',
            actif=True,
        )

        cls.employe_drh = ZY00.objects.create(
            matricule='DRH00001', nom='Nkoa', prenoms='Marie',
            date_naissance=date(1980, 3, 10), sexe='F',
            type_id='CNI', numero_id='IDDRH0001',
            date_validite_id=date(2020, 1, 1), date_expiration_id=date(2030, 1, 1),
            type_dossier='SAL', etat='actif',
        )
        cls.user_drh = User.objects.create_user(username='DRH00001', password='testpass123')
        cls.employe_drh.user = cls.user_drh
        cls.employe_drh.save()
        ZYRE.objects.create(
            employe=cls.employe_drh, role=cls.role_drh,
            date_debut=date.today(), actif=True,
        )
        ZYRE.objects.create(
            employe=cls.employe_drh, role=cls.role_rh_validation,
            date_debut=date.today(), actif=True,
        )

        # ── Type d'absence sans décompte solde (évite AcquisitionConges) ────────
        cls.type_autorisation = TypeAbsence.objects.create(
            code='AUT',
            libelle='Autorisation spéciale',
            categorie='AUTORISATION',
            paye=True,
            decompte_solde=False,
            justificatif_obligatoire=False,
            actif=True,
        )

    def _post_creer_absence(self, date_debut=None, date_fin=None, type_absence=None):
        """Helper : POST de création d'absence avec l'utilisateur de base."""
        if date_debut is None:
            date_debut = date.today() + timedelta(days=10)
        if date_fin is None:
            date_fin = date.today() + timedelta(days=12)
        if type_absence is None:
            type_absence = self.type_autorisation

        return self.client.post(
            reverse('absence:creer_absence'),
            data={
                'type_absence': type_absence.pk,
                'date_debut': date_debut.isoformat(),
                'date_fin': date_fin.isoformat(),
                'periode': 'JOURNEE_COMPLETE',
                'motif': 'Motif de test',
            },
        )

    # =========================================================================
    # Création d'absence
    # =========================================================================

    def test_creation_absence_cree_statut_en_attente_manager(self):
        """La création d'une absence la place directement en EN_ATTENTE_MANAGER."""
        response = self._post_creer_absence()

        self.assertIn(response.status_code, [200, 302])
        absence = Absence.objects.filter(employe=self.employe).last()
        self.assertIsNotNone(absence, "L'absence aurait dû être créée")
        self.assertEqual(absence.statut, 'EN_ATTENTE_MANAGER')

    def test_creation_absence_redirige_vers_liste(self):
        """Après création, l'utilisateur est redirigé vers la liste."""
        response = self._post_creer_absence()
        self.assertRedirects(response, reverse('absence:liste_absences'))

    def test_creation_absence_dates_invalides_renvoie_erreur(self):
        """date_fin < date_debut → formulaire invalide, pas d'absence créée."""
        nb_avant = Absence.objects.filter(employe=self.employe).count()
        response = self._post_creer_absence(
            date_debut=date.today() + timedelta(days=20),
            date_fin=date.today() + timedelta(days=10),  # antérieure à date_debut
        )
        nb_apres = Absence.objects.filter(employe=self.employe).count()
        # La vue doit renvoyer le formulaire (200) sans créer d'absence
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nb_avant, nb_apres)

    def test_creation_necessite_authentification(self):
        """Accès sans authentification → redirection vers login."""
        self.client.logout()
        response = self._post_creer_absence()
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    # =========================================================================
    # Workflow complet : EN_ATTENTE_MANAGER → EN_ATTENTE_RH → VALIDE
    # =========================================================================

    def _creer_absence_en_attente(self):
        """Crée une absence directement en base en EN_ATTENTE_MANAGER."""
        return Absence.objects.create(
            employe=self.employe,
            type_absence=self.type_autorisation,
            date_debut=date.today() + timedelta(days=10),
            date_fin=date.today() + timedelta(days=12),
            periode='JOURNEE_COMPLETE',
            motif='Test workflow',
            statut='EN_ATTENTE_MANAGER',
            created_by=self.employe,
        )

    def test_workflow_complet_manager_puis_rh(self):
        """
        Workflow happy path : manager approuve → EN_ATTENTE_RH,
        puis RH approuve → VALIDE.
        """
        absence = self._creer_absence_en_attente()
        url = reverse('absence:api_valider_absence', args=[absence.id])

        # Étape 1 : validation manager (décision = 'APPROUVE' selon le modèle)
        client_manager = Client()
        client_manager.login(username='MGR00001', password='testpass123')
        response = client_manager.post(url, data={
            'decision': 'APPROUVE',
            'commentaire': 'RAS, accordé.',
        })

        data = json.loads(response.content)
        self.assertTrue(data.get('success'), f"Validation manager échouée : {data}")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'EN_ATTENTE_RH')
        self.assertEqual(absence.manager_validateur, self.employe_manager)

        # Étape 2 : validation RH
        client_drh = Client()
        client_drh.login(username='DRH00001', password='testpass123')
        response = client_drh.post(url, data={
            'decision': 'APPROUVE',
            'commentaire': 'Validé par les RH.',
        })

        data = json.loads(response.content)
        self.assertTrue(data.get('success'), f"Validation RH échouée : {data}")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'VALIDE')
        self.assertEqual(absence.rh_validateur, self.employe_drh)
        self.assertIsNotNone(absence.date_validation_manager)
        self.assertIsNotNone(absence.date_validation_rh)

    def test_workflow_rejet_par_manager(self):
        """Le manager peut rejeter une absence → statut REJETE."""
        absence = self._creer_absence_en_attente()
        url = reverse('absence:api_valider_absence', args=[absence.id])

        client_manager = Client()
        client_manager.login(username='MGR00001', password='testpass123')
        response = client_manager.post(url, data={
            'decision': 'REJETE',
            'commentaire': 'Période chargée, impossible.',
        })

        data = json.loads(response.content)
        self.assertTrue(data.get('success'), f"Rejet manager échoué : {data}")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'REJETE')
        self.assertEqual(absence.commentaire_manager, 'Période chargée, impossible.')

    def test_workflow_rejet_par_rh(self):
        """La RH peut rejeter une absence en EN_ATTENTE_RH → statut REJETE."""
        absence = self._creer_absence_en_attente()
        absence.statut = 'EN_ATTENTE_RH'
        absence.manager_validateur = self.employe_manager
        absence.save()

        url = reverse('absence:api_valider_absence', args=[absence.id])

        client_drh = Client()
        client_drh.login(username='DRH00001', password='testpass123')
        response = client_drh.post(url, data={
            'decision': 'REJETE',
            'commentaire': 'Pièces justificatives manquantes.',
        })

        data = json.loads(response.content)
        self.assertTrue(data.get('success'), f"Rejet RH échoué : {data}")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'REJETE')

    # =========================================================================
    # Annulation par l'employé
    # =========================================================================

    def test_employe_peut_annuler_absence_en_attente(self):
        """L'employé peut annuler une absence encore en attente de validation."""
        absence = self._creer_absence_en_attente()
        url = reverse('absence:api_absence_annuler', args=[absence.id])

        response = self.client.post(url)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'), f"Annulation échouée : {data}")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'ANNULE')

    def test_employe_ne_peut_pas_annuler_absence_validee_sans_droit(self):
        """Une absence REJETE ne peut pas être annulée (propriété peut_annuler=False)."""
        absence = self._creer_absence_en_attente()
        absence.statut = 'REJETE'
        absence.save()

        url = reverse('absence:api_absence_annuler', args=[absence.id])
        response = self.client.post(url)
        data = json.loads(response.content)
        self.assertFalse(data.get('success'))

    # =========================================================================
    # Contrôles d'accès
    # =========================================================================

    def test_simple_employe_ne_peut_pas_valider_absence(self):
        """
        Un employé ordinaire (sans rôle manager) tente de valider une absence
        → l'API renvoie une erreur (ValidationError dans le modèle).
        """
        absence = self._creer_absence_en_attente()
        url = reverse('absence:api_valider_absence', args=[absence.id])

        # self.client est connecté en tant que BASE0001 (pas de rôle manager)
        response = self.client.post(url, data={
            'decision': 'VALIDE',
            'commentaire': '',
        })

        data = json.loads(response.content)
        self.assertFalse(data.get('success'), "Un employé sans rôle manager ne doit pas pouvoir valider")

        absence.refresh_from_db()
        self.assertEqual(absence.statut, 'EN_ATTENTE_MANAGER')

    def test_validation_absence_pas_en_attente_renvoie_erreur(self):
        """
        Tenter de valider une absence qui n'est pas en attente
        → l'API renvoie une erreur métier.
        """
        absence = self._creer_absence_en_attente()
        absence.statut = 'VALIDE'
        absence.save()

        url = reverse('absence:api_valider_absence', args=[absence.id])
        client_manager = Client()
        client_manager.login(username='MGR00001', password='testpass123')
        response = client_manager.post(url, data={
            'decision': 'VALIDE',
            'commentaire': '',
        })

        data = json.loads(response.content)
        self.assertFalse(data.get('success'))

    def test_detail_absence_accessible_par_son_employe(self):
        """L'employé peut accéder au détail de sa propre absence via l'API."""
        absence = self._creer_absence_en_attente()
        url = reverse('absence:api_absence_detail', args=[absence.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
        self.assertEqual(data['data']['employe_matricule'], self.employe.matricule)

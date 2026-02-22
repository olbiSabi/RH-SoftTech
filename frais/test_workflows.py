# frais/test_workflows.py
"""
Tests d'intégration E2E des workflows critiques du module Notes de Frais.

Couvre le cycle complet :
  - Employé crée une note (BROUILLON)
  - Employé ajoute une ligne de dépense
  - Employé soumet la note (SOUMIS)
  - DRH valide la note (VALIDE) — happy path
  - DRH rejette la note (REJETE)
  - Tentative de soumission sans ligne → bloquée
  - Tentative de validation par un non-habilité → bloquée
"""
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from core.tests.base import BaseTestCase
from employee.models import ZY00, ZYRE
from frais.models import NFCA, NFLF, NFNF


class TestWorkflowNoteFrais(BaseTestCase):
    """
    Workflow E2E complet : création → ajout ligne → soumission → validation / rejet.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # crée cls.employe, cls.user, cls.role_drh, …

        # ── Catégorie de frais sans justificatif obligatoire ─────────────────
        cls.categorie = NFCA.objects.create(
            CODE='TRANS',
            LIBELLE='Transport',
            DESCRIPTION='Frais de transport divers',
            JUSTIFICATIF_OBLIGATOIRE=False,
            STATUT=True,
        )

        # ── DRH (seul rôle habilité à valider les frais) ─────────────────────
        cls.employe_drh = ZY00.objects.create(
            matricule='DRHF0001', nom='Essomba', prenoms='Claude',
            date_naissance=date(1975, 4, 20), sexe='M',
            type_id='CNI', numero_id='IDDRHF001',
            date_validite_id=date(2020, 1, 1), date_expiration_id=date(2030, 1, 1),
            type_dossier='SAL', etat='actif',
        )
        cls.user_drh = User.objects.create_user(username='DRHF0001', password='testpass123')
        cls.employe_drh.user = cls.user_drh
        cls.employe_drh.save()
        ZYRE.objects.create(
            employe=cls.employe_drh, role=cls.role_drh,
            date_debut=date.today(), actif=True,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _client_drh(self):
        c = Client()
        c.login(username='DRHF0001', password='testpass123')
        return c

    def _creer_note_via_http(self):
        """POST de création d'une note de frais ; retourne (response, note|None)."""
        periode_debut = date.today() - timedelta(days=30)
        periode_fin = date.today()
        response = self.client.post(
            reverse('frais:creer_note'),
            data={
                'PERIODE_DEBUT': periode_debut.isoformat(),
                'PERIODE_FIN': periode_fin.isoformat(),
                'OBJET': 'Mission Yaoundé',
            },
        )
        note = NFNF.objects.filter(EMPLOYE=self.employe).order_by('-CREATED_AT').first()
        return response, note

    def _ajouter_ligne_via_http(self, note):
        """POST d'ajout d'une ligne de frais ; retourne la réponse JSON."""
        response = self.client.post(
            reverse('frais:ajouter_ligne', kwargs={'note_uuid': note.uuid}),
            data={
                'CATEGORIE': self.categorie.pk,
                'DATE_DEPENSE': (note.PERIODE_DEBUT + timedelta(days=1)).isoformat(),
                'DESCRIPTION': 'Taxi aéroport',
                'MONTANT': '15000',
                'DEVISE': 'XOF',
            },
        )
        return response

    # =========================================================================
    # Création de la note
    # =========================================================================

    def test_creation_note_cree_en_brouillon(self):
        """Une nouvelle note est créée avec le statut BROUILLON."""
        response, note = self._creer_note_via_http()

        self.assertIsNotNone(note, "La note aurait dû être créée")
        self.assertEqual(note.STATUT, 'BROUILLON')
        self.assertEqual(note.EMPLOYE, self.employe)

    def test_creation_note_redirige_vers_detail(self):
        """Après création, l'utilisateur est redirigé vers la page de détail."""
        response, note = self._creer_note_via_http()
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(note)
        self.assertIn(str(note.uuid), response['Location'])

    def test_creation_note_genere_reference_automatique(self):
        """La référence (ex. NF2026XXXXX) est générée automatiquement."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)
        self.assertTrue(note.REFERENCE.startswith('NF'), f"Référence inattendue : {note.REFERENCE}")

    def test_creation_note_necessite_authentification(self):
        """Un utilisateur non connecté est redirigé vers le login."""
        self.client.logout()
        response = self.client.post(
            reverse('frais:creer_note'),
            data={
                'PERIODE_DEBUT': date.today().isoformat(),
                'PERIODE_FIN': date.today().isoformat(),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    # =========================================================================
    # Ajout de ligne
    # =========================================================================

    def test_ajout_ligne_retourne_succes_json(self):
        """L'ajout d'une ligne renvoie {success: true} et met à jour le montant."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)

        response = self._ajouter_ligne_via_http(note)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get('success'), f"Ajout ligne échoué : {data}")
        self.assertIn('montant_total', data)
        self.assertEqual(Decimal(data['montant_total']), Decimal('15000'))

    def test_ajout_ligne_cree_en_base(self):
        """La ligne créée est bien persistée en base et liée à la note."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)

        self._ajouter_ligne_via_http(note)

        self.assertEqual(note.lignes.count(), 1)
        ligne = note.lignes.first()
        self.assertEqual(ligne.MONTANT, Decimal('15000'))
        self.assertEqual(ligne.CATEGORIE, self.categorie)

    def test_ajout_ligne_autre_employe_refuse(self):
        """Un autre employé ne peut pas ajouter de ligne sur la note d'un collègue."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)

        # Le DRH tente d'ajouter une ligne sur la note de BASE0001
        client_drh = self._client_drh()
        response = client_drh.post(
            reverse('frais:ajouter_ligne', kwargs={'note_uuid': note.uuid}),
            data={
                'CATEGORIE': self.categorie.pk,
                'DATE_DEPENSE': date.today().isoformat(),
                'DESCRIPTION': 'Tentative intrusion',
                'MONTANT': '5000',
                'DEVISE': 'XOF',
            },
        )
        data = json.loads(response.content)
        self.assertFalse(data.get('success'))
        self.assertEqual(response.status_code, 403)

    # =========================================================================
    # Soumission
    # =========================================================================

    def test_soumission_sans_ligne_est_bloquee(self):
        """Soumettre une note sans ligne → message d'erreur, statut inchangé."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)

        response = self.client.post(
            reverse('frais:soumettre_note', kwargs={'uuid': note.uuid}),
        )
        # La vue redirige toujours vers le détail ; c'est l'absence de changement de statut qu'on vérifie
        self.assertEqual(response.status_code, 302)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'BROUILLON', "La note sans ligne ne doit pas passer en SOUMIS")

    def test_soumission_avec_ligne_passe_en_soumis(self):
        """Soumettre une note avec une ligne valide → statut SOUMIS."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)

        self._ajouter_ligne_via_http(note)

        response = self.client.post(
            reverse('frais:soumettre_note', kwargs={'uuid': note.uuid}),
        )
        self.assertEqual(response.status_code, 302)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'SOUMIS')
        self.assertIsNotNone(note.DATE_SOUMISSION)

    def test_soumission_par_autre_employe_refusee(self):
        """Un autre employé ne peut pas soumettre la note d'un collègue (403)."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)
        self._ajouter_ligne_via_http(note)

        client_drh = self._client_drh()
        response = client_drh.post(
            reverse('frais:soumettre_note', kwargs={'uuid': note.uuid}),
        )
        self.assertEqual(response.status_code, 403)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'BROUILLON')

    # =========================================================================
    # Workflow complet : création → ajout ligne → soumission → validation
    # =========================================================================

    def _note_prete_a_valider(self):
        """Crée en base une note déjà en statut SOUMIS avec une ligne."""
        note = NFNF.objects.create(
            EMPLOYE=self.employe,
            PERIODE_DEBUT=date.today() - timedelta(days=30),
            PERIODE_FIN=date.today(),
            OBJET='Note de test prête',
            STATUT='SOUMIS',
            CREATED_BY=self.employe,
        )
        NFLF.objects.create(
            NOTE_FRAIS=note,
            CATEGORIE=self.categorie,
            DATE_DEPENSE=date.today() - timedelta(days=5),
            DESCRIPTION='Carburant',
            MONTANT=Decimal('8000'),
            DEVISE='XOF',
            STATUT_LIGNE='EN_ATTENTE',
        )
        note.calculer_totaux()
        return note

    def test_workflow_complet_creation_soumission_validation(self):
        """
        Workflow happy path complet via HTTP :
          BROUILLON → (ajout ligne) → SOUMIS → VALIDE
        """
        # 1. Créer la note
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)
        self.assertEqual(note.STATUT, 'BROUILLON')

        # 2. Ajouter une ligne
        resp_ligne = self._ajouter_ligne_via_http(note)
        self.assertTrue(json.loads(resp_ligne.content).get('success'))

        # 3. Soumettre
        self.client.post(reverse('frais:soumettre_note', kwargs={'uuid': note.uuid}))
        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'SOUMIS')

        # 4. DRH valide
        client_drh = self._client_drh()
        response = client_drh.post(
            reverse('frais:valider_note', kwargs={'uuid': note.uuid}),
            data={'commentaire': 'Conforme, validé.'},
        )
        self.assertEqual(response.status_code, 302)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'VALIDE')
        self.assertEqual(note.VALIDEUR, self.employe_drh)
        self.assertIsNotNone(note.DATE_VALIDATION)

    def test_workflow_rejet_par_drh(self):
        """Le DRH peut rejeter une note soumise → statut REJETE."""
        note = self._note_prete_a_valider()

        client_drh = self._client_drh()
        response = client_drh.post(
            reverse('frais:rejeter_note', kwargs={'uuid': note.uuid}),
            data={'commentaire': 'Justificatifs insuffisants.'},
        )
        self.assertEqual(response.status_code, 302)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'REJETE')
        self.assertEqual(note.COMMENTAIRE_VALIDATION, 'Justificatifs insuffisants.')

    # =========================================================================
    # Contrôles d'accès à la validation
    # =========================================================================

    def test_employe_ordinaire_ne_peut_pas_valider(self):
        """Un employé sans rôle DRH/DAF/… ne peut pas valider (403)."""
        note = self._note_prete_a_valider()

        # self.client est BASE0001, sans rôle valideur frais
        response = self.client.post(
            reverse('frais:valider_note', kwargs={'uuid': note.uuid}),
            data={'commentaire': ''},
        )
        self.assertEqual(response.status_code, 403)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'SOUMIS', "Le statut ne doit pas changer")

    def test_employe_ordinaire_ne_peut_pas_rejeter(self):
        """Un employé sans rôle DRH/DAF/… ne peut pas rejeter (403)."""
        note = self._note_prete_a_valider()

        response = self.client.post(
            reverse('frais:rejeter_note', kwargs={'uuid': note.uuid}),
            data={'commentaire': 'Tentative non autorisée'},
        )
        self.assertEqual(response.status_code, 403)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'SOUMIS')

    def test_rejet_sans_commentaire_est_invalide(self):
        """
        Le rejet requiert un commentaire (motif obligatoire).
        Sans commentaire, le statut reste inchangé.
        """
        note = self._note_prete_a_valider()

        client_drh = self._client_drh()
        response = client_drh.post(
            reverse('frais:rejeter_note', kwargs={'uuid': note.uuid}),
            data={'commentaire': ''},  # champ vide
        )
        # La vue redirige même si le form est invalide (messages.error)
        self.assertEqual(response.status_code, 302)

        note.refresh_from_db()
        self.assertEqual(note.STATUT, 'SOUMIS', "Le rejet sans motif ne doit pas changer le statut")

    # =========================================================================
    # Suppression / intégrité
    # =========================================================================

    def test_suppression_note_brouillon_possible(self):
        """Une note en BROUILLON peut être supprimée par son propriétaire."""
        _, note = self._creer_note_via_http()
        self.assertIsNotNone(note)
        note_uuid = note.uuid

        response = self.client.post(
            reverse('frais:supprimer_note', kwargs={'uuid': note_uuid}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(NFNF.objects.filter(uuid=note_uuid).exists())

    def test_suppression_note_soumise_bloquee(self):
        """Une note déjà SOUMIS ne peut pas être supprimée."""
        note = self._note_prete_a_valider()
        note_uuid = note.uuid

        response = self.client.post(
            reverse('frais:supprimer_note', kwargs={'uuid': note_uuid}),
        )
        # La vue redirige mais la note reste en base
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NFNF.objects.filter(uuid=note_uuid).exists())

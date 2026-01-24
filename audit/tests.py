# audit/tests.py
"""
Tests pour le module Conformité & Audit.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from audit.models import AURC, AUAL, AURA
from audit.forms import (
    AURCForm, ResoudreAlerteForm, AssignerAlerteForm,
    FiltresLogsForm, FiltresAlertesForm, GenererRapportForm
)
from audit.services import ConformiteService, AlerteService, LogService, RapportAuditService

User = get_user_model()


# ============================================================================
# Tests des Modèles
# ============================================================================

class AURCModelTest(TestCase):
    """Tests pour le modèle AURC (Règles de conformité)."""

    def test_creation_regle(self):
        """Test de création d'une règle de conformité."""
        regle = AURC.objects.create(
            CODE='REGLE_TEST_001',
            LIBELLE='Règle de test',
            DESCRIPTION='Description de la règle de test',
            TYPE_REGLE='CONTRAT',
            SEVERITE='WARNING',
            FREQUENCE_VERIFICATION='QUOTIDIEN',
            JOURS_AVANT_EXPIRATION=30,
            NOTIFIER_EMPLOYE=True,
            NOTIFIER_MANAGER=True,
            NOTIFIER_RH=True,
            STATUT=True
        )
        self.assertIsNotNone(regle.uuid)
        self.assertEqual(regle.CODE, 'REGLE_TEST_001')
        self.assertEqual(regle.TYPE_REGLE, 'CONTRAT')
        self.assertEqual(regle.SEVERITE, 'WARNING')

    def test_str_representation(self):
        """Test de la représentation string."""
        regle = AURC.objects.create(
            CODE='REGLE_STR_TEST',
            LIBELLE='Test String',
            TYPE_REGLE='DOCUMENT'
        )
        self.assertEqual(str(regle), 'REGLE_STR_TEST - Test String')

    def test_default_values(self):
        """Test des valeurs par défaut."""
        regle = AURC.objects.create(
            CODE='REGLE_DEFAULT',
            LIBELLE='Test Défaut',
            TYPE_REGLE='CONTRAT'
        )
        self.assertEqual(regle.SEVERITE, 'WARNING')
        self.assertEqual(regle.FREQUENCE_VERIFICATION, 'QUOTIDIEN')
        self.assertEqual(regle.JOURS_AVANT_EXPIRATION, 30)
        self.assertTrue(regle.STATUT)
        self.assertTrue(regle.NOTIFIER_MANAGER)
        self.assertTrue(regle.NOTIFIER_RH)
        self.assertFalse(regle.NOTIFIER_EMPLOYE)


class AUALModelTest(TestCase):
    """Tests pour le modèle AUAL (Alertes)."""

    def setUp(self):
        """Configuration des données de test."""
        self.regle = AURC.objects.create(
            CODE='REGLE_ALERTE',
            LIBELLE='Règle pour alertes',
            TYPE_REGLE='CONTRAT'
        )

    def test_creation_alerte(self):
        """Test de création d'une alerte."""
        alerte = AUAL.objects.create(
            REGLE=self.regle,
            TYPE_ALERTE='CONTRAT',
            TITRE='Contrat expirant',
            DESCRIPTION='Le contrat expire dans 30 jours',
            PRIORITE='HAUTE',
            STATUT='NOUVEAU'
        )
        self.assertIsNotNone(alerte.uuid)
        self.assertIsNotNone(alerte.REFERENCE)
        self.assertTrue(alerte.REFERENCE.startswith('AL'))

    def test_auto_reference_generation(self):
        """Test de la génération automatique de référence."""
        alerte1 = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte 1',
            DESCRIPTION='Description 1'
        )
        alerte2 = AUAL.objects.create(
            TYPE_ALERTE='DOCUMENT',
            TITRE='Alerte 2',
            DESCRIPTION='Description 2'
        )
        # Les références doivent être uniques et séquentielles
        self.assertNotEqual(alerte1.REFERENCE, alerte2.REFERENCE)
        annee = timezone.now().year
        self.assertTrue(alerte1.REFERENCE.startswith(f'AL{annee}'))
        self.assertTrue(alerte2.REFERENCE.startswith(f'AL{annee}'))

    def test_est_en_retard(self):
        """Test de la propriété est_en_retard."""
        # Alerte avec échéance passée
        alerte_retard = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte en retard',
            DESCRIPTION='Description',
            DATE_ECHEANCE=date.today() - timedelta(days=5),
            STATUT='NOUVEAU'
        )
        self.assertTrue(alerte_retard.est_en_retard)

        # Alerte avec échéance future
        alerte_ok = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte OK',
            DESCRIPTION='Description',
            DATE_ECHEANCE=date.today() + timedelta(days=5),
            STATUT='NOUVEAU'
        )
        self.assertFalse(alerte_ok.est_en_retard)

        # Alerte résolue (même si échéance passée)
        alerte_resolue = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte résolue',
            DESCRIPTION='Description',
            DATE_ECHEANCE=date.today() - timedelta(days=5),
            STATUT='RESOLU'
        )
        self.assertFalse(alerte_resolue.est_en_retard)

    def test_jours_restants(self):
        """Test de la propriété jours_restants."""
        alerte = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Test jours restants',
            DESCRIPTION='Description',
            DATE_ECHEANCE=date.today() + timedelta(days=10)
        )
        self.assertEqual(alerte.jours_restants, 10)

        # Sans échéance
        alerte_sans_echeance = AUAL.objects.create(
            TYPE_ALERTE='DOCUMENT',
            TITRE='Sans échéance',
            DESCRIPTION='Description'
        )
        self.assertIsNone(alerte_sans_echeance.jours_restants)


class AURAModelTest(TestCase):
    """Tests pour le modèle AURA (Rapports)."""

    def test_creation_rapport(self):
        """Test de création d'un rapport."""
        rapport = AURA.objects.create(
            TITRE='Rapport de test',
            TYPE_RAPPORT='CONFORMITE',
            FORMAT='PDF',
            DATE_DEBUT=date.today() - timedelta(days=30),
            DATE_FIN=date.today()
        )
        self.assertIsNotNone(rapport.uuid)
        self.assertIsNotNone(rapport.REFERENCE)
        self.assertTrue(rapport.REFERENCE.startswith('RA'))

    def test_auto_reference_generation(self):
        """Test de la génération automatique de référence."""
        rapport1 = AURA.objects.create(
            TITRE='Rapport 1',
            TYPE_RAPPORT='CONFORMITE',
            DATE_DEBUT=date.today(),
            DATE_FIN=date.today()
        )
        rapport2 = AURA.objects.create(
            TITRE='Rapport 2',
            TYPE_RAPPORT='LOGS',
            DATE_DEBUT=date.today(),
            DATE_FIN=date.today()
        )
        self.assertNotEqual(rapport1.REFERENCE, rapport2.REFERENCE)
        annee = timezone.now().year
        self.assertTrue(rapport1.REFERENCE.startswith(f'RA{annee}'))

    def test_default_values(self):
        """Test des valeurs par défaut."""
        rapport = AURA.objects.create(
            TITRE='Rapport défaut',
            TYPE_RAPPORT='ALERTES',
            DATE_DEBUT=date.today(),
            DATE_FIN=date.today()
        )
        self.assertEqual(rapport.FORMAT, 'PDF')
        self.assertEqual(rapport.STATUT, 'EN_COURS')
        self.assertEqual(rapport.NB_ENREGISTREMENTS, 0)


# ============================================================================
# Tests des Formulaires
# ============================================================================

class AURCFormTest(TestCase):
    """Tests pour le formulaire AURC."""

    def test_form_valid(self):
        """Test d'un formulaire valide."""
        data = {
            'CODE': 'REGLE_FORM_TEST',
            'LIBELLE': 'Règle test formulaire',
            'DESCRIPTION': 'Description de test',
            'TYPE_REGLE': 'CONTRAT',
            'SEVERITE': 'WARNING',
            'FREQUENCE_VERIFICATION': 'QUOTIDIEN',
            'JOURS_AVANT_EXPIRATION': 30,
            'NOTIFIER_EMPLOYE': True,
            'NOTIFIER_MANAGER': True,
            'NOTIFIER_RH': True,
            'STATUT': True
        }
        form = AURCForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_required_fields(self):
        """Test des champs obligatoires."""
        form = AURCForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('CODE', form.errors)
        self.assertIn('LIBELLE', form.errors)
        self.assertIn('TYPE_REGLE', form.errors)


class ResoudreAlerteFormTest(TestCase):
    """Tests pour le formulaire de résolution d'alerte."""

    def test_form_valid(self):
        """Test d'un formulaire valide."""
        data = {
            'COMMENTAIRE_RESOLUTION': 'Problème résolu manuellement'
        }
        form = ResoudreAlerteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_optional_comment(self):
        """Test que le commentaire est optionnel."""
        form = ResoudreAlerteForm(data={})
        self.assertTrue(form.is_valid())


class GenererRapportFormTest(TestCase):
    """Tests pour le formulaire de génération de rapport."""

    def test_form_valid(self):
        """Test d'un formulaire valide."""
        data = {
            'type_rapport': 'CONFORMITE',
            'format_export': 'PDF',
            'date_debut': date.today() - timedelta(days=30),
            'date_fin': date.today()
        }
        form = GenererRapportForm(data=data)
        self.assertTrue(form.is_valid())

    def test_date_debut_apres_date_fin(self):
        """Test que date_debut doit être avant date_fin."""
        data = {
            'type_rapport': 'CONFORMITE',
            'format_export': 'PDF',
            'date_debut': date.today(),
            'date_fin': date.today() - timedelta(days=30)
        }
        form = GenererRapportForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class FiltresAlertesFormTest(TestCase):
    """Tests pour le formulaire de filtres des alertes."""

    def test_form_all_empty(self):
        """Test formulaire avec tous les champs vides."""
        form = FiltresAlertesForm(data={})
        self.assertTrue(form.is_valid())

    def test_form_with_filters(self):
        """Test formulaire avec filtres."""
        data = {
            'statut': 'NOUVEAU',
            'priorite': 'HAUTE',
            'type_alerte': 'CONTRAT'
        }
        form = FiltresAlertesForm(data=data)
        self.assertTrue(form.is_valid())


# ============================================================================
# Tests des Services
# ============================================================================

class ConformiteServiceTest(TestCase):
    """Tests pour ConformiteService."""

    def test_verifier_conformite_contrats_empty(self):
        """Test vérification sans contrats expirés."""
        # Créer la règle nécessaire
        AURC.objects.create(
            CODE='CONTRAT_EXPIRATION',
            LIBELLE='Contrat expirant',
            TYPE_REGLE='CONTRAT',
            JOURS_AVANT_EXPIRATION=30,
            STATUT=True
        )
        # Sans données, devrait retourner une liste vide
        alertes = ConformiteService.verifier_conformite_contrats()
        self.assertIsInstance(alertes, list)

    def test_verifier_conformite_documents_empty(self):
        """Test vérification sans documents expirés."""
        AURC.objects.create(
            CODE='DOCUMENT_EXPIRATION',
            LIBELLE='Document expirant',
            TYPE_REGLE='DOCUMENT',
            JOURS_AVANT_EXPIRATION=30,
            STATUT=True
        )
        alertes = ConformiteService.verifier_conformite_documents()
        self.assertIsInstance(alertes, list)


class AlerteServiceTest(TestCase):
    """Tests pour AlerteService."""

    def test_get_stats_dashboard(self):
        """Test récupération des statistiques dashboard."""
        # Créer quelques alertes
        AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte 1',
            DESCRIPTION='Desc 1',
            STATUT='NOUVEAU',
            PRIORITE='HAUTE'
        )
        AUAL.objects.create(
            TYPE_ALERTE='DOCUMENT',
            TITRE='Alerte 2',
            DESCRIPTION='Desc 2',
            STATUT='EN_COURS',
            PRIORITE='CRITIQUE'
        )

        stats = AlerteService.get_stats_dashboard()
        self.assertIn('total_alertes', stats)
        self.assertIn('alertes_nouvelles', stats)
        self.assertIn('alertes_critiques', stats)
        self.assertIn('par_type', stats)
        self.assertIn('par_statut', stats)
        self.assertEqual(stats['total_alertes'], 2)
        self.assertEqual(stats['alertes_nouvelles'], 1)

    def test_resoudre_alerte(self):
        """Test résolution d'une alerte."""
        alerte = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='À résoudre',
            DESCRIPTION='Description',
            STATUT='NOUVEAU'
        )

        result = AlerteService.resoudre_alerte(
            alerte,
            commentaire='Résolu par test',
            resolu_par=None
        )

        alerte.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(alerte.STATUT, 'RESOLU')
        self.assertEqual(alerte.COMMENTAIRE_RESOLUTION, 'Résolu par test')
        self.assertIsNotNone(alerte.DATE_RESOLUTION)

    def test_ignorer_alerte(self):
        """Test ignorer une alerte."""
        alerte = AUAL.objects.create(
            TYPE_ALERTE='DOCUMENT',
            TITRE='À ignorer',
            DESCRIPTION='Description',
            STATUT='NOUVEAU'
        )

        result = AlerteService.ignorer_alerte(
            alerte,
            commentaire='Faux positif',
            ignore_par=None
        )

        alerte.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(alerte.STATUT, 'IGNORE')


class LogServiceTest(TestCase):
    """Tests pour LogService."""

    def test_get_logs_filtres_empty(self):
        """Test récupération logs avec filtres vides."""
        logs = LogService.get_logs_filtres()
        # Devrait retourner un queryset (vide ou pas)
        self.assertIsNotNone(logs)

    def test_get_stats_logs(self):
        """Test statistiques des logs."""
        stats = LogService.get_stats_logs()
        self.assertIn('total', stats)
        self.assertIn('par_action', stats)
        self.assertIn('par_table', stats)


class RapportAuditServiceTest(TestCase):
    """Tests pour RapportAuditService."""

    def test_generer_rapport_conformite(self):
        """Test génération rapport conformité."""
        date_debut = date.today() - timedelta(days=30)
        date_fin = date.today()

        rapport = RapportAuditService.generer_rapport_conformite(
            date_debut=date_debut,
            date_fin=date_fin,
            genere_par=None
        )

        self.assertIsNotNone(rapport)
        self.assertEqual(rapport.TYPE_RAPPORT, 'CONFORMITE')
        self.assertEqual(rapport.DATE_DEBUT, date_debut)
        self.assertEqual(rapport.DATE_FIN, date_fin)

    def test_generer_rapport_logs(self):
        """Test génération rapport logs."""
        date_debut = date.today() - timedelta(days=7)
        date_fin = date.today()

        rapport = RapportAuditService.generer_rapport_logs(
            date_debut=date_debut,
            date_fin=date_fin,
            genere_par=None
        )

        self.assertIsNotNone(rapport)
        self.assertEqual(rapport.TYPE_RAPPORT, 'LOGS')


# ============================================================================
# Tests des Vues
# ============================================================================

class AuditViewsTest(TestCase):
    """Tests pour les vues du module audit."""

    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        self.client.login(username='testuser', password='testpass123')

        # Créer une règle de test
        self.regle = AURC.objects.create(
            CODE='REGLE_VIEW_TEST',
            LIBELLE='Règle test vues',
            TYPE_REGLE='CONTRAT'
        )

        # Créer une alerte de test
        self.alerte = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte test vue',
            DESCRIPTION='Description test',
            STATUT='NOUVEAU',
            PRIORITE='MOYENNE'
        )

        # Créer un rapport de test
        self.rapport = AURA.objects.create(
            TITRE='Rapport test',
            TYPE_RAPPORT='CONFORMITE',
            DATE_DEBUT=date.today() - timedelta(days=30),
            DATE_FIN=date.today(),
            STATUT='TERMINE'
        )

    def test_dashboard_view(self):
        """Test de la vue dashboard."""
        response = self.client.get(reverse('audit:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/dashboard.html')

    def test_liste_alertes_view(self):
        """Test de la vue liste des alertes."""
        response = self.client.get(reverse('audit:liste_alertes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/liste_alertes.html')

    def test_detail_alerte_view(self):
        """Test de la vue détail d'une alerte."""
        response = self.client.get(
            reverse('audit:detail_alerte', kwargs={'uuid': self.alerte.uuid})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/detail_alerte.html')

    def test_liste_logs_view(self):
        """Test de la vue liste des logs."""
        response = self.client.get(reverse('audit:liste_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/liste_logs.html')

    def test_liste_rapports_view(self):
        """Test de la vue liste des rapports."""
        response = self.client.get(reverse('audit:liste_rapports'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/liste_rapports.html')

    def test_generer_rapport_view_get(self):
        """Test de la vue génération de rapport (GET)."""
        response = self.client.get(reverse('audit:generer_rapport'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/generer_rapport.html')

    def test_generer_rapport_view_post(self):
        """Test de la vue génération de rapport (POST)."""
        data = {
            'type_rapport': 'CONFORMITE',
            'format_export': 'PDF',
            'date_debut': (date.today() - timedelta(days=30)).isoformat(),
            'date_fin': date.today().isoformat()
        }
        response = self.client.post(reverse('audit:generer_rapport'), data)
        # Devrait rediriger vers la liste des rapports
        self.assertIn(response.status_code, [200, 302])

    def test_liste_regles_view(self):
        """Test de la vue liste des règles."""
        response = self.client.get(reverse('audit:liste_regles'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit/liste_regles.html')

    def test_api_stats_dashboard(self):
        """Test de l'API stats dashboard."""
        response = self.client.get(reverse('audit:api_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('total_alertes', data)
        self.assertIn('alertes_nouvelles', data)


class AuditResolutionViewsTest(TestCase):
    """Tests pour les vues de résolution d'alertes."""

    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testresolver',
            password='testpass123'
        )
        self.client.login(username='testresolver', password='testpass123')

        self.alerte = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte à résoudre',
            DESCRIPTION='Description',
            STATUT='NOUVEAU'
        )

    def test_resoudre_alerte_view(self):
        """Test de la vue résolution d'alerte."""
        response = self.client.post(
            reverse('audit:resoudre_alerte', kwargs={'uuid': self.alerte.uuid}),
            {'COMMENTAIRE_RESOLUTION': 'Résolu via test'}
        )
        # Devrait rediriger
        self.assertIn(response.status_code, [200, 302])

        self.alerte.refresh_from_db()
        self.assertEqual(self.alerte.STATUT, 'RESOLU')

    def test_ignorer_alerte_view(self):
        """Test de la vue ignorer une alerte."""
        response = self.client.post(
            reverse('audit:ignorer_alerte', kwargs={'uuid': self.alerte.uuid}),
            {'COMMENTAIRE_RESOLUTION': 'Faux positif'}
        )
        self.assertIn(response.status_code, [200, 302])

        self.alerte.refresh_from_db()
        self.assertEqual(self.alerte.STATUT, 'IGNORE')


# ============================================================================
# Tests d'Intégration
# ============================================================================

class AuditIntegrationTest(TestCase):
    """Tests d'intégration du module audit."""

    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testintegration',
            password='testpass123'
        )
        self.client.login(username='testintegration', password='testpass123')

    def test_workflow_creation_regle(self):
        """Test du workflow complet de création de règle."""
        # 1. Accéder au formulaire de création
        response = self.client.get(reverse('audit:creer_regle'))
        self.assertEqual(response.status_code, 200)

        # 2. Soumettre le formulaire
        data = {
            'CODE': 'REGLE_INTEGRATION',
            'LIBELLE': 'Règle intégration',
            'DESCRIPTION': 'Test intégration',
            'TYPE_REGLE': 'DOCUMENT',
            'SEVERITE': 'WARNING',
            'FREQUENCE_VERIFICATION': 'HEBDOMADAIRE',
            'JOURS_AVANT_EXPIRATION': 15,
            'NOTIFIER_EMPLOYE': True,
            'NOTIFIER_MANAGER': True,
            'NOTIFIER_RH': True,
            'STATUT': True
        }
        response = self.client.post(reverse('audit:creer_regle'), data)

        # 3. Vérifier la création
        self.assertTrue(AURC.objects.filter(CODE='REGLE_INTEGRATION').exists())

    def test_workflow_alerte_resolution(self):
        """Test du workflow complet de résolution d'alerte."""
        # 1. Créer une alerte
        alerte = AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte workflow',
            DESCRIPTION='Test workflow',
            STATUT='NOUVEAU',
            PRIORITE='HAUTE'
        )

        # 2. Consulter le détail
        response = self.client.get(
            reverse('audit:detail_alerte', kwargs={'uuid': alerte.uuid})
        )
        self.assertEqual(response.status_code, 200)

        # 3. Résoudre l'alerte
        response = self.client.post(
            reverse('audit:resoudre_alerte', kwargs={'uuid': alerte.uuid}),
            {'COMMENTAIRE_RESOLUTION': 'Traité'}
        )

        # 4. Vérifier la résolution
        alerte.refresh_from_db()
        self.assertEqual(alerte.STATUT, 'RESOLU')

    def test_workflow_generation_rapport(self):
        """Test du workflow de génération de rapport."""
        # 1. Accéder au formulaire
        response = self.client.get(reverse('audit:generer_rapport'))
        self.assertEqual(response.status_code, 200)

        # 2. Compter les rapports existants
        count_before = AURA.objects.count()

        # 3. Générer un rapport
        data = {
            'type_rapport': 'ALERTES',
            'format_export': 'EXCEL',
            'date_debut': (date.today() - timedelta(days=7)).isoformat(),
            'date_fin': date.today().isoformat()
        }
        response = self.client.post(reverse('audit:generer_rapport'), data)

        # 4. Vérifier la création
        count_after = AURA.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_filtres_alertes(self):
        """Test des filtres sur la liste des alertes."""
        # Créer plusieurs alertes
        AUAL.objects.create(
            TYPE_ALERTE='CONTRAT',
            TITRE='Alerte contrat',
            DESCRIPTION='Desc',
            STATUT='NOUVEAU',
            PRIORITE='HAUTE'
        )
        AUAL.objects.create(
            TYPE_ALERTE='DOCUMENT',
            TITRE='Alerte document',
            DESCRIPTION='Desc',
            STATUT='RESOLU',
            PRIORITE='BASSE'
        )

        # Filtrer par statut
        response = self.client.get(
            reverse('audit:liste_alertes'),
            {'statut': 'NOUVEAU'}
        )
        self.assertEqual(response.status_code, 200)

        # Filtrer par type
        response = self.client.get(
            reverse('audit:liste_alertes'),
            {'type_alerte': 'CONTRAT'}
        )
        self.assertEqual(response.status_code, 200)

        # Filtrer par priorité
        response = self.client.get(
            reverse('audit:liste_alertes'),
            {'priorite': 'HAUTE'}
        )
        self.assertEqual(response.status_code, 200)


# ============================================================================
# Tests de Sécurité
# ============================================================================

class AuditSecurityTest(TestCase):
    """Tests de sécurité du module audit."""

    def test_acces_non_authentifie_dashboard(self):
        """Test d'accès non authentifié au dashboard."""
        client = Client()
        response = client.get(reverse('audit:dashboard'))
        # Devrait rediriger vers login
        self.assertIn(response.status_code, [302, 403])

    def test_acces_non_authentifie_alertes(self):
        """Test d'accès non authentifié aux alertes."""
        client = Client()
        response = client.get(reverse('audit:liste_alertes'))
        self.assertIn(response.status_code, [302, 403])

    def test_alerte_inexistante(self):
        """Test d'accès à une alerte inexistante."""
        client = Client()
        user = User.objects.create_user(
            username='testsecurity',
            password='testpass123'
        )
        client.login(username='testsecurity', password='testpass123')

        import uuid as uuid_lib
        fake_uuid = uuid_lib.uuid4()
        response = client.get(
            reverse('audit:detail_alerte', kwargs={'uuid': fake_uuid})
        )
        self.assertEqual(response.status_code, 404)

# gestion_temps_activite/tests/test_views.py
"""
Tests pour les vues de l'application Gestion Temps et Activités.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock

User = get_user_model()


class TestViewImports(TestCase):
    """Tests pour vérifier les imports des vues."""

    def test_client_views_import(self):
        """Test import vues client."""
        from gestion_temps_activite.views.client_views import (
            client_liste,
            client_detail,
            client_create,
            client_update,
            client_delete,
        )
        self.assertTrue(callable(client_liste))
        self.assertTrue(callable(client_detail))
        self.assertTrue(callable(client_create))
        self.assertTrue(callable(client_update))
        self.assertTrue(callable(client_delete))

    def test_activite_views_import(self):
        """Test import vues activité."""
        from gestion_temps_activite.views.activite_views import (
            activite_liste,
            activite_create,
            activite_update,
            activite_delete,
        )
        self.assertTrue(callable(activite_liste))
        self.assertTrue(callable(activite_create))
        self.assertTrue(callable(activite_update))
        self.assertTrue(callable(activite_delete))

    def test_projet_views_import(self):
        """Test import vues projet."""
        from gestion_temps_activite.views.projet_views import (
            projet_liste,
            projet_detail,
            projet_create,
            projet_update,
            projet_delete,
        )
        self.assertTrue(callable(projet_liste))
        self.assertTrue(callable(projet_detail))
        self.assertTrue(callable(projet_create))
        self.assertTrue(callable(projet_update))
        self.assertTrue(callable(projet_delete))

    def test_tache_views_import(self):
        """Test import vues tâche."""
        from gestion_temps_activite.views.tache_views import (
            tache_liste,
            tache_detail,
            tache_create,
            tache_update,
            tache_delete,
        )
        self.assertTrue(callable(tache_liste))
        self.assertTrue(callable(tache_detail))
        self.assertTrue(callable(tache_create))
        self.assertTrue(callable(tache_update))
        self.assertTrue(callable(tache_delete))

    def test_document_views_import(self):
        """Test import vues document."""
        from gestion_temps_activite.views.document_views import (
            document_upload,
            document_delete,
        )
        self.assertTrue(callable(document_upload))
        self.assertTrue(callable(document_delete))

    def test_imputation_views_import(self):
        """Test import vues imputation."""
        from gestion_temps_activite.views.imputation_views import (
            imputation_liste,
            imputation_mes_temps,
            imputation_create,
            imputation_update,
            imputation_delete,
            imputation_validation,
            imputation_valider,
            imputation_rejeter,
            imputation_export_excel,
        )
        self.assertTrue(callable(imputation_liste))
        self.assertTrue(callable(imputation_mes_temps))
        self.assertTrue(callable(imputation_create))
        self.assertTrue(callable(imputation_update))
        self.assertTrue(callable(imputation_delete))
        self.assertTrue(callable(imputation_validation))
        self.assertTrue(callable(imputation_valider))
        self.assertTrue(callable(imputation_rejeter))
        self.assertTrue(callable(imputation_export_excel))

    def test_commentaire_views_import(self):
        """Test import vues commentaire."""
        from gestion_temps_activite.views.commentaire_views import (
            commentaire_ajouter,
            commentaire_repondre,
            commentaire_modifier,
            commentaire_supprimer,
            commentaire_mentions,
        )
        self.assertTrue(callable(commentaire_ajouter))
        self.assertTrue(callable(commentaire_repondre))
        self.assertTrue(callable(commentaire_modifier))
        self.assertTrue(callable(commentaire_supprimer))
        self.assertTrue(callable(commentaire_mentions))

    def test_notification_views_import(self):
        """Test import vues notification."""
        from gestion_temps_activite.views.notification_views import (
            notification_tache_detail,
            toutes_notifications_gta,
            marquer_notification_gta_lue,
            marquer_toutes_notifications_gta_lues,
        )
        self.assertTrue(callable(notification_tache_detail))
        self.assertTrue(callable(toutes_notifications_gta))
        self.assertTrue(callable(marquer_notification_gta_lue))
        self.assertTrue(callable(marquer_toutes_notifications_gta_lues))

    def test_dashboard_views_import(self):
        """Test import vues dashboard."""
        from gestion_temps_activite.views.dashboard_views import dashboard
        self.assertTrue(callable(dashboard))

    def test_api_views_import(self):
        """Test import vues API."""
        from gestion_temps_activite.views.api_views import (
            api_taches_par_projet,
            api_activites_en_vigueur,
        )
        self.assertTrue(callable(api_taches_par_projet))
        self.assertTrue(callable(api_activites_en_vigueur))

    def test_views_module_import(self):
        """Test import depuis le module principal views."""
        from gestion_temps_activite import views

        # Vérifier quelques vues clés
        self.assertTrue(hasattr(views, 'dashboard'))
        self.assertTrue(hasattr(views, 'client_liste'))
        self.assertTrue(hasattr(views, 'projet_liste'))
        self.assertTrue(hasattr(views, 'tache_liste'))
        self.assertTrue(hasattr(views, 'imputation_liste'))


class TestNotificationHelpers(TestCase):
    """Tests pour les helpers de notification."""

    def test_notifier_nouvelle_tache_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_nouvelle_tache
        self.assertTrue(callable(notifier_nouvelle_tache))

    def test_notifier_reassignation_tache_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_reassignation_tache
        self.assertTrue(callable(notifier_reassignation_tache))

    def test_notifier_modification_tache_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_modification_tache
        self.assertTrue(callable(notifier_modification_tache))

    def test_notifier_changement_statut_tache_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_changement_statut_tache
        self.assertTrue(callable(notifier_changement_statut_tache))

    def test_notifier_nouveau_commentaire_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_nouveau_commentaire
        self.assertTrue(callable(notifier_nouveau_commentaire))

    def test_notifier_echeance_tache_proche_function_exists(self):
        """Test que la fonction existe."""
        from gestion_temps_activite.views.notification_views import notifier_echeance_tache_proche
        self.assertTrue(callable(notifier_echeance_tache_proche))


class TestTacheViewsHelpers(TestCase):
    """Tests pour les helpers des vues tâches."""

    def test_detecter_changements_function_exists(self):
        """Test que la fonction detecter_changements existe."""
        from gestion_temps_activite.views.tache_views import detecter_changements
        self.assertTrue(callable(detecter_changements))

    def test_detecter_changements_with_changes(self):
        """Test détection de changements."""
        from gestion_temps_activite.views.tache_views import detecter_changements

        mock_form = Mock()
        mock_form.changed_data = ['titre', 'description']
        mock_form.fields = {
            'titre': Mock(label='Titre'),
            'description': Mock(label='Description'),
            'statut': Mock(label='Statut'),
        }

        mock_tache = Mock()

        changements = detecter_changements(mock_form, mock_tache, ['titre', 'description', 'statut'])

        self.assertEqual(len(changements), 2)
        self.assertIn('Titre', changements)
        self.assertIn('Description', changements)

    def test_detecter_changements_no_changes(self):
        """Test sans changements."""
        from gestion_temps_activite.views.tache_views import detecter_changements

        mock_form = Mock()
        mock_form.changed_data = []
        mock_form.fields = {}

        mock_tache = Mock()

        changements = detecter_changements(mock_form, mock_tache, ['titre'])

        self.assertEqual(len(changements), 0)

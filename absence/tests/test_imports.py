# absence/tests/test_imports.py
"""
Tests pour vérifier que tous les modules s'importent correctement
après la migration vers l'architecture modulaire.
"""
from django.test import TestCase


class TestModuleImports(TestCase):
    """Tests d'importation des modules."""

    def test_import_views_main(self):
        """Test import du fichier views.py principal."""
        from absence import views
        self.assertIsNotNone(views)

    def test_import_urls(self):
        """Test import du fichier urls.py."""
        from absence import urls
        self.assertIsNotNone(urls)
        self.assertTrue(hasattr(urls, 'urlpatterns'))
        self.assertTrue(hasattr(urls, 'app_name'))
        self.assertEqual(urls.app_name, 'absence')

    # ===== TESTS VIEWS_MODULES =====

    def test_import_views_modules_init(self):
        """Test import views_modules/__init__.py."""
        from absence import views_modules
        self.assertIsNotNone(views_modules)

    def test_import_configuration_views(self):
        """Test import views_modules/configuration_views.py."""
        from absence.views_modules import configuration_views
        self.assertTrue(hasattr(configuration_views, 'liste_conventions'))
        self.assertTrue(hasattr(configuration_views, 'liste_jours_feries'))
        self.assertTrue(hasattr(configuration_views, 'liste_types_absence'))
        self.assertTrue(hasattr(configuration_views, 'liste_parametres_calcul'))

    def test_import_acquisition_views(self):
        """Test import views_modules/acquisition_views.py."""
        from absence.views_modules import acquisition_views
        self.assertTrue(hasattr(acquisition_views, 'liste_acquisitions'))

    def test_import_absence_views(self):
        """Test import views_modules/absence_views.py."""
        from absence.views_modules import absence_views
        self.assertTrue(hasattr(absence_views, 'liste_absences'))
        self.assertTrue(hasattr(absence_views, 'creer_absence'))
        self.assertTrue(hasattr(absence_views, 'modifier_absence'))

    def test_import_validation_views(self):
        """Test import views_modules/validation_views.py."""
        from absence.views_modules import validation_views
        self.assertTrue(hasattr(validation_views, 'validation_manager'))
        self.assertTrue(hasattr(validation_views, 'validation_rh'))
        self.assertTrue(hasattr(validation_views, 'consultation_absences'))

    # ===== TESTS VIEWS_API =====

    def test_import_views_api_init(self):
        """Test import views_api/__init__.py."""
        from absence import views_api
        self.assertIsNotNone(views_api)

    def test_import_convention_api(self):
        """Test import views_api/convention_api.py."""
        from absence.views_api import convention_api
        self.assertTrue(hasattr(convention_api, 'api_convention_detail'))
        self.assertTrue(hasattr(convention_api, 'api_convention_create'))
        self.assertTrue(hasattr(convention_api, 'api_convention_update'))
        self.assertTrue(hasattr(convention_api, 'api_convention_delete'))
        self.assertTrue(hasattr(convention_api, 'api_convention_toggle_actif'))

    def test_import_jour_ferie_api(self):
        """Test import views_api/jour_ferie_api.py."""
        from absence.views_api import jour_ferie_api
        self.assertTrue(hasattr(jour_ferie_api, 'api_jour_ferie_detail'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_jour_ferie_create'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_jour_ferie_update'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_jour_ferie_delete'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_jour_ferie_toggle'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_dupliquer_jours_feries'))
        self.assertTrue(hasattr(jour_ferie_api, 'api_jours_feries'))

    def test_import_type_absence_api(self):
        """Test import views_api/type_absence_api.py."""
        from absence.views_api import type_absence_api
        self.assertTrue(hasattr(type_absence_api, 'api_type_absence_detail'))
        self.assertTrue(hasattr(type_absence_api, 'api_type_absence_create'))
        self.assertTrue(hasattr(type_absence_api, 'api_type_absence_update'))
        self.assertTrue(hasattr(type_absence_api, 'api_type_absence_delete'))
        self.assertTrue(hasattr(type_absence_api, 'api_type_absence_toggle'))

    def test_import_parametre_calcul_api(self):
        """Test import views_api/parametre_calcul_api.py."""
        from absence.views_api import parametre_calcul_api
        self.assertTrue(hasattr(parametre_calcul_api, 'api_parametre_calcul_detail'))
        self.assertTrue(hasattr(parametre_calcul_api, 'api_parametre_calcul_create'))
        self.assertTrue(hasattr(parametre_calcul_api, 'api_parametre_calcul_update'))
        self.assertTrue(hasattr(parametre_calcul_api, 'api_parametre_calcul_delete'))

    def test_import_acquisition_api(self):
        """Test import views_api/acquisition_api.py."""
        from absence.views_api import acquisition_api
        self.assertTrue(hasattr(acquisition_api, 'api_acquisition_detail'))
        self.assertTrue(hasattr(acquisition_api, 'api_acquisition_update'))
        self.assertTrue(hasattr(acquisition_api, 'api_acquisition_delete'))
        self.assertTrue(hasattr(acquisition_api, 'api_recalculer_acquisition'))
        self.assertTrue(hasattr(acquisition_api, 'api_calculer_acquisitions'))
        self.assertTrue(hasattr(acquisition_api, 'api_calculer_acquis_a_date'))
        self.assertTrue(hasattr(acquisition_api, 'api_acquisition_employe_annee'))

    def test_import_absence_api(self):
        """Test import views_api/absence_api.py."""
        from absence.views_api import absence_api
        self.assertTrue(hasattr(absence_api, 'api_absence_detail'))
        self.assertTrue(hasattr(absence_api, 'api_absence_delete'))
        self.assertTrue(hasattr(absence_api, 'api_absence_annuler'))
        self.assertTrue(hasattr(absence_api, 'api_valider_absence'))
        self.assertTrue(hasattr(absence_api, 'api_historique_validation'))
        self.assertTrue(hasattr(absence_api, 'api_verifier_solde'))
        self.assertTrue(hasattr(absence_api, 'api_mes_absences_calendrier'))

    def test_import_notification_api(self):
        """Test import views_api/notification_api.py."""
        from absence.views_api import notification_api
        self.assertTrue(hasattr(notification_api, 'notification_detail'))
        self.assertTrue(hasattr(notification_api, 'marquer_toutes_lues'))
        self.assertTrue(hasattr(notification_api, 'toutes_notifications'))
        self.assertTrue(hasattr(notification_api, 'notification_counts'))
        self.assertTrue(hasattr(notification_api, 'marquer_notification_lue'))

    # ===== TESTS SERVICES =====

    def test_import_services_init(self):
        """Test import services/__init__.py."""
        from absence import services
        self.assertIsNotNone(services)

    def test_import_acquisition_service(self):
        """Test import services/acquisition_service.py."""
        from absence.services import acquisition_service
        self.assertTrue(hasattr(acquisition_service, 'AcquisitionService'))

    def test_import_absence_service(self):
        """Test import services/absence_service.py."""
        from absence.services import absence_service
        self.assertTrue(hasattr(absence_service, 'AbsenceService'))

    def test_import_notification_service(self):
        """Test import services/notification_service.py."""
        from absence.services import notification_service
        self.assertTrue(hasattr(notification_service, 'NotificationService'))

    def test_import_validation_service(self):
        """Test import services/validation_service.py."""
        from absence.services import validation_service
        self.assertTrue(hasattr(validation_service, 'ValidationService'))


class TestViewsReexports(TestCase):
    """Tests que views.py réexporte correctement toutes les fonctions."""

    def test_views_exports_configuration_views(self):
        """Test que views.py exporte les vues de configuration."""
        from absence import views
        self.assertTrue(hasattr(views, 'liste_conventions'))
        self.assertTrue(hasattr(views, 'liste_jours_feries'))
        self.assertTrue(hasattr(views, 'liste_types_absence'))
        self.assertTrue(hasattr(views, 'liste_parametres_calcul'))

    def test_views_exports_acquisition_views(self):
        """Test que views.py exporte les vues d'acquisition."""
        from absence import views
        self.assertTrue(hasattr(views, 'liste_acquisitions'))

    def test_views_exports_absence_views(self):
        """Test que views.py exporte les vues d'absence."""
        from absence import views
        self.assertTrue(hasattr(views, 'liste_absences'))
        self.assertTrue(hasattr(views, 'creer_absence'))
        self.assertTrue(hasattr(views, 'modifier_absence'))

    def test_views_exports_validation_views(self):
        """Test que views.py exporte les vues de validation."""
        from absence import views
        self.assertTrue(hasattr(views, 'validation_manager'))
        self.assertTrue(hasattr(views, 'validation_rh'))
        self.assertTrue(hasattr(views, 'consultation_absences'))

    def test_views_exports_convention_apis(self):
        """Test que views.py exporte les APIs de convention."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_convention_detail'))
        self.assertTrue(hasattr(views, 'api_convention_create'))
        self.assertTrue(hasattr(views, 'api_convention_update'))
        self.assertTrue(hasattr(views, 'api_convention_delete'))
        self.assertTrue(hasattr(views, 'api_convention_toggle_actif'))

    def test_views_exports_jour_ferie_apis(self):
        """Test que views.py exporte les APIs de jour férié."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_jour_ferie_detail'))
        self.assertTrue(hasattr(views, 'api_jour_ferie_create'))
        self.assertTrue(hasattr(views, 'api_jour_ferie_update'))
        self.assertTrue(hasattr(views, 'api_jour_ferie_delete'))
        self.assertTrue(hasattr(views, 'api_jour_ferie_toggle'))
        self.assertTrue(hasattr(views, 'api_dupliquer_jours_feries'))
        self.assertTrue(hasattr(views, 'api_jours_feries'))

    def test_views_exports_type_absence_apis(self):
        """Test que views.py exporte les APIs de type absence."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_type_absence_detail'))
        self.assertTrue(hasattr(views, 'api_type_absence_create'))
        self.assertTrue(hasattr(views, 'api_type_absence_update'))
        self.assertTrue(hasattr(views, 'api_type_absence_delete'))
        self.assertTrue(hasattr(views, 'api_type_absence_toggle'))

    def test_views_exports_parametre_calcul_apis(self):
        """Test que views.py exporte les APIs de paramètre calcul."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_parametre_calcul_detail'))
        self.assertTrue(hasattr(views, 'api_parametre_calcul_create'))
        self.assertTrue(hasattr(views, 'api_parametre_calcul_update'))
        self.assertTrue(hasattr(views, 'api_parametre_calcul_delete'))

    def test_views_exports_acquisition_apis(self):
        """Test que views.py exporte les APIs d'acquisition."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_acquisition_detail'))
        self.assertTrue(hasattr(views, 'api_acquisition_update'))
        self.assertTrue(hasattr(views, 'api_acquisition_delete'))
        self.assertTrue(hasattr(views, 'api_recalculer_acquisition'))
        self.assertTrue(hasattr(views, 'api_calculer_acquisitions'))
        self.assertTrue(hasattr(views, 'api_calculer_acquis_a_date'))
        self.assertTrue(hasattr(views, 'api_acquisition_employe_annee'))

    def test_views_exports_absence_apis(self):
        """Test que views.py exporte les APIs d'absence."""
        from absence import views
        self.assertTrue(hasattr(views, 'api_absence_detail'))
        self.assertTrue(hasattr(views, 'api_absence_delete'))
        self.assertTrue(hasattr(views, 'api_absence_annuler'))
        self.assertTrue(hasattr(views, 'api_valider_absence'))
        self.assertTrue(hasattr(views, 'api_historique_validation'))
        self.assertTrue(hasattr(views, 'api_verifier_solde'))
        self.assertTrue(hasattr(views, 'api_mes_absences_calendrier'))

    def test_views_exports_notification_apis(self):
        """Test que views.py exporte les APIs de notification."""
        from absence import views
        self.assertTrue(hasattr(views, 'notification_detail'))
        self.assertTrue(hasattr(views, 'marquer_toutes_lues'))
        self.assertTrue(hasattr(views, 'toutes_notifications'))
        self.assertTrue(hasattr(views, 'notification_counts'))
        self.assertTrue(hasattr(views, 'marquer_notification_lue'))


class TestUrlPatterns(TestCase):
    """Tests pour vérifier les patterns d'URL."""

    def test_url_patterns_count(self):
        """Test que le nombre d'URLs est correct."""
        from absence.urls import urlpatterns
        # Comptage des URLs dans le fichier
        # Absences: 6 pages + 8 APIs = 14
        # Acquisitions: 1 page + 7 APIs = 8
        # Conventions: 1 page + 5 APIs = 6
        # Jours fériés: 1 page + 7 APIs = 8
        # Types absence: 1 page + 5 APIs = 6
        # Paramètres: 1 page + 5 APIs = 6
        # Notifications: 5
        # Total attendu: ~53
        self.assertGreaterEqual(len(urlpatterns), 40)

    def test_url_names_exist(self):
        """Test que les noms d'URL existent."""
        from django.urls import reverse, NoReverseMatch

        url_names = [
            'absence:liste_absences',
            'absence:creer_absence',
            'absence:validation_manager',
            'absence:validation_rh',
            'absence:consultation_absences',
            'absence:liste_acquisitions',
            'absence:liste_conventions',
            'absence:liste_jours_feries',
            'absence:liste_types_absence',
            'absence:liste_parametres_calcul',
            'absence:toutes_notifications',
            'absence:marquer_toutes_lues',
            'absence:notification_counts',
        ]

        for name in url_names:
            try:
                url = reverse(name)
                self.assertIsNotNone(url)
            except NoReverseMatch:
                self.fail(f"URL name '{name}' not found")

    def test_url_with_params_exist(self):
        """Test que les URLs avec paramètres existent."""
        from django.urls import reverse, NoReverseMatch

        url_params = [
            ('absence:modifier_absence', {'id': 1}),
            ('absence:api_absence_detail', {'id': 1}),
            ('absence:api_convention_detail', {'id': 1}),
            ('absence:api_jour_ferie_detail', {'id': 1}),
            ('absence:api_type_absence_detail', {'id': 1}),
            ('absence:api_parametre_calcul_detail', {'id': 1}),
            ('absence:api_acquisition_detail', {'id': 1}),
            ('absence:notification_detail', {'id': 1}),
        ]

        for name, kwargs in url_params:
            try:
                url = reverse(name, kwargs=kwargs)
                self.assertIsNotNone(url)
            except NoReverseMatch:
                self.fail(f"URL name '{name}' with params {kwargs} not found")

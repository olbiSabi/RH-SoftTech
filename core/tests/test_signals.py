# core/tests/test_signals.py
"""
Tests pour le système d'audit basé sur les signals.
"""
from django.test import TestCase

from core.signals import (
    get_current_request,
    get_current_user,
    set_current_request,
    model_to_dict,
)


class TestThreadLocalFunctions(TestCase):
    """Tests pour les fonctions thread-local."""

    def tearDown(self):
        """Nettoyer après chaque test."""
        set_current_request(None)

    def test_set_and_get_current_request(self):
        """Test set/get current request."""
        # Initialement None
        self.assertIsNone(get_current_request())

        # Définir une requête mock
        mock_request = object()
        set_current_request(mock_request)

        # Vérifier qu'on la récupère
        self.assertEqual(get_current_request(), mock_request)

    def test_get_current_user_no_request(self):
        """Test get_current_user sans requête."""
        set_current_request(None)
        self.assertIsNone(get_current_user())

    def test_get_current_user_with_request(self):
        """Test get_current_user avec requête."""
        class MockRequest:
            class MockUser:
                pass
            user = MockUser()

        mock_request = MockRequest()
        set_current_request(mock_request)

        user = get_current_user()
        self.assertIsNotNone(user)
        self.assertIsInstance(user, MockRequest.MockUser)


class TestModelToDict(TestCase):
    """Tests pour la fonction model_to_dict."""

    def test_model_to_dict_basic(self):
        """Test conversion basique."""
        from core.models import ZDLOG

        log = ZDLOG(
            TABLE_NAME='Test',
            RECORD_ID='123',
            TYPE_MOUVEMENT='CREATE',
            DESCRIPTION='Test description'
        )

        data = model_to_dict(log)

        self.assertIn('TABLE_NAME', data)
        self.assertEqual(data['TABLE_NAME'], 'Test')
        self.assertIn('RECORD_ID', data)
        self.assertEqual(data['RECORD_ID'], '123')

    def test_model_to_dict_excludes_id(self):
        """Test que 'id' est exclu par défaut."""
        from core.models import ZDLOG

        log = ZDLOG(
            TABLE_NAME='Test',
            RECORD_ID='123',
            TYPE_MOUVEMENT='CREATE'
        )

        data = model_to_dict(log)
        self.assertNotIn('id', data)

    def test_model_to_dict_custom_exclude(self):
        """Test exclusion personnalisée."""
        from core.models import ZDLOG

        log = ZDLOG(
            TABLE_NAME='Test',
            RECORD_ID='123',
            TYPE_MOUVEMENT='CREATE',
            DESCRIPTION='Test'
        )

        data = model_to_dict(log, exclude_fields=['id', 'DESCRIPTION'])
        self.assertNotIn('DESCRIPTION', data)

    def test_model_to_dict_datetime_serialization(self):
        """Test sérialisation des dates."""
        from django.utils import timezone
        from core.models import ZDLOG

        log = ZDLOG(
            TABLE_NAME='Test',
            RECORD_ID='123',
            TYPE_MOUVEMENT='CREATE',
            DATE_MODIFICATION=timezone.now()
        )

        data = model_to_dict(log)

        # Les dates doivent être converties en ISO format
        self.assertIn('DATE_MODIFICATION', data)
        self.assertIsInstance(data['DATE_MODIFICATION'], str)


class TestAuditSignalsRegistration(TestCase):
    """Tests pour l'enregistrement des signals d'audit."""

    def test_signals_module_loads(self):
        """Test que le module signals se charge sans erreur."""
        from core import signals
        self.assertIsNotNone(signals)

    def test_register_function_exists(self):
        """Test que register_all_audit_signals existe."""
        from core.signals import register_all_audit_signals
        self.assertTrue(callable(register_all_audit_signals))

    def test_create_audit_handlers_exists(self):
        """Test que create_audit_handlers existe."""
        from core.signals import create_audit_handlers
        self.assertTrue(callable(create_audit_handlers))


class TestDescriptionFunctions(TestCase):
    """Tests pour les fonctions de description."""

    def test_description_functions_exist(self):
        """Test que les fonctions de description existent."""
        from core import signals

        description_funcs = [
            '_get_description_zdde',
            '_get_description_zdpo',
            '_get_description_zy00',
            '_get_description_zyco',
            '_get_description_zyte',
            '_get_description_zyme',
            '_get_description_zyaf',
            '_get_description_zyad',
            '_get_description_zydo',
            '_get_description_zyfa',
            '_get_description_zypp',
            '_get_description_zyib',
            '_get_description_zyma',
            '_get_description_config_conv',
            '_get_description_type_absence',
            '_get_description_jour_ferie',
            '_get_description_param_calcul',
            '_get_description_acquisition',
            '_get_description_absence',
            '_get_description_validation',
            '_get_description_notification',
            '_get_description_entreprise',
        ]

        for func_name in description_funcs:
            self.assertTrue(
                hasattr(signals, func_name),
                f"Function {func_name} not found in signals module"
            )

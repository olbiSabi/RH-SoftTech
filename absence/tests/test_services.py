# absence/tests/test_services.py
"""
Tests pour les services métier de l'application absence.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase


class TestValidationService(TestCase):
    """Tests pour ValidationService."""

    def test_validate_date_range_valid(self):
        """Test validation plage de dates valide dans le futur."""
        from absence.services.validation_service import ValidationService

        tomorrow = date.today() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)

        result = ValidationService.validate_date_range(tomorrow, day_after)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_validate_date_range_invalid_order(self):
        """Test validation plage de dates avec ordre inversé."""
        from absence.services.validation_service import ValidationService

        tomorrow = date.today() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)

        result = ValidationService.validate_date_range(day_after, tomorrow)
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)

    def test_validate_date_range_same_day(self):
        """Test validation même jour dans le futur."""
        from absence.services.validation_service import ValidationService

        tomorrow = date.today() + timedelta(days=1)

        result = ValidationService.validate_date_range(tomorrow, tomorrow)
        self.assertTrue(result['valid'])

    def test_validate_date_range_past_date(self):
        """Test validation date dans le passé."""
        from absence.services.validation_service import ValidationService

        yesterday = date.today() - timedelta(days=1)
        today = date.today()

        result = ValidationService.validate_date_range(yesterday, today)
        self.assertFalse(result['valid'])
        self.assertIn("passé", str(result['errors']))

    def test_validate_date_range_missing_dates(self):
        """Test validation avec dates manquantes."""
        from absence.services.validation_service import ValidationService

        result = ValidationService.validate_date_range(None, None)
        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 2)

    def test_parse_date_from_string_iso_format(self):
        """Test parsing date format ISO."""
        from absence.services.validation_service import ValidationService

        result = ValidationService.parse_date_from_string('2025-01-15')
        self.assertIsNotNone(result['date'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['date'], date(2025, 1, 15))

    def test_parse_date_from_string_french_format(self):
        """Test parsing date format français."""
        from absence.services.validation_service import ValidationService

        result = ValidationService.parse_date_from_string('15/01/2025')
        self.assertIsNotNone(result['date'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['date'], date(2025, 1, 15))

    def test_parse_date_from_string_invalid(self):
        """Test parsing date invalide."""
        from absence.services.validation_service import ValidationService

        result = ValidationService.parse_date_from_string('not-a-date')
        self.assertIsNone(result['date'])
        self.assertIsNotNone(result['error'])

    def test_parse_date_from_string_empty(self):
        """Test parsing date vide."""
        from absence.services.validation_service import ValidationService

        result = ValidationService.parse_date_from_string('')
        self.assertIsNone(result['date'])
        self.assertIsNotNone(result['error'])


class TestAcquisitionService(TestCase):
    """Tests pour AcquisitionService."""

    def test_service_class_exists(self):
        """Test que la classe AcquisitionService existe."""
        from absence.services.acquisition_service import AcquisitionService
        self.assertIsNotNone(AcquisitionService)

    def test_calculer_jours_acquis_au_method_exists(self):
        """Test que la méthode calculer_jours_acquis_au existe."""
        from absence.services.acquisition_service import AcquisitionService
        self.assertTrue(hasattr(AcquisitionService, 'calculer_jours_acquis_au'))

    def test_calculer_mois_travailles_jusquau_method_exists(self):
        """Test que la méthode calculer_mois_travailles_jusquau existe."""
        from absence.services.acquisition_service import AcquisitionService
        self.assertTrue(hasattr(AcquisitionService, 'calculer_mois_travailles_jusquau'))

    def test_calculer_jours_anciennete_method_exists(self):
        """Test que la méthode calculer_jours_anciennete existe."""
        from absence.services.acquisition_service import AcquisitionService
        self.assertTrue(hasattr(AcquisitionService, 'calculer_jours_anciennete'))

    def test_recalculer_acquisition_method_exists(self):
        """Test que la méthode recalculer_acquisition existe."""
        from absence.services.acquisition_service import AcquisitionService
        self.assertTrue(hasattr(AcquisitionService, 'recalculer_acquisition'))


class TestAbsenceService(TestCase):
    """Tests pour AbsenceService."""

    def test_service_class_exists(self):
        """Test que la classe AbsenceService existe."""
        from absence.services.absence_service import AbsenceService
        self.assertIsNotNone(AbsenceService)

    def test_soumettre_absence_method_exists(self):
        """Test que la méthode soumettre_absence existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'soumettre_absence'))

    def test_valider_manager_method_exists(self):
        """Test que la méthode valider_manager existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'valider_manager'))

    def test_valider_rh_method_exists(self):
        """Test que la méthode valider_rh existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'valider_rh'))

    def test_annuler_absence_method_exists(self):
        """Test que la méthode annuler_absence existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'annuler_absence'))

    def test_rejeter_manager_method_exists(self):
        """Test que la méthode rejeter_manager existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'rejeter_manager'))

    def test_rejeter_rh_method_exists(self):
        """Test que la méthode rejeter_rh existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'rejeter_rh'))

    def test_calculer_nombre_jours_method_exists(self):
        """Test que la méthode calculer_nombre_jours existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'calculer_nombre_jours'))

    def test_verifier_solde_method_exists(self):
        """Test que la méthode verifier_solde existe."""
        from absence.services.absence_service import AbsenceService
        self.assertTrue(hasattr(AbsenceService, 'verifier_solde'))

    def test_statuts_constants_exist(self):
        """Test que les constantes de statuts existent."""
        from absence.services.absence_service import AbsenceService
        self.assertEqual(AbsenceService.BROUILLON, 'BROUILLON')
        self.assertEqual(AbsenceService.EN_ATTENTE_MANAGER, 'EN_ATTENTE_MANAGER')
        self.assertEqual(AbsenceService.EN_ATTENTE_RH, 'EN_ATTENTE_RH')
        self.assertEqual(AbsenceService.VALIDE, 'VALIDE')
        self.assertEqual(AbsenceService.REJETE, 'REJETE')
        self.assertEqual(AbsenceService.ANNULE, 'ANNULE')


class TestNotificationService(TestCase):
    """Tests pour NotificationService."""

    def test_service_class_exists(self):
        """Test que la classe NotificationService existe."""
        from absence.services.notification_service import NotificationService
        self.assertIsNotNone(NotificationService)

    def test_notifier_nouvelle_demande_method_exists(self):
        """Test que la méthode notifier_nouvelle_demande existe."""
        from absence.services.notification_service import NotificationService
        self.assertTrue(hasattr(NotificationService, 'notifier_nouvelle_demande'))

    def test_notifier_validation_manager_method_exists(self):
        """Test que la méthode notifier_validation_manager existe."""
        from absence.services.notification_service import NotificationService
        self.assertTrue(hasattr(NotificationService, 'notifier_validation_manager'))

    def test_notifier_validation_rh_method_exists(self):
        """Test que la méthode notifier_validation_rh existe."""
        from absence.services.notification_service import NotificationService
        self.assertTrue(hasattr(NotificationService, 'notifier_validation_rh'))


class TestValidationServiceAdvanced(TestCase):
    """Tests avancés pour ValidationService."""

    def test_can_employee_submit_method_exists(self):
        """Test que la méthode can_employee_submit existe."""
        from absence.services.validation_service import ValidationService
        self.assertTrue(hasattr(ValidationService, 'can_employee_submit'))

    def test_can_manager_validate_method_exists(self):
        """Test que la méthode can_manager_validate existe."""
        from absence.services.validation_service import ValidationService
        self.assertTrue(hasattr(ValidationService, 'can_manager_validate'))

    def test_can_rh_validate_method_exists(self):
        """Test que la méthode can_rh_validate existe."""
        from absence.services.validation_service import ValidationService
        self.assertTrue(hasattr(ValidationService, 'can_rh_validate'))

    def test_can_cancel_method_exists(self):
        """Test que la méthode can_cancel existe."""
        from absence.services.validation_service import ValidationService
        self.assertTrue(hasattr(ValidationService, 'can_cancel'))

    def test_check_overlap_method_exists(self):
        """Test que la méthode check_overlap existe."""
        from absence.services.validation_service import ValidationService
        self.assertTrue(hasattr(ValidationService, 'check_overlap'))


class TestServiceIntegration(TestCase):
    """Tests d'intégration entre services."""

    def test_services_can_be_imported_together(self):
        """Test que tous les services peuvent être importés ensemble."""
        from absence.services import (
            AcquisitionService,
            AbsenceService,
            NotificationService,
            ValidationService,
        )

        self.assertIsNotNone(AcquisitionService)
        self.assertIsNotNone(AbsenceService)
        self.assertIsNotNone(NotificationService)
        self.assertIsNotNone(ValidationService)

    def test_services_are_classes(self):
        """Test que les services sont des classes."""
        from absence.services import (
            AcquisitionService,
            AbsenceService,
            NotificationService,
            ValidationService,
        )

        self.assertTrue(isinstance(AcquisitionService, type))
        self.assertTrue(isinstance(AbsenceService, type))
        self.assertTrue(isinstance(NotificationService, type))
        self.assertTrue(isinstance(ValidationService, type))

    def test_services_have_static_methods(self):
        """Test que les services ont des méthodes statiques."""
        from absence.services import ValidationService

        # Tester que validate_date_range est une méthode statique
        self.assertTrue(callable(ValidationService.validate_date_range))

# employee/tests/test_services/test_validation_service.py
"""
Tests pour ValidationService.
"""
from datetime import date

from django.test import TestCase

from employee.services.validation_service import ValidationService


class ValidationServiceTestCase(TestCase):
    """Tests pour ValidationService."""

    # ===== Tests validate_date_range =====

    def test_validate_date_range_valid_when_end_after_start(self):
        """validate_date_range valide si date fin après date début."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        is_valid, errors = ValidationService.validate_date_range(start, end)

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_date_range_valid_when_no_end_date(self):
        """validate_date_range valide sans date de fin."""
        start = date(2024, 1, 1)

        is_valid, errors = ValidationService.validate_date_range(start, None)

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_date_range_invalid_when_end_before_start(self):
        """validate_date_range invalide si date fin avant date début."""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)

        is_valid, errors = ValidationService.validate_date_range(start, end)

        self.assertFalse(is_valid)
        self.assertIn('date_fin', errors)

    def test_validate_date_range_invalid_when_same_dates(self):
        """validate_date_range invalide si dates identiques."""
        same_date = date(2024, 6, 15)

        is_valid, errors = ValidationService.validate_date_range(same_date, same_date)

        self.assertFalse(is_valid)
        self.assertIn('date_fin', errors)

    def test_validate_date_range_invalid_without_start_date(self):
        """validate_date_range invalide sans date de début."""
        is_valid, errors = ValidationService.validate_date_range(None, date(2024, 12, 31))

        self.assertFalse(is_valid)
        self.assertIn('date_debut', errors)

    def test_validate_date_range_uses_custom_field_names(self):
        """validate_date_range utilise les noms de champs personnalisés."""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)

        is_valid, errors = ValidationService.validate_date_range(
            start, end,
            field_names=('debut', 'fin')
        )

        self.assertFalse(is_valid)
        self.assertIn('fin', errors)

    # ===== Tests parse_date_from_string =====

    def test_parse_date_from_string_parses_iso_format(self):
        """parse_date_from_string parse le format ISO."""
        parsed, errors = ValidationService.parse_date_from_string('2024-06-15')

        self.assertEqual(parsed, date(2024, 6, 15))
        self.assertEqual(errors, {})

    def test_parse_date_from_string_parses_french_format(self):
        """parse_date_from_string parse le format français."""
        parsed, errors = ValidationService.parse_date_from_string('15/06/2024')

        self.assertEqual(parsed, date(2024, 6, 15))
        self.assertEqual(errors, {})

    def test_parse_date_from_string_returns_none_for_empty_when_not_required(self):
        """parse_date_from_string retourne None pour chaîne vide si non requis."""
        parsed, errors = ValidationService.parse_date_from_string('', required=False)

        self.assertIsNone(parsed)
        self.assertEqual(errors, {})

    def test_parse_date_from_string_returns_error_for_empty_when_required(self):
        """parse_date_from_string retourne erreur pour chaîne vide si requis."""
        parsed, errors = ValidationService.parse_date_from_string('', 'date_test', required=True)

        self.assertIsNone(parsed)
        self.assertIn('date_test', errors)

    def test_parse_date_from_string_returns_error_for_invalid_format(self):
        """parse_date_from_string retourne erreur pour format invalide."""
        parsed, errors = ValidationService.parse_date_from_string('invalid-date', 'date_test')

        self.assertIsNone(parsed)
        self.assertIn('date_test', errors)

    # ===== Tests check_overlap (logique manuelle) =====

    def test_check_overlap_logic_no_overlap_before(self):
        """Logique de chevauchement - pas de chevauchement (avant)."""
        existing_start = date(2024, 6, 1)
        existing_end = date(2024, 6, 30)
        new_start = date(2024, 1, 1)
        new_end = date(2024, 5, 31)

        has_overlap = not (new_end < existing_start or new_start > existing_end)

        self.assertFalse(has_overlap)

    def test_check_overlap_logic_no_overlap_after(self):
        """Logique de chevauchement - pas de chevauchement (après)."""
        existing_start = date(2024, 1, 1)
        existing_end = date(2024, 3, 31)
        new_start = date(2024, 6, 1)
        new_end = date(2024, 12, 31)

        has_overlap = not (new_end < existing_start or new_start > existing_end)

        self.assertFalse(has_overlap)

    def test_check_overlap_logic_detects_overlap_inside(self):
        """Logique de chevauchement - détecte inclusion."""
        existing_start = date(2024, 1, 1)
        existing_end = date(2024, 12, 31)
        new_start = date(2024, 6, 1)
        new_end = date(2024, 6, 30)

        has_overlap = not (new_end < existing_start or new_start > existing_end)

        self.assertTrue(has_overlap)

    def test_check_overlap_logic_detects_partial_overlap(self):
        """Logique de chevauchement - détecte chevauchement partiel."""
        existing_start = date(2024, 1, 1)
        existing_end = date(2024, 6, 30)
        new_start = date(2024, 6, 1)
        new_end = date(2024, 12, 31)

        has_overlap = not (new_end < existing_start or new_start > existing_end)

        self.assertTrue(has_overlap)

    # ===== Tests validate_required_fields =====

    def test_validate_required_fields_valid_when_all_present(self):
        """validate_required_fields valide si tous les champs présents."""
        data = {'nom': 'Test', 'prenom': 'User', 'email': 'test@test.com'}

        errors = ValidationService.validate_required_fields(
            data, ['nom', 'prenom', 'email']
        )

        self.assertEqual(errors, {})

    def test_validate_required_fields_invalid_when_missing(self):
        """validate_required_fields invalide si champs manquants."""
        data = {'nom': 'Test'}

        errors = ValidationService.validate_required_fields(
            data, ['nom', 'prenom', 'email']
        )

        self.assertIn('prenom', errors)
        self.assertIn('email', errors)

    def test_validate_required_fields_invalid_for_empty_values(self):
        """validate_required_fields invalide pour valeurs vides."""
        data = {'nom': 'Test', 'prenom': '', 'email': None}

        errors = ValidationService.validate_required_fields(
            data, ['nom', 'prenom', 'email']
        )

        self.assertIn('prenom', errors)
        self.assertIn('email', errors)

    def test_validate_required_fields_invalid_for_only_whitespace(self):
        """validate_required_fields invalide pour whitespace seul."""
        data = {'nom': '   '}

        errors = ValidationService.validate_required_fields(data, ['nom'])

        self.assertIn('nom', errors)

    # ===== Tests validate_email =====

    def test_validate_email_valid(self):
        """validate_email valide un email correct."""
        is_valid, errors = ValidationService.validate_email('test@example.com')

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_email_invalid(self):
        """validate_email invalide un email incorrect."""
        is_valid, errors = ValidationService.validate_email('invalid-email')

        self.assertFalse(is_valid)
        self.assertIn('email', errors)

    def test_validate_email_empty_when_not_required(self):
        """validate_email accepte vide si non requis."""
        is_valid, errors = ValidationService.validate_email('', required=False)

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    # ===== Tests validate_phone_number =====

    def test_validate_phone_number_valid(self):
        """validate_phone_number valide un numéro correct."""
        is_valid, errors = ValidationService.validate_phone_number('+33612345678')

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_phone_number_valid_with_spaces(self):
        """validate_phone_number valide un numéro avec espaces."""
        is_valid, errors = ValidationService.validate_phone_number('06 12 34 56 78')

        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_phone_number_invalid_too_short(self):
        """validate_phone_number invalide un numéro trop court."""
        is_valid, errors = ValidationService.validate_phone_number('123')

        self.assertFalse(is_valid)
        self.assertIn('telephone', errors)

    # ===== Tests normalize_string =====

    def test_normalize_string_strips_whitespace(self):
        """normalize_string retire les espaces."""
        result = ValidationService.normalize_string('  test  ')

        self.assertEqual(result, 'test')

    def test_normalize_string_handles_none(self):
        """normalize_string gère None."""
        result = ValidationService.normalize_string(None)

        self.assertEqual(result, '')

    # ===== Tests capitalize_name =====

    def test_capitalize_name_uppercase(self):
        """capitalize_name met en majuscules."""
        result = ValidationService.capitalize_name('dupont')

        self.assertEqual(result, 'DUPONT')

    def test_capitalize_name_handles_none(self):
        """capitalize_name gère None."""
        result = ValidationService.capitalize_name(None)

        self.assertEqual(result, '')

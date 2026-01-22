# employee/tests/test_services/test_embauche_service.py
"""
Tests pour EmbaucheService.
"""
from datetime import date

from django.contrib.auth.models import User

from employee.tests.base import EmployeeTestCase
from employee.services.embauche_service import EmbaucheService
from employee.models import ZY00


class EmbaucheServiceTestCase(EmployeeTestCase):
    """Tests pour EmbaucheService."""

    def setUp(self):
        """Créer les données spécifiques à chaque test."""
        self.pre_employee = self.create_employee(
            matricule='PRE001',
            nom='Candidat',
            prenoms='Test',
            type_dossier='PRE',
            etat='actif'
        )

    # ===== Tests validate_embauche =====

    def test_validate_embauche_changes_type_dossier(self):
        """validate_embauche change type_dossier de PRE à SAL."""
        success, message = EmbaucheService.validate_embauche(self.pre_employee)

        self.assertTrue(success)
        self.pre_employee.refresh_from_db()
        self.assertEqual(self.pre_employee.type_dossier, 'SAL')

    def test_validate_embauche_sets_validation_date(self):
        """validate_embauche définit la date de validation."""
        EmbaucheService.validate_embauche(self.pre_employee)

        self.pre_employee.refresh_from_db()
        self.assertEqual(
            self.pre_employee.date_validation_embauche,
            date.today()
        )

    def test_validate_embauche_returns_false_for_already_sal(self):
        """validate_embauche retourne False pour un salarié."""
        sal_employee = self.create_employee(
            matricule='SAL001',
            type_dossier='SAL'
        )

        success, message = EmbaucheService.validate_embauche(sal_employee)

        self.assertFalse(success)
        self.assertIn("pas en pré-embauche", message)

    def test_validate_embauche_returns_success_message(self):
        """validate_embauche retourne un message de succès."""
        success, message = EmbaucheService.validate_embauche(self.pre_employee)

        self.assertTrue(success)
        self.assertIn("validée avec succès", message)

    # ===== Tests create_user_account =====

    def test_create_user_account_creates_user(self):
        """create_user_account crée un compte utilisateur."""
        username, password = EmbaucheService.create_user_account(self.pre_employee)

        self.assertIsNotNone(username)
        self.assertIsNotNone(password)
        self.assertTrue(User.objects.filter(username=username).exists())

    def test_create_user_account_links_to_employee(self):
        """create_user_account lie le user à l'employé."""
        EmbaucheService.create_user_account(self.pre_employee)

        self.pre_employee.refresh_from_db()
        self.assertIsNotNone(self.pre_employee.user)

    def test_create_user_account_returns_username_password(self):
        """create_user_account retourne un tuple (username, password)."""
        result = EmbaucheService.create_user_account(self.pre_employee)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        username, password = result
        self.assertIsInstance(username, str)
        self.assertIsInstance(password, str)

    def test_create_user_account_uses_default_password(self):
        """create_user_account utilise le mot de passe par défaut."""
        username, password = EmbaucheService.create_user_account(self.pre_employee)

        self.assertEqual(password, EmbaucheService.DEFAULT_PASSWORD)

    def test_create_user_account_uses_custom_password(self):
        """create_user_account accepte un mot de passe personnalisé."""
        custom_password = "CustomPass123!"
        username, password = EmbaucheService.create_user_account(
            self.pre_employee, password=custom_password
        )

        self.assertEqual(password, custom_password)

    def test_create_user_account_generates_username_from_name(self):
        """create_user_account génère le username à partir du nom et prénom."""
        username, _ = EmbaucheService.create_user_account(self.pre_employee)

        # Le format attendu est nom.prenom (en minuscules)
        expected_start = "candidat.test"
        self.assertTrue(username.startswith(expected_start))

    # ===== Tests can_validate_embauche =====

    def test_can_validate_embauche_true_with_contract_and_affectation(self):
        """can_validate_embauche retourne True avec contrat et affectation."""
        self.create_contract(self.pre_employee, actif=True)
        self.create_affectation(self.pre_employee, self.poste)

        can_validate, reason = EmbaucheService.can_validate_embauche(self.pre_employee)

        self.assertTrue(can_validate)

    def test_can_validate_embauche_false_for_sal(self):
        """can_validate_embauche retourne False pour SAL."""
        sal = self.create_employee(matricule='SAL001', type_dossier='SAL')

        can_validate, reason = EmbaucheService.can_validate_embauche(sal)

        self.assertFalse(can_validate)
        self.assertIn("pas en pré-embauche", reason)

    def test_can_validate_embauche_false_without_contract(self):
        """can_validate_embauche retourne False sans contrat actif."""
        self.create_affectation(self.pre_employee, self.poste)
        # Pas de contrat

        can_validate, reason = EmbaucheService.can_validate_embauche(self.pre_employee)

        self.assertFalse(can_validate)
        self.assertIn("contrat", reason)

    def test_can_validate_embauche_false_without_affectation(self):
        """can_validate_embauche retourne False sans affectation active."""
        self.create_contract(self.pre_employee, actif=True)
        # Pas d'affectation

        can_validate, reason = EmbaucheService.can_validate_embauche(self.pre_employee)

        self.assertFalse(can_validate)
        self.assertIn("affectation", reason)

    # ===== Tests get_pre_embauches_pending =====

    def test_get_pre_embauches_pending_returns_pre_employees(self):
        """get_pre_embauches_pending retourne les pré-embauches en attente."""
        # Créer plusieurs pré-embauches
        pre2 = self.create_employee(
            matricule='PRE002',
            type_dossier='PRE',
            etat='actif'
        )

        result = EmbaucheService.get_pre_embauches_pending()

        self.assertIn(self.pre_employee, result)
        self.assertIn(pre2, result)

    def test_get_pre_embauches_pending_excludes_sal(self):
        """get_pre_embauches_pending exclut les salariés."""
        sal = self.create_employee(
            matricule='SAL001',
            type_dossier='SAL',
            etat='actif'
        )

        result = EmbaucheService.get_pre_embauches_pending()

        self.assertNotIn(sal, result)

    def test_get_pre_embauches_pending_excludes_inactive(self):
        """get_pre_embauches_pending exclut les inactifs."""
        inactive_pre = self.create_employee(
            matricule='PRE003',
            type_dossier='PRE',
            etat='inactif'
        )

        result = EmbaucheService.get_pre_embauches_pending()

        self.assertNotIn(inactive_pre, result)

    # ===== Tests cancel_embauche =====

    def test_cancel_embauche_deletes_employee(self):
        """cancel_embauche supprime l'employé."""
        matricule = self.pre_employee.matricule

        success, message = EmbaucheService.cancel_embauche(self.pre_employee)

        self.assertTrue(success)
        self.assertFalse(ZY00.objects.filter(matricule=matricule).exists())

    def test_cancel_embauche_returns_false_for_sal(self):
        """cancel_embauche retourne False pour un salarié."""
        sal = self.create_employee(matricule='SAL001', type_dossier='SAL')

        success, message = EmbaucheService.cancel_embauche(sal)

        self.assertFalse(success)
        self.assertTrue(ZY00.objects.filter(matricule='SAL001').exists())

    def test_cancel_embauche_deletes_user(self):
        """cancel_embauche supprime le compte utilisateur."""
        user = self.create_user_for_employee(self.pre_employee)
        user_id = user.id

        EmbaucheService.cancel_embauche(self.pre_employee)

        self.assertFalse(User.objects.filter(id=user_id).exists())

    # ===== Tests get_embauche_stats =====

    def test_get_embauche_stats_returns_dict(self):
        """get_embauche_stats retourne un dictionnaire avec les statistiques."""
        result = EmbaucheService.get_embauche_stats()

        self.assertIsInstance(result, dict)
        self.assertIn('pre_embauches', result)
        self.assertIn('salaries_actifs', result)
        self.assertIn('salaries_inactifs', result)
        self.assertIn('total', result)

    def test_get_embauche_stats_counts_correctly(self):
        """get_embauche_stats compte correctement les différents types."""
        # On a déjà self.pre_employee (PRE, actif)
        self.create_employee(matricule='SAL001', type_dossier='SAL', etat='actif')
        self.create_employee(matricule='SAL002', type_dossier='SAL', etat='inactif')

        result = EmbaucheService.get_embauche_stats()

        self.assertGreaterEqual(result['pre_embauches'], 1)
        self.assertGreaterEqual(result['salaries_actifs'], 1)
        self.assertGreaterEqual(result['salaries_inactifs'], 1)

    # ===== Tests reset_user_password =====

    def test_reset_user_password_changes_password(self):
        """reset_user_password change le mot de passe."""
        self.create_user_for_employee(self.pre_employee)

        success, new_password = EmbaucheService.reset_user_password(self.pre_employee)

        self.assertTrue(success)
        self.assertEqual(new_password, EmbaucheService.DEFAULT_PASSWORD)

    def test_reset_user_password_uses_custom_password(self):
        """reset_user_password accepte un mot de passe personnalisé."""
        self.create_user_for_employee(self.pre_employee)
        custom_pass = "NewPass123!"

        success, new_password = EmbaucheService.reset_user_password(
            self.pre_employee, new_password=custom_pass
        )

        self.assertTrue(success)
        self.assertEqual(new_password, custom_pass)

    def test_reset_user_password_returns_false_without_user(self):
        """reset_user_password retourne False sans compte utilisateur."""
        # self.pre_employee n'a pas de user

        success, new_password = EmbaucheService.reset_user_password(self.pre_employee)

        self.assertFalse(success)
        self.assertEqual(new_password, "")

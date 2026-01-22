# employee/tests/test_services/test_status_service.py
"""
Tests pour StatusService.
"""
from datetime import date, timedelta

from employee.tests.base import EmployeeTestCase
from employee.services.status_service import StatusService


class StatusServiceTestCase(EmployeeTestCase):
    """Tests pour StatusService."""

    def setUp(self):
        """Créer les données spécifiques à chaque test."""
        self.employee = self.create_employee(matricule='EMP001', etat='actif')
        self.inactive_employee = self.create_employee(
            matricule='EMP002', etat='inactif'
        )

    # ===== Tests is_active =====

    def test_is_active_returns_true_with_active_contract(self):
        """is_active retourne True si l'employé a un contrat actif."""
        # is_active vérifie les contrats, pas le champ etat
        self.create_contract(self.employee, actif=True)

        result = StatusService.is_active(self.employee)

        self.assertTrue(result)

    def test_is_active_returns_false_without_contract(self):
        """is_active retourne False sans contrat actif."""
        # Même si etat='actif', sans contrat, is_active retourne False
        result = StatusService.is_active(self.employee)

        self.assertFalse(result)

    def test_is_active_returns_false_with_expired_contract(self):
        """is_active retourne False avec un contrat expiré."""
        self.create_contract(
            self.employee,
            date_fin=date.today() - timedelta(days=1),
            actif=True
        )

        result = StatusService.is_active(self.employee)

        self.assertFalse(result)

    def test_is_active_returns_false_with_inactive_contract(self):
        """is_active retourne False avec un contrat inactif."""
        self.create_contract(self.employee, actif=False)

        result = StatusService.is_active(self.employee)

        self.assertFalse(result)

    # ===== Tests get_current_contract =====

    def test_get_current_contract_returns_active_contract(self):
        """get_current_contract retourne le contrat actif."""
        contract = self.create_contract(self.employee, actif=True)

        result = StatusService.get_current_contract(self.employee)

        self.assertEqual(result, contract)

    def test_get_current_contract_returns_none_without_contract(self):
        """get_current_contract retourne None sans contrat."""
        result = StatusService.get_current_contract(self.employee)

        self.assertIsNone(result)

    def test_get_current_contract_returns_none_for_expired_contract(self):
        """get_current_contract retourne None pour contrat expiré."""
        self.create_contract(
            self.employee,
            date_fin=date.today() - timedelta(days=1),
            actif=True
        )

        result = StatusService.get_current_contract(self.employee)

        self.assertIsNone(result)

    def test_get_current_contract_returns_none_for_inactive_contract(self):
        """get_current_contract retourne None pour contrat inactif."""
        self.create_contract(self.employee, actif=False)

        result = StatusService.get_current_contract(self.employee)

        self.assertIsNone(result)

    # ===== Tests calculate_seniority_years =====

    def test_calculate_seniority_years_returns_correct_years(self):
        """calculate_seniority_years retourne le bon nombre d'années."""
        self.employee.date_entree_entreprise = date.today() - timedelta(days=365*3)
        self.employee.save()

        result = StatusService.calculate_seniority_years(self.employee)

        self.assertEqual(result, 3)

    def test_calculate_seniority_years_returns_zero_without_date(self):
        """calculate_seniority_years retourne 0 sans date d'entrée."""
        self.employee.date_entree_entreprise = None
        self.employee.save()

        result = StatusService.calculate_seniority_years(self.employee)

        self.assertEqual(result, 0)

    def test_calculate_seniority_years_returns_zero_for_new_employee(self):
        """calculate_seniority_years retourne 0 pour nouvel employé."""
        self.employee.date_entree_entreprise = date.today()
        self.employee.save()

        result = StatusService.calculate_seniority_years(self.employee)

        self.assertEqual(result, 0)

    # ===== Tests synchronize_status =====

    def test_synchronize_status_activates_with_valid_contract(self):
        """synchronize_status active l'employé avec contrat valide."""
        self.employee.etat = 'inactif'
        self.employee.save()
        self.create_contract(self.employee, actif=True)

        StatusService.synchronize_status(self.employee)

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.etat, 'actif')

    def test_synchronize_status_deactivates_without_contract(self):
        """synchronize_status désactive l'employé sans contrat valide."""
        self.employee.etat = 'actif'
        self.employee.type_dossier = 'SAL'
        self.employee.save()
        # Pas de contrat

        StatusService.synchronize_status(self.employee)

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.etat, 'inactif')

    def test_synchronize_status_keeps_pre_embauche_active(self):
        """synchronize_status garde les pré-embauches actifs même sans contrat."""
        pre_employee = self.create_employee(
            matricule='PRE001',
            type_dossier='PRE',
            etat='actif'
        )
        # Pas de contrat mais PRE

        StatusService.synchronize_status(pre_employee)

        pre_employee.refresh_from_db()
        self.assertEqual(pre_employee.etat, 'actif')

    def test_synchronize_status_returns_true_when_changed(self):
        """synchronize_status retourne True si le statut a changé."""
        self.employee.etat = 'actif'
        self.employee.type_dossier = 'SAL'
        self.employee.save()
        # Pas de contrat -> sera désactivé

        result = StatusService.synchronize_status(self.employee)

        self.assertTrue(result)

    def test_synchronize_status_returns_false_when_unchanged(self):
        """synchronize_status retourne False si le statut n'a pas changé."""
        self.employee.etat = 'actif'
        self.employee.save()
        self.create_contract(self.employee, actif=True)

        result = StatusService.synchronize_status(self.employee)

        self.assertFalse(result)

    # ===== Tests deactivate_associated_data =====

    def test_deactivate_associated_data_deactivates_contracts(self):
        """deactivate_associated_data désactive les contrats si employé inactif."""
        # L'employé DOIT être inactif pour que la méthode fonctionne
        self.inactive_employee.etat = 'inactif'
        self.inactive_employee.save()
        contract = self.create_contract(self.inactive_employee, actif=True)

        StatusService.deactivate_associated_data(self.inactive_employee)

        contract.refresh_from_db()
        self.assertFalse(contract.actif)

    def test_deactivate_associated_data_does_nothing_if_active(self):
        """deactivate_associated_data ne fait rien si employé actif."""
        # L'employé est actif, donc la méthode ne fait rien
        self.employee.etat = 'actif'
        self.employee.save()
        contract = self.create_contract(self.employee, actif=True)

        StatusService.deactivate_associated_data(self.employee)

        contract.refresh_from_db()
        # Le contrat reste actif car l'employé est actif
        self.assertTrue(contract.actif)

    # ===== Tests is_pre_hire / is_employee =====

    def test_is_pre_hire_returns_true_for_pre(self):
        """is_pre_hire retourne True pour type_dossier PRE."""
        pre = self.create_employee(matricule='PRE001', type_dossier='PRE')

        result = StatusService.is_pre_hire(pre)

        self.assertTrue(result)

    def test_is_pre_hire_returns_false_for_sal(self):
        """is_pre_hire retourne False pour type_dossier SAL."""
        result = StatusService.is_pre_hire(self.employee)

        self.assertFalse(result)

    def test_is_employee_returns_true_for_sal(self):
        """is_employee retourne True pour type_dossier SAL."""
        result = StatusService.is_employee(self.employee)

        self.assertTrue(result)

    def test_is_employee_returns_false_for_pre(self):
        """is_employee retourne False pour type_dossier PRE."""
        pre = self.create_employee(matricule='PRE001', type_dossier='PRE')

        result = StatusService.is_employee(pre)

        self.assertFalse(result)

    # ===== Tests has_active_contract =====

    def test_has_active_contract_returns_true_with_contract(self):
        """has_active_contract retourne True avec un contrat actif."""
        self.create_contract(self.employee, actif=True)

        result = StatusService.has_active_contract(self.employee)

        self.assertTrue(result)

    def test_has_active_contract_returns_false_without_contract(self):
        """has_active_contract retourne False sans contrat."""
        result = StatusService.has_active_contract(self.employee)

        self.assertFalse(result)

    # ===== Tests get_contract_type =====

    def test_get_contract_type_returns_type(self):
        """get_contract_type retourne le type de contrat."""
        self.create_contract(self.employee, type_contrat='CDI', actif=True)

        result = StatusService.get_contract_type(self.employee)

        self.assertEqual(result, 'CDI')

    def test_get_contract_type_returns_none_without_contract(self):
        """get_contract_type retourne None sans contrat."""
        result = StatusService.get_contract_type(self.employee)

        self.assertIsNone(result)

# employee/tests/test_services/test_permission_service.py
"""
Tests pour PermissionService.
"""
from datetime import date, timedelta

from django.core.exceptions import ObjectDoesNotExist

from employee.tests.base import EmployeeTestCase
from employee.services.permission_service import PermissionService
from employee.models import ZYRE, ZYRO


class PermissionServiceTestCase(EmployeeTestCase):
    """Tests pour PermissionService."""

    def setUp(self):
        """Créer les données spécifiques à chaque test."""
        self.employee = self.create_employee(matricule='EMP001')
        self.drh_employee = self.create_employee(matricule='DRH001')
        self.manager_employee = self.create_employee(matricule='MGR001')

    # ===== Tests has_role =====

    def test_has_role_returns_true_when_role_assigned(self):
        """has_role retourne True si le rôle est attribué et actif."""
        self.assign_role(self.drh_employee, self.role_drh)

        result = PermissionService.has_role(self.drh_employee, 'DRH')

        self.assertTrue(result)

    def test_has_role_returns_false_when_role_not_assigned(self):
        """has_role retourne False si le rôle n'est pas attribué."""
        result = PermissionService.has_role(self.employee, 'DRH')

        self.assertFalse(result)

    def test_has_role_returns_false_when_role_inactive(self):
        """has_role retourne False si l'attribution est inactive."""
        self.assign_role(self.drh_employee, self.role_drh, actif=False)

        result = PermissionService.has_role(self.drh_employee, 'DRH')

        self.assertFalse(result)

    def test_has_role_returns_false_when_role_has_end_date(self):
        """has_role retourne False si l'attribution a une date de fin."""
        attribution = self.assign_role(self.drh_employee, self.role_drh)
        attribution.date_fin = date.today() - timedelta(days=1)
        attribution.save()

        result = PermissionService.has_role(self.drh_employee, 'DRH')

        self.assertFalse(result)

    # ===== Tests get_roles =====

    def test_get_roles_returns_empty_queryset_when_no_roles(self):
        """get_roles retourne un queryset vide sans rôles."""
        result = PermissionService.get_roles(self.employee)

        self.assertEqual(result.count(), 0)

    def test_get_roles_returns_active_attributions_only(self):
        """get_roles retourne uniquement les attributions actives."""
        self.assign_role(self.employee, self.role_drh, actif=True)
        self.assign_role(self.employee, self.role_manager, actif=False)

        result = PermissionService.get_roles(self.employee)
        # get_roles retourne des ZYRE (attributions), pas des ZYRO
        codes = [attr.role.CODE for attr in result]

        self.assertEqual(codes, ['DRH'])

    def test_get_roles_returns_multiple_active_attributions(self):
        """get_roles retourne toutes les attributions actives."""
        self.assign_role(self.employee, self.role_drh)
        self.assign_role(self.employee, self.role_manager)

        result = PermissionService.get_roles(self.employee)
        codes = sorted([attr.role.CODE for attr in result])

        self.assertEqual(codes, ['DRH', 'MANAGER'])

    # ===== Tests get_role_codes =====

    def test_get_role_codes_returns_list_of_codes(self):
        """get_role_codes retourne une liste de codes."""
        self.assign_role(self.employee, self.role_drh)
        self.assign_role(self.employee, self.role_manager)

        result = PermissionService.get_role_codes(self.employee)

        self.assertIsInstance(result, list)
        self.assertIn('DRH', result)
        self.assertIn('MANAGER', result)

    # ===== Tests add_role =====

    def test_add_role_creates_new_attribution(self):
        """add_role crée une nouvelle attribution."""
        result = PermissionService.add_role(
            self.employee, 'DRH', created_by=self.drh_employee
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.role.CODE, 'DRH')
        self.assertTrue(result.actif)
        self.assertEqual(result.created_by, self.drh_employee)

    def test_add_role_raises_exception_for_invalid_role(self):
        """add_role lève une exception pour un code de rôle invalide."""
        with self.assertRaises(ZYRO.DoesNotExist):
            PermissionService.add_role(self.employee, 'INVALID_ROLE')

    def test_add_role_with_custom_date(self):
        """add_role accepte une date de début personnalisée."""
        custom_date = date(2024, 1, 1)

        result = PermissionService.add_role(
            self.employee, 'DRH', date_debut=custom_date
        )

        self.assertEqual(result.date_debut, custom_date)

    # ===== Tests remove_role =====

    def test_remove_role_deactivates_attribution(self):
        """remove_role désactive l'attribution et retourne le nombre modifié."""
        attribution = self.assign_role(self.employee, self.role_drh)

        result = PermissionService.remove_role(self.employee, 'DRH')

        # remove_role retourne un int (nombre de lignes modifiées)
        self.assertEqual(result, 1)
        attribution.refresh_from_db()
        self.assertFalse(attribution.actif)
        self.assertIsNotNone(attribution.date_fin)

    def test_remove_role_returns_zero_when_not_found(self):
        """remove_role retourne 0 si le rôle n'est pas attribué."""
        result = PermissionService.remove_role(self.employee, 'DRH')

        self.assertEqual(result, 0)

    # ===== Tests is_drh / is_assistant_rh =====

    def test_is_drh_returns_true_for_drh(self):
        """is_drh retourne True pour un DRH."""
        self.assign_role(self.drh_employee, self.role_drh)

        result = PermissionService.is_drh(self.drh_employee)

        self.assertTrue(result)

    def test_is_drh_returns_false_for_non_drh(self):
        """is_drh retourne False pour un non-DRH."""
        result = PermissionService.is_drh(self.employee)

        self.assertFalse(result)

    def test_is_assistant_rh_returns_true(self):
        """is_assistant_rh retourne True pour un Assistant RH."""
        self.assign_role(self.employee, self.role_assistant_rh)

        result = PermissionService.is_assistant_rh(self.employee)

        self.assertTrue(result)

    # ===== Tests can_hire =====

    def test_can_hire_returns_true_for_drh(self):
        """can_hire retourne True pour un DRH."""
        self.assign_role(self.drh_employee, self.role_drh)

        result = PermissionService.can_hire(self.drh_employee)

        self.assertTrue(result)

    def test_can_hire_returns_false_for_assistant_rh(self):
        """can_hire retourne False pour un Assistant RH (seul DRH/GESTION_APP)."""
        self.assign_role(self.employee, self.role_assistant_rh)

        # Note: can_hire vérifie DRH ou GESTION_APP, pas ASSISTANT_RH
        result = PermissionService.can_hire(self.employee)

        self.assertFalse(result)

    def test_can_hire_returns_false_for_regular_employee(self):
        """can_hire retourne False pour un employé standard."""
        result = PermissionService.can_hire(self.employee)

        self.assertFalse(result)

    # ===== Tests can_manage_employees =====

    def test_can_manage_employees_returns_true_for_drh(self):
        """can_manage_employees retourne True pour un DRH."""
        self.assign_role(self.drh_employee, self.role_drh)

        result = PermissionService.can_manage_employees(self.drh_employee)

        self.assertTrue(result)

    def test_can_manage_employees_returns_true_for_assistant_rh(self):
        """can_manage_employees retourne True pour un Assistant RH."""
        self.assign_role(self.employee, self.role_assistant_rh)

        result = PermissionService.can_manage_employees(self.employee)

        self.assertTrue(result)

    def test_can_manage_employees_returns_false_for_regular_employee(self):
        """can_manage_employees retourne False pour un employé standard."""
        result = PermissionService.can_manage_employees(self.employee)

        self.assertFalse(result)

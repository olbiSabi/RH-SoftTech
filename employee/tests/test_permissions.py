"""
Tests pour le système de permissions et rôles (PermissionService).

Tests complets du PermissionService qui gère l'attribution et la vérification
des rôles et permissions des employés.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from employee.models import ZY00, ZYRO, ZYRE
from employee.services.permission_service import PermissionService
from entreprise.models import Entreprise


class BasePermissionTestCase(TestCase):
    """Classe de base pour les tests de permissions avec fixtures communes."""

    def setUp(self):
        """Prépare les données communes."""
        # Créer une entreprise
        self.entreprise = Entreprise.objects.create(
            code='ENT001',
            nom='Entreprise Test',
            raison_sociale='Entreprise Test SARL',
            numero_impot='123456789',
            rccm='RCCM123',
            adresse='123 Rue Test',
            ville='Lomé',
            pays='Togo'
        )

        # Créer des employés
        self.employe = ZY00.objects.create(
            nom='Dupont',
            prenoms='Jean',
            date_naissance=date(1990, 1, 1),
            sexe='M',
            type_id='CNI',
            numero_id='CNI001',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise
        )

        self.admin = ZY00.objects.create(
            nom='Admin',
            prenoms='System',
            date_naissance=date(1985, 1, 1),
            sexe='M',
            type_id='CNI',
            numero_id='CNI002',
            date_validite_id=date(2020, 1, 1),
            date_expiration_id=date(2030, 1, 1),
            entreprise=self.entreprise
        )

        # Créer des rôles
        self.role_drh = ZYRO.objects.create(
            CODE='DRH',
            LIBELLE='Directeur RH',
            DESCRIPTION='Directeur des ressources humaines',
            PERMISSIONS_CUSTOM={
                'can_validate_all': True,
                'can_manage_employees': True
            },
            actif=True
        )

        self.role_manager = ZYRO.objects.create(
            CODE='MANAGER',
            LIBELLE='Manager',
            DESCRIPTION='Manager d\'équipe',
            PERMISSIONS_CUSTOM={
                'can_validate_team': True
            },
            actif=True
        )

        self.role_comptable = ZYRO.objects.create(
            CODE='COMPTABLE',
            LIBELLE='Comptable',
            DESCRIPTION='Comptable',
            PERMISSIONS_CUSTOM={
                'can_view_finances': True,
                'can_export_data': True
            },
            actif=True
        )


class PermissionServiceHasRoleTest(BasePermissionTestCase):
    """Tests pour has_role()."""

    def test_has_role_with_active_role(self):
        """Test qu'un employé avec un rôle actif retourne True."""
        # Attribuer le rôle
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        # Vérifier
        self.assertTrue(PermissionService.has_role(self.employe, 'DRH'))

    def test_has_role_without_role(self):
        """Test qu'un employé sans rôle retourne False."""
        self.assertFalse(PermissionService.has_role(self.employe, 'DRH'))

    def test_has_role_with_inactive_role(self):
        """Test qu'un rôle inactif retourne False."""
        # Attribuer le rôle mais inactif
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=False  # Inactif
        )

        self.assertFalse(PermissionService.has_role(self.employe, 'DRH'))

    def test_has_role_with_end_date(self):
        """Test qu'un rôle avec date de fin retourne False."""
        # Attribuer le rôle avec date de fin
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today() - timedelta(days=100),
            date_fin=date.today() - timedelta(days=1),  # Terminé
            actif=True
        )

        self.assertFalse(PermissionService.has_role(self.employe, 'DRH'))

    def test_has_role_multiple_roles(self):
        """Test qu'un employé avec plusieurs rôles peut tous les avoir."""
        # Attribuer plusieurs rôles
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_manager,
            date_debut=date.today(),
            actif=True
        )

        # Vérifier les deux
        self.assertTrue(PermissionService.has_role(self.employe, 'DRH'))
        self.assertTrue(PermissionService.has_role(self.employe, 'MANAGER'))
        self.assertFalse(PermissionService.has_role(self.employe, 'COMPTABLE'))


class PermissionServiceGetRolesTest(BasePermissionTestCase):
    """Tests pour get_roles()."""

    def test_get_roles_returns_queryset(self):
        """Test que get_roles() retourne un QuerySet."""
        roles = PermissionService.get_roles(self.employe)

        from django.db.models import QuerySet
        self.assertIsInstance(roles, QuerySet)

    def test_get_roles_empty_for_new_employee(self):
        """Test qu'un nouvel employé n'a pas de rôles."""
        roles = PermissionService.get_roles(self.employe)

        self.assertEqual(roles.count(), 0)

    def test_get_roles_returns_active_roles_only(self):
        """Test que seuls les rôles actifs sont retournés."""
        # Rôle actif
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        # Rôle inactif
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_manager,
            date_debut=date.today(),
            actif=False
        )

        roles = PermissionService.get_roles(self.employe)

        self.assertEqual(roles.count(), 1)
        self.assertEqual(roles.first().role.CODE, 'DRH')

    def test_get_roles_excludes_ended_roles(self):
        """Test que les rôles terminés sont exclus."""
        # Rôle actif
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        # Rôle avec date_fin (terminé)
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_manager,
            date_debut=date.today() - timedelta(days=100),
            date_fin=date.today() - timedelta(days=1),
            actif=True
        )

        roles = PermissionService.get_roles(self.employe)

        self.assertEqual(roles.count(), 1)
        self.assertEqual(roles.first().role.CODE, 'DRH')


class PermissionServiceGetRoleCodesTest(BasePermissionTestCase):
    """Tests pour get_role_codes()."""

    def test_get_role_codes_returns_list(self):
        """Test que get_role_codes() retourne une liste."""
        codes = PermissionService.get_role_codes(self.employe)

        self.assertIsInstance(codes, list)

    def test_get_role_codes_empty_list(self):
        """Test qu'un employé sans rôle retourne une liste vide."""
        codes = PermissionService.get_role_codes(self.employe)

        self.assertEqual(len(codes), 0)

    def test_get_role_codes_returns_correct_codes(self):
        """Test que les bons codes sont retournés."""
        # Attribuer des rôles
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_comptable,
            date_debut=date.today(),
            actif=True
        )

        codes = PermissionService.get_role_codes(self.employe)

        self.assertEqual(len(codes), 2)
        self.assertIn('DRH', codes)
        self.assertIn('COMPTABLE', codes)


class PermissionServiceAddRoleTest(BasePermissionTestCase):
    """Tests pour add_role()."""

    def test_add_role_creates_attribution(self):
        """Test l'ajout d'un rôle crée une attribution."""
        attribution = PermissionService.add_role(
            self.employe,
            'DRH',
            created_by=self.admin
        )

        self.assertIsNotNone(attribution)
        self.assertEqual(attribution.employe, self.employe)
        self.assertEqual(attribution.role.CODE, 'DRH')
        self.assertTrue(attribution.actif)
        self.assertEqual(attribution.created_by, self.admin)

    def test_add_role_with_custom_date(self):
        """Test l'ajout d'un rôle avec une date de début spécifique."""
        date_debut = date.today() - timedelta(days=30)

        attribution = PermissionService.add_role(
            self.employe,
            'MANAGER',
            date_debut=date_debut,
            created_by=self.admin
        )

        self.assertEqual(attribution.date_debut, date_debut)

    def test_add_role_default_date_is_today(self):
        """Test que la date par défaut est aujourd'hui."""
        attribution = PermissionService.add_role(
            self.employe,
            'COMPTABLE',
            created_by=self.admin
        )

        self.assertEqual(attribution.date_debut, date.today())

    def test_add_role_with_commentaire(self):
        """Test l'ajout d'un rôle avec commentaire."""
        attribution = PermissionService.add_role(
            self.employe,
            'DRH',
            created_by=self.admin,
            commentaire='Promotion suite à excellence'
        )

        self.assertEqual(attribution.commentaire, 'Promotion suite à excellence')

    def test_add_role_nonexistent_role(self):
        """Test qu'ajouter un rôle inexistant lève une exception."""
        with self.assertRaises(ZYRO.DoesNotExist):
            PermissionService.add_role(
                self.employe,
                'ROLE_INEXISTANT',
                created_by=self.admin
            )

    def test_add_role_inactive_role(self):
        """Test qu'on ne peut pas ajouter un rôle inactif."""
        # Créer un rôle inactif
        role_inactif = ZYRO.objects.create(
            CODE='ARCHIVED',
            LIBELLE='Rôle archivé',
            actif=False
        )

        with self.assertRaises(ZYRO.DoesNotExist):
            PermissionService.add_role(
                self.employe,
                'ARCHIVED',
                created_by=self.admin
            )


class PermissionServiceRemoveRoleTest(BasePermissionTestCase):
    """Tests pour remove_role()."""

    def test_remove_role_deactivates_attribution(self):
        """Test que remove_role() désactive l'attribution."""
        # Ajouter un rôle
        attribution = PermissionService.add_role(
            self.employe,
            'DRH',
            created_by=self.admin
        )

        # Vérifier qu'il est actif
        self.assertTrue(PermissionService.has_role(self.employe, 'DRH'))

        # Retirer le rôle
        PermissionService.remove_role(self.employe, 'DRH')

        # Vérifier qu'il n'est plus actif
        self.assertFalse(PermissionService.has_role(self.employe, 'DRH'))

    def test_remove_role_sets_date_fin(self):
        """Test que remove_role() met une date de fin."""
        # Ajouter puis retirer
        PermissionService.add_role(self.employe, 'MANAGER', created_by=self.admin)
        PermissionService.remove_role(self.employe, 'MANAGER')

        # Vérifier que date_fin est définie
        attribution = ZYRE.objects.filter(
            employe=self.employe,
            role__CODE='MANAGER'
        ).first()

        self.assertIsNotNone(attribution.date_fin)

    def test_remove_role_nonexistent_role(self):
        """Test qu'on peut retirer un rôle que l'employé n'a pas."""
        # Ne devrait pas lever d'exception
        PermissionService.remove_role(self.employe, 'DRH')


class PermissionServiceHasPermissionTest(BasePermissionTestCase):
    """Tests pour has_permission()."""

    def test_has_permission_via_custom_permission(self):
        """Test la vérification de permission custom."""
        # Attribuer un rôle avec permissions custom
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,  # a can_validate_all, can_manage_employees
            date_debut=date.today(),
            actif=True
        )

        # Vérifier les permissions
        self.assertTrue(PermissionService.has_permission(self.employe, 'can_validate_all'))
        self.assertTrue(PermissionService.has_permission(self.employe, 'can_manage_employees'))
        self.assertFalse(PermissionService.has_permission(self.employe, 'can_view_finances'))

    def test_has_permission_via_multiple_roles(self):
        """Test qu'on peut avoir des permissions de plusieurs rôles."""
        # Attribuer deux rôles
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_comptable,
            date_debut=date.today(),
            actif=True
        )

        # Vérifier les permissions des deux rôles
        self.assertTrue(PermissionService.has_permission(self.employe, 'can_validate_all'))  # DRH
        self.assertTrue(PermissionService.has_permission(self.employe, 'can_view_finances'))  # COMPTABLE
        self.assertTrue(PermissionService.has_permission(self.employe, 'can_export_data'))    # COMPTABLE

    def test_has_permission_no_roles(self):
        """Test qu'un employé sans rôle n'a aucune permission."""
        self.assertFalse(PermissionService.has_permission(self.employe, 'can_validate_all'))
        self.assertFalse(PermissionService.has_permission(self.employe, 'anything'))


class ZY00PermissionMethodsTest(BasePermissionTestCase):
    """Tests pour les méthodes de permission du modèle ZY00."""

    def test_has_role_method(self):
        """Test la méthode has_role() de ZY00."""
        # Attribuer un rôle
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        # Utiliser la méthode du modèle
        self.assertTrue(self.employe.has_role('DRH'))
        self.assertFalse(self.employe.has_role('MANAGER'))

    def test_get_roles_method(self):
        """Test la méthode get_roles() de ZY00."""
        # Attribuer des rôles
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_drh,
            date_debut=date.today(),
            actif=True
        )

        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_manager,
            date_debut=date.today(),
            actif=True
        )

        # Utiliser la méthode du modèle
        roles = self.employe.get_roles()

        self.assertEqual(roles.count(), 2)

    def test_has_permission_method(self):
        """Test la méthode has_permission() de ZY00."""
        # Attribuer un rôle
        ZYRE.objects.create(
            employe=self.employe,
            role=self.role_comptable,
            date_debut=date.today(),
            actif=True
        )

        # Utiliser la méthode du modèle
        self.assertTrue(self.employe.has_permission('can_view_finances'))
        self.assertFalse(self.employe.has_permission('can_validate_all'))

    def test_add_role_method(self):
        """Test la méthode add_role() de ZY00."""
        # Utiliser la méthode du modèle
        attribution = self.employe.add_role('DRH', created_by=self.admin)

        self.assertIsNotNone(attribution)
        self.assertTrue(self.employe.has_role('DRH'))

    def test_remove_role_method(self):
        """Test la méthode remove_role() de ZY00."""
        # Ajouter puis retirer
        self.employe.add_role('MANAGER', created_by=self.admin)
        self.assertTrue(self.employe.has_role('MANAGER'))

        self.employe.remove_role('MANAGER')
        self.assertFalse(self.employe.has_role('MANAGER'))


# Fonction pour exécuter tous les tests
def run_permission_tests():
    """Exécute tous les tests de permissions."""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["employee.tests.test_permissions"])

    return failures

# employee/services/hierarchy_service.py
"""
Service de gestion de la hiérarchie organisationnelle.
Extrait la logique métier du modèle ZY00 concernant les managers,
les départements et les relations hiérarchiques.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
import logging

from django.db.models import QuerySet

if TYPE_CHECKING:
    from employee.models import ZY00, ZYAF

logger = logging.getLogger(__name__)


class HierarchyService:
    """
    Service pour la gestion de la hiérarchie organisationnelle.

    Ce service centralise toute la logique liée aux managers,
    départements, équipes et relations hiérarchiques.

    Utilisation:
        from employee.services import HierarchyService

        # Vérifier si manager
        if HierarchyService.is_manager(employe):
            subordonnes = HierarchyService.get_subordinates(employe)

        # Obtenir le manager d'un employé
        manager = HierarchyService.get_manager_of_employee(employe)
    """

    # ==================== VÉRIFICATIONS MANAGER ====================

    @staticmethod
    def is_manager(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé est manager d'un département (via ZYMA)
        OU s'il a le rôle MANAGER.

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si l'employé est manager
        """
        from django.apps import apps
        ZYMA = apps.get_model('departement', 'ZYMA')

        # 1. Vérifier via la table ZYMA (managers de département)
        if ZYMA.objects.filter(
            employe=employee,
            actif=True,
            date_fin__isnull=True
        ).exists():
            return True

        # 2. Vérifier aussi le rôle MANAGER
        from employee.services.permission_service import PermissionService
        if PermissionService.has_role(employee, 'MANAGER'):
            return True

        return False

    @staticmethod
    def is_manager_of(manager: 'ZY00', employee: 'ZY00') -> bool:
        """
        Vérifie si un employé est manager d'un autre employé.

        Args:
            manager: L'employé potentiel manager
            employee: L'employé dont on vérifie la subordination

        Returns:
            bool: True si manager est le manager de employee
        """
        if not manager or not employee:
            return False

        try:
            from django.apps import apps
            ZYMA = apps.get_model('departement', 'ZYMA')
            ZYAF = apps.get_model('employee', 'ZYAF')

            # 1. Vérifier si manager est manager actif d'un département
            est_manager_actif = ZYMA.objects.filter(
                employe=manager,
                actif=True,
                date_fin__isnull=True
            ).exists()

            if not est_manager_actif:
                return False

            # 2. Vérifier si l'autre employé est dans un département géré
            affectation_employe = ZYAF.objects.filter(
                employe=employee,
                date_fin__isnull=True
            ).select_related('poste__DEPARTEMENT').first()

            if not affectation_employe or not affectation_employe.poste.DEPARTEMENT:
                return False

            # 3. Vérifier si manager gère le département de l'employé
            return ZYMA.objects.filter(
                employe=manager,
                departement=affectation_employe.poste.DEPARTEMENT,
                actif=True,
                date_fin__isnull=True
            ).exists()

        except Exception as e:
            logger.error(f"Erreur dans is_manager_of: {e}")
            return False

    @staticmethod
    def is_in_department_of_manager(employee: 'ZY00', manager: 'ZY00') -> bool:
        """
        Vérifie si un employé est dans un département géré par le manager.
        Basé sur ZYMA (managers) et ZYAF (affectations).

        Args:
            employee: L'employé à vérifier
            manager: Le manager potentiel

        Returns:
            bool: True si l'employé est dans un département du manager
        """
        try:
            from django.apps import apps
            ZYMA = apps.get_model('departement', 'ZYMA')
            ZYAF = apps.get_model('employee', 'ZYAF')

            # 1. Récupérer les départements gérés par le manager
            departements_geres = ZYMA.objects.filter(
                employe=manager,
                actif=True,
                date_fin__isnull=True
            ).values_list('departement', flat=True)

            if not departements_geres:
                return False

            # 2. Récupérer l'affectation active de l'employé
            affectation_employe = ZYAF.objects.filter(
                employe=employee,
                date_fin__isnull=True,
                employe__etat='actif'
            ).select_related('poste__DEPARTEMENT').first()

            if not affectation_employe or not affectation_employe.poste.DEPARTEMENT:
                return False

            # 3. Vérifier si le département de l'employé est géré par le manager
            return affectation_employe.poste.DEPARTEMENT.id in departements_geres

        except Exception as e:
            logger.error(f"Erreur dans is_in_department_of_manager: {e}")
            return False

    # ==================== RÉCUPÉRATION DES MANAGERS ====================

    @staticmethod
    def get_manager_of_employee(employee: 'ZY00') -> Optional['ZY00']:
        """
        Retourne le manager du département de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            ZY00 ou None: Le manager ou None si non trouvé
        """
        try:
            from django.apps import apps
            ZYMA = apps.get_model('departement', 'ZYMA')
            ZYAF = apps.get_model('employee', 'ZYAF')

            # Récupérer l'affectation active de l'employé
            affectation = ZYAF.objects.filter(
                employe=employee,
                date_fin__isnull=True
            ).select_related('poste__DEPARTEMENT').first()

            if affectation and affectation.poste.DEPARTEMENT:
                # Récupérer le manager actif de ce département
                manager_zyma = ZYMA.get_manager_actif(affectation.poste.DEPARTEMENT)
                if manager_zyma:
                    return manager_zyma.employe

            return None
        except Exception as e:
            logger.error(f"Erreur get_manager_of_employee pour {employee.matricule}: {e}")
            return None

    @staticmethod
    def get_manager_record(employee: 'ZY00'):
        """
        Retourne l'objet ZYMA du manager responsable de l'employé.
        Permet d'accéder à manager.employe, manager.departement, manager.date_debut, etc.

        Args:
            employee: Instance de ZY00

        Returns:
            ZYMA ou None: L'objet ZYMA complet ou None
        """
        try:
            from django.apps import apps
            ZYMA = apps.get_model('departement', 'ZYMA')
            ZYAF = apps.get_model('employee', 'ZYAF')

            # Récupérer l'affectation active avec le département
            affectation_active = ZYAF.objects.filter(
                employe=employee,
                date_fin__isnull=True
            ).select_related('poste__DEPARTEMENT').first()

            if not affectation_active:
                return None

            if not affectation_active.poste.DEPARTEMENT:
                return None

            # Récupérer le manager actif du département
            return ZYMA.get_manager_actif(affectation_active.poste.DEPARTEMENT)

        except Exception as e:
            logger.error(f"Erreur get_manager_record pour {employee.matricule}: {e}")
            return None

    # ==================== DÉPARTEMENTS GÉRÉS ====================

    @staticmethod
    def get_managed_departments(manager: 'ZY00') -> List:
        """
        Retourne les départements gérés par un manager.

        Args:
            manager: Instance de ZY00

        Returns:
            List: Liste des IDs de départements gérés
        """
        from django.apps import apps
        ZYMA = apps.get_model('departement', 'ZYMA')

        if not HierarchyService.is_manager(manager):
            return []

        return list(ZYMA.objects.filter(
            employe=manager,
            actif=True,
            date_fin__isnull=True
        ).values_list('departement', flat=True))

    @staticmethod
    def get_managed_department_objects(manager: 'ZY00') -> QuerySet:
        """
        Retourne les objets département (ZDDE) gérés par un manager.

        Args:
            manager: Instance de ZY00

        Returns:
            QuerySet[ZDDE]: Les départements gérés
        """
        from django.apps import apps
        ZDDE = apps.get_model('departement', 'ZDDE')

        dept_ids = HierarchyService.get_managed_departments(manager)
        return ZDDE.objects.filter(id__in=dept_ids)

    # ==================== SUBORDONNÉS ET ÉQUIPE ====================

    @staticmethod
    def get_subordinates(manager: 'ZY00') -> QuerySet:
        """
        Retourne tous les subordonnés (employés des départements gérés).

        Args:
            manager: Instance de ZY00

        Returns:
            QuerySet[ZY00]: Les employés subordonnés
        """
        from employee.models import ZY00, ZYAF

        departements_geres = HierarchyService.get_managed_departments(manager)
        if not departements_geres:
            return ZY00.objects.none()

        # Récupérer les employés de ces départements (via leur affectation active)
        subordonnes_ids = ZYAF.objects.filter(
            poste__DEPARTEMENT__in=departements_geres,
            date_fin__isnull=True,
            employe__etat='actif'
        ).exclude(employe=manager).values_list('employe', flat=True).distinct()

        return ZY00.objects.filter(matricule__in=subordonnes_ids)

    @staticmethod
    def get_team_members(employee: 'ZY00') -> QuerySet:
        """
        Retourne l'équipe complète du manager (tous les employés du département).
        Si l'employé est manager, retourne son équipe.
        Si l'employé n'est pas manager, retourne l'équipe de son manager.

        Args:
            employee: Instance de ZY00

        Returns:
            QuerySet[ZY00]: Les membres de l'équipe
        """
        from employee.models import ZY00

        # 1. Si l'employé est manager, retourner son équipe
        if HierarchyService.is_manager(employee):
            return HierarchyService.get_subordinates(employee)

        # 2. Sinon, trouver le manager et retourner son équipe
        manager = HierarchyService.get_manager_of_employee(employee)
        if manager:
            return HierarchyService.get_subordinates(manager)

        return ZY00.objects.none()

    @staticmethod
    def get_colleagues_same_department(employee: 'ZY00') -> QuerySet:
        """
        Retourne tous les collaborateurs du même département.

        Args:
            employee: Instance de ZY00

        Returns:
            QuerySet[ZY00]: Les collègues du même département
        """
        from employee.models import ZY00, ZYAF

        # Récupérer l'affectation active
        affectation = ZYAF.objects.filter(
            employe=employee,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

        if not affectation or not affectation.poste.DEPARTEMENT:
            return ZY00.objects.none()

        departement = affectation.poste.DEPARTEMENT

        # Chercher les affectations actives dans ce département
        employes_ids = ZYAF.objects.filter(
            poste__DEPARTEMENT=departement,
            date_fin__isnull=True,
            employe__etat='actif'
        ).values_list('employe', flat=True).distinct()

        return ZY00.objects.filter(matricule__in=employes_ids).exclude(pk=employee.pk)

    @staticmethod
    def is_in_team_of(employee: 'ZY00', other_employee: 'ZY00') -> bool:
        """
        Vérifie si un employé fait partie de l'équipe d'un autre employé.
        (même département ou sous la gestion du même manager)

        Args:
            employee: L'employé à vérifier
            other_employee: L'autre employé

        Returns:
            bool: True si employee fait partie de l'équipe de other_employee
        """
        if not employee or not other_employee:
            return False

        # 1. Même département
        dept_employee = HierarchyService.get_current_department(employee)
        dept_other = HierarchyService.get_current_department(other_employee)

        if dept_employee and dept_other and dept_employee == dept_other:
            return True

        # 2. Même manager
        manager_employee = HierarchyService.get_manager_of_employee(employee)
        manager_other = HierarchyService.get_manager_of_employee(other_employee)

        if manager_employee and manager_other and manager_employee == manager_other:
            return True

        # 3. L'autre employé est le manager de employee
        if manager_employee and manager_employee == other_employee:
            return True

        # 4. Employee est le manager de l'autre
        if manager_other and manager_other == employee:
            return True

        return False

    # ==================== DÉPARTEMENT ET POSTE ACTUELS ====================

    @staticmethod
    def get_current_department(employee: 'ZY00'):
        """
        Retourne le département actuel de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            ZDDE ou None: Le département actuel
        """
        from employee.models import ZYAF

        affectation = ZYAF.objects.filter(
            employe=employee,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

        if affectation and affectation.poste.DEPARTEMENT:
            return affectation.poste.DEPARTEMENT
        return None

    @staticmethod
    def get_current_position(employee: 'ZY00'):
        """
        Retourne le poste actuel de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            ZDPO ou None: Le poste actuel
        """
        from employee.models import ZYAF

        affectation = ZYAF.objects.filter(
            employe=employee,
            date_fin__isnull=True
        ).select_related('poste').first()

        if affectation:
            return affectation.poste
        return None

    @staticmethod
    def get_current_assignment(employee: 'ZY00') -> Optional['ZYAF']:
        """
        Retourne l'affectation actuelle de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            ZYAF ou None: L'affectation actuelle
        """
        from employee.models import ZYAF

        return ZYAF.objects.filter(
            employe=employee,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

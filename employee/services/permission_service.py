# employee/services/permission_service.py
"""
Service de gestion des permissions et rôles des employés.
Extrait la logique métier du modèle ZY00.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Set
from datetime import date
import logging

from django.db.models import QuerySet

if TYPE_CHECKING:
    from employee.models import ZY00, ZYRE, ZYRO

logger = logging.getLogger(__name__)


class PermissionService:
    """
    Service pour la gestion des permissions et rôles des employés.

    Ce service centralise toute la logique liée aux rôles (ZYRO/ZYRE)
    et aux vérifications de permissions.

    Utilisation:
        from employee.services import PermissionService

        # Vérifier un rôle
        if PermissionService.has_role(employe, 'DRH'):
            ...

        # Ajouter un rôle
        attribution = PermissionService.add_role(employe, 'MANAGER', created_by=admin)
    """

    # ==================== GESTION DES RÔLES ====================

    @staticmethod
    def has_role(employee: 'ZY00', role_code: str) -> bool:
        """
        Vérifie si l'employé a un rôle spécifique actif.

        Args:
            employee: Instance de ZY00
            role_code: Code du rôle (ex: 'DRH', 'MANAGER', 'COMPTABLE')

        Returns:
            bool: True si l'employé a ce rôle actif

        Exemple:
            if PermissionService.has_role(employe, 'DRH'):
                # L'employé a le rôle DRH
        """
        from employee.models import ZYRE

        return ZYRE.objects.filter(
            employe=employee,
            role__CODE=role_code,
            actif=True,
            date_fin__isnull=True
        ).exists()

    @staticmethod
    def get_roles(employee: 'ZY00') -> QuerySet:
        """
        Récupère tous les rôles actifs de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            QuerySet[ZYRE]: Liste des attributions de rôles actives

        Exemple:
            roles = PermissionService.get_roles(employe)
            for attribution in roles:
                print(attribution.role.CODE, attribution.role.LIBELLE)
        """
        from employee.models import ZYRE

        return ZYRE.objects.filter(
            employe=employee,
            actif=True,
            date_fin__isnull=True
        ).select_related('role')

    @staticmethod
    def get_role_codes(employee: 'ZY00') -> List[str]:
        """
        Récupère les codes de tous les rôles actifs de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            List[str]: Liste des codes de rôles
        """
        return list(
            PermissionService.get_roles(employee)
            .values_list('role__CODE', flat=True)
        )

    @staticmethod
    def add_role(
        employee: 'ZY00',
        role_code: str,
        date_debut: Optional[date] = None,
        created_by: Optional['ZY00'] = None,
        commentaire: str = ""
    ) -> 'ZYRE':
        """
        Ajoute un rôle à l'employé.

        Args:
            employee: Instance de ZY00
            role_code: Code du rôle à ajouter
            date_debut: Date de début (défaut: aujourd'hui)
            created_by: Employé qui crée l'attribution
            commentaire: Commentaire optionnel

        Returns:
            ZYRE: L'attribution créée

        Raises:
            ZYRO.DoesNotExist: Si le rôle n'existe pas
            ValidationError: Si l'employé a déjà ce rôle actif

        Exemple:
            attribution = PermissionService.add_role(
                employe, 'DRH', created_by=admin_employe
            )
        """
        from employee.models import ZYRO, ZYRE

        role = ZYRO.objects.get(CODE=role_code, actif=True)

        if not date_debut:
            date_debut = date.today()

        attribution = ZYRE.objects.create(
            employe=employee,
            role=role,
            date_debut=date_debut,
            actif=True,
            created_by=created_by,
            commentaire=commentaire
        )

        logger.info(
            f"Rôle {role_code} attribué à {employee.matricule} "
            f"par {created_by.matricule if created_by else 'système'}"
        )

        return attribution

    @staticmethod
    def remove_role(employee: 'ZY00', role_code: str, date_fin: Optional[date] = None) -> int:
        """
        Retire un rôle à l'employé (désactive l'attribution).

        Args:
            employee: Instance de ZY00
            role_code: Code du rôle à retirer
            date_fin: Date de fin (défaut: aujourd'hui)

        Returns:
            int: Nombre d'attributions désactivées

        Exemple:
            PermissionService.remove_role(employe, 'DRH')
        """
        from employee.models import ZYRE

        if not date_fin:
            date_fin = date.today()

        updated = ZYRE.objects.filter(
            employe=employee,
            role__CODE=role_code,
            actif=True,
            date_fin__isnull=True
        ).update(
            actif=False,
            date_fin=date_fin
        )

        if updated:
            logger.info(f"Rôle {role_code} retiré à {employee.matricule}")

        return updated

    @staticmethod
    def reactivate_role(attribution_id: int) -> Optional['ZYRE']:
        """
        Réactive une attribution de rôle précédemment désactivée.

        Args:
            attribution_id: ID de l'attribution ZYRE

        Returns:
            ZYRE: L'attribution réactivée ou None si non trouvée
        """
        from employee.models import ZYRE

        try:
            attribution = ZYRE.objects.get(id=attribution_id)
            attribution.actif = True
            attribution.date_fin = None
            attribution.save()

            logger.info(
                f"Rôle {attribution.role.CODE} réactivé pour "
                f"{attribution.employe.matricule}"
            )

            return attribution
        except ZYRE.DoesNotExist:
            return None

    # ==================== VÉRIFICATION DES PERMISSIONS ====================

    @staticmethod
    def has_permission(employee: 'ZY00', permission_name: str) -> bool:
        """
        Vérifie si l'employé a une permission spécifique via ses rôles.
        Cherche dans Django Groups ET dans les permissions custom.

        Args:
            employee: Instance de ZY00
            permission_name: Nom de la permission
                - Format Django: 'app_label.codename' ou juste 'codename'
                - Format custom: 'can_validate_rh', 'zdda.delete', etc.

        Returns:
            bool: True si au moins un des rôles actifs a cette permission

        Exemples:
            if PermissionService.has_permission(employe, 'absence.validate_absence_rh'):
                ...  # Permission Django
            if PermissionService.has_permission(employe, 'can_validate_rh'):
                ...  # Permission custom
        """
        from employee.models import ZYRE

        # 1. Vérifier dans les permissions Django natives de l'utilisateur
        if employee.user:
            if employee.user.has_perm(permission_name):
                return True

            # Vérifier aussi avec le format court si format long fourni
            if '.' in permission_name:
                _, codename = permission_name.split('.', 1)
                if employee.user.has_perm(permission_name):
                    return True

        # 2. Vérifier dans les rôles ZYRO (Django Groups + Custom)
        roles_actifs = ZYRE.objects.filter(
            employe=employee,
            actif=True,
            date_fin__isnull=True
        ).select_related('role')

        for attribution in roles_actifs:
            if attribution.role.has_permission(permission_name):
                return True

        return False

    @staticmethod
    def get_all_permissions(employee: 'ZY00') -> Set[str]:
        """
        Récupère toutes les permissions de l'employé (Django + custom).

        Args:
            employee: Instance de ZY00

        Returns:
            Set[str]: Ensemble des noms de permissions
        """
        permissions = set()

        # Permissions Django de l'utilisateur
        if employee.user:
            permissions.update(employee.user.get_all_permissions())

        # Permissions custom des rôles
        for attribution in PermissionService.get_roles(employee):
            if attribution.role.PERMISSIONS_CUSTOM:
                for perm, value in attribution.role.PERMISSIONS_CUSTOM.items():
                    if value:
                        permissions.add(perm)

        return permissions

    # ==================== VÉRIFICATIONS MÉTIER SPÉCIFIQUES ====================

    @staticmethod
    def is_drh(employee: 'ZY00') -> bool:
        """Vérifie si l'employé est DRH ou GESTION_APP."""
        return (
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP')
        )

    @staticmethod
    def is_assistant_rh(employee: 'ZY00') -> bool:
        """Vérifie si l'employé est assistant RH."""
        return PermissionService.has_role(employee, 'ASSISTANT_RH')

    @staticmethod
    def can_hire(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut embaucher.
        Rôles autorisés: DRH, GESTION_APP
        """
        return (
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP')
        )

    @staticmethod
    def can_manage_employees(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut accéder au menu Salariés.
        Rôles autorisés: DRH, GESTION_APP, ASSISTANT_RH, RH_VALIDATION_ABS
        """
        return (
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'ASSISTANT_RH') or
            PermissionService.has_role(employee, 'RH_VALIDATION_ABS')
        )

    @staticmethod
    def can_manage_app_settings(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut gérer le paramétrage de l'application.
        Rôle autorisé: GESTION_APP uniquement
        """
        return PermissionService.has_role(employee, 'GESTION_APP')

    @staticmethod
    def can_validate_absence_as_manager(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut valider les absences en tant que manager.
        Utilise le système de rôles existant (ZYRO).
        """
        from employee.services.hierarchy_service import HierarchyService

        return (
            PermissionService.has_role(employee, 'MANAGER_ABSENCE') or
            PermissionService.has_permission(employee, 'absence.valider_absence_manager') or
            HierarchyService.is_manager(employee)
        )

    @staticmethod
    def can_validate_absence_as_rh(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut valider les absences RH.
        Utilise le système de rôles existant (ZYRO).
        """
        return (
            PermissionService.has_role(employee, 'RH_VALIDATION') or
            PermissionService.has_permission(employee, 'absence.valider_absence_rh')
        )

    # ==================== PERMISSIONS MODULE PROJECT MANAGEMENT ====================

    @staticmethod
    def can_manage_clients(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut gérer les clients (créer, modifier, supprimer).
        Rôles autorisés: RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_manage_activities(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut gérer les activités.
        Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'MANAGER') or
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_manage_projects(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut gérer les projets (créer, modifier, supprimer).
        Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'MANAGER') or
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_manage_tasks(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut créer/modifier/supprimer des tâches/tickets.
        Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'MANAGER') or
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_validate_time_entries(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut valider les imputations de temps.
        Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'MANAGER') or
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_view_all_time_entries(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut voir toutes les imputations (validation, rapports, export).
        Rôles autorisés: MANAGER, RESP_ADMIN, DRH, GESTION_APP, DIRECTEUR
        """
        return (
            PermissionService.has_role(employee, 'MANAGER') or
            PermissionService.has_role(employee, 'RESP_ADMIN') or
            PermissionService.has_role(employee, 'DRH') or
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

    @staticmethod
    def can_create_time_entry(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut créer des imputations de temps.
        Tous les employés peuvent créer des imputations.
        """
        return True

    @staticmethod
    def can_view_tasks(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut voir les tâches.
        Tous les employés peuvent voir les tâches.
        """
        return True

    @staticmethod
    def can_upload_documents(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut uploader des documents.
        Tous les employés peuvent uploader des documents.
        """
        return True

    # ==================== PERMISSIONS MODULE AUDIT ====================

    @staticmethod
    def can_access_audit(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé peut accéder au module Conformité & Audit.
        Rôles autorisés: GESTION_APP, DIRECTEUR uniquement
        """
        return (
            PermissionService.has_role(employee, 'GESTION_APP') or
            PermissionService.has_role(employee, 'DIRECTEUR')
        )

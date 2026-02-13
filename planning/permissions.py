"""Utilitaires de permissions pour le module Planning."""
from django.db import models


def get_planning_role(user):
    """
    Determine le role de l'utilisateur dans le module planning.

    Returns:
        str ou None: 'admin', 'manager', 'employee', ou None
    """
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return 'admin'

    employe = getattr(user, 'employe', None)
    if not employe:
        return None

    if (employe.has_role('DRH')
            or employe.has_role('GESTION_APP')
            or employe.has_role('DIRECTEUR')
            or employe.has_role('PDG')):
        return 'admin'

    if employe.est_manager_departement():
        return 'manager'

    if employe.etat == 'actif':
        return 'employee'

    return None


def get_visible_employees(user):
    """
    Retourne le QuerySet des employes visibles selon le role.

    - admin : tous les employes actifs
    - manager : subordonnes + soi-meme
    - employee : collegues du meme departement + soi-meme
    """
    from employee.models import ZY00
    from employee.services.hierarchy_service import HierarchyService

    role = get_planning_role(user)
    employe = getattr(user, 'employe', None)

    if role == 'admin':
        return ZY00.objects.filter(etat='actif')

    if role == 'manager' and employe:
        subordinates = HierarchyService.get_subordinates(employe)
        return (subordinates | ZY00.objects.filter(pk=employe.pk)).distinct()

    if role == 'employee' and employe:
        colleagues = HierarchyService.get_colleagues_same_department(employe)
        return (colleagues | ZY00.objects.filter(pk=employe.pk)).distinct()

    return ZY00.objects.none()


def get_visible_plannings(user):
    """
    Retourne les plannings visibles selon le role.

    - admin : tous les plannings
    - manager : plannings de son departement + plannings globaux (dept=null)
    - employee : plannings de son departement + plannings globaux
    """
    from .models import Planning
    from employee.services.hierarchy_service import HierarchyService

    role = get_planning_role(user)
    employe = getattr(user, 'employe', None)

    if role == 'admin':
        return Planning.objects.all()

    if role == 'manager' and employe:
        dept_ids = HierarchyService.get_managed_departments(employe)
        return Planning.objects.filter(
            models.Q(departement_id__in=dept_ids) | models.Q(departement__isnull=True)
        )

    if role == 'employee' and employe:
        dept = HierarchyService.get_current_department(employe)
        if dept:
            return Planning.objects.filter(
                models.Q(departement=dept) | models.Q(departement__isnull=True)
            )
        return Planning.objects.none()

    return Planning.objects.none()


def can_edit_planning(user):
    """Retourne True si l'utilisateur peut creer/modifier/supprimer."""
    return get_planning_role(user) in ('admin', 'manager')

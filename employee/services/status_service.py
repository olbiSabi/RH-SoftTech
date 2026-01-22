# employee/services/status_service.py
"""
Service de gestion du statut des employés.
Gère le calcul du statut actif/inactif, l'ancienneté et les conventions.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date
import logging

from django.db.models import Q
from django.utils import timezone

if TYPE_CHECKING:
    from employee.models import ZY00, ZYCO

logger = logging.getLogger(__name__)


class StatusService:
    """
    Service pour la gestion du statut des employés.

    Ce service centralise toute la logique liée au statut (actif/inactif),
    aux contrats, à l'ancienneté et aux conventions collectives.

    Utilisation:
        from employee.services import StatusService

        # Vérifier si un employé est actif
        if StatusService.is_active(employe):
            ...

        # Synchroniser le statut
        StatusService.synchronize_status(employe)

        # Calculer l'ancienneté
        annees = StatusService.calculate_seniority_years(employe)
    """

    # ==================== STATUT ACTIF/INACTIF ====================

    @staticmethod
    def is_active(employee: 'ZY00') -> bool:
        """
        Calcule dynamiquement si l'employé est actif basé sur les contrats.
        C'est LA VÉRITÉ MÉTIER.

        Un employé est actif s'il a AU MOINS UN contrat actif
        (sans date de fin ou avec date de fin >= aujourd'hui).

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si l'employé est actif
        """
        aujourdhui = timezone.now().date()

        contrats_actifs = employee.contrats.filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=aujourdhui),
            actif=True
        )

        return contrats_actifs.exists()

    @staticmethod
    def synchronize_status(employee: 'ZY00') -> bool:
        """
        Synchronise le champ `etat` avec la réalité métier.

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si le statut a été modifié
        """
        if StatusService.is_active(employee):
            nouvel_etat = 'actif'
        else:
            # Les pré-embauches restent actifs même sans contrat
            if employee.type_dossier == 'PRE':
                nouvel_etat = 'actif'
            else:
                nouvel_etat = 'inactif'

        if employee.etat != nouvel_etat:
            employee.etat = nouvel_etat
            employee.save(update_fields=['etat'])
            logger.info(
                f"Statut de {employee.matricule} synchronisé vers '{nouvel_etat}'"
            )
            return True
        return False

    @staticmethod
    def deactivate_associated_data(employee: 'ZY00') -> None:
        """
        Désactive toutes les données associées lorsque l'employé est inactif.
        Appelé lors de la radiation ou du licenciement.

        Args:
            employee: Instance de ZY00
        """
        if employee.etat == 'inactif':
            employee.contrats.filter(actif=True).update(actif=False)
            employee.telephones.filter(actif=True).update(actif=False)
            employee.emails.filter(actif=True).update(actif=False)
            employee.affectations.filter(actif=True).update(actif=False)
            employee.adresses.filter(actif=True).update(actif=False)

            logger.info(
                f"Données associées désactivées pour {employee.matricule}"
            )

    # ==================== GESTION DES CONTRATS ====================

    @staticmethod
    def get_current_contract(employee: 'ZY00') -> Optional['ZYCO']:
        """
        Retourne le contrat actif actuel de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            ZYCO ou None: Le contrat actif
        """
        aujourdhui = timezone.now().date()

        return employee.contrats.filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=aujourdhui),
            actif=True
        ).order_by('-date_debut').first()

    @staticmethod
    def get_contracts_history(employee: 'ZY00'):
        """
        Retourne l'historique complet des contrats de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            QuerySet[ZYCO]: Tous les contrats triés par date
        """
        return employee.contrats.all().order_by('-date_debut')

    @staticmethod
    def has_active_contract(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé a un contrat actif.

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si un contrat actif existe
        """
        return StatusService.get_current_contract(employee) is not None

    @staticmethod
    def get_contract_type(employee: 'ZY00') -> Optional[str]:
        """
        Retourne le type de contrat actuel.

        Args:
            employee: Instance de ZY00

        Returns:
            str ou None: Le type de contrat (CDI, CDD, etc.)
        """
        contract = StatusService.get_current_contract(employee)
        return contract.type_contrat if contract else None

    # ==================== ANCIENNETÉ ====================

    @staticmethod
    def calculate_seniority_years(employee: 'ZY00') -> int:
        """
        Calcule l'ancienneté en années complètes.

        Args:
            employee: Instance de ZY00

        Returns:
            int: Nombre d'années d'ancienneté
        """
        if not employee.date_entree_entreprise:
            return 0

        aujourdhui = timezone.now().date()
        delta = aujourdhui - employee.date_entree_entreprise
        return delta.days // 365

    @staticmethod
    def calculate_seniority_months(employee: 'ZY00') -> int:
        """
        Calcule l'ancienneté en mois complets.

        Args:
            employee: Instance de ZY00

        Returns:
            int: Nombre de mois d'ancienneté
        """
        if not employee.date_entree_entreprise:
            return 0

        aujourdhui = timezone.now().date()
        delta = aujourdhui - employee.date_entree_entreprise
        return delta.days // 30

    @staticmethod
    def calculate_seniority_detailed(employee: 'ZY00') -> dict:
        """
        Calcule l'ancienneté détaillée (années, mois, jours).

        Args:
            employee: Instance de ZY00

        Returns:
            dict: {'years': int, 'months': int, 'days': int}
        """
        if not employee.date_entree_entreprise:
            return {'years': 0, 'months': 0, 'days': 0}

        aujourdhui = timezone.now().date()
        delta = aujourdhui - employee.date_entree_entreprise

        years = delta.days // 365
        remaining_days = delta.days % 365
        months = remaining_days // 30
        days = remaining_days % 30

        return {
            'years': years,
            'months': months,
            'days': days
        }

    # ==================== CONVENTIONS COLLECTIVES ====================

    @staticmethod
    def get_applicable_convention(employee: 'ZY00'):
        """
        Retourne la convention applicable à l'employé.
        Priorité : convention_personnalisee > entreprise.configuration_conventionnelle

        Args:
            employee: Instance de ZY00

        Returns:
            ConfigurationConventionnelle ou None
        """
        if employee.convention_personnalisee:
            return employee.convention_personnalisee
        if employee.entreprise and employee.entreprise.configuration_conventionnelle:
            return employee.entreprise.configuration_conventionnelle
        return None

    @staticmethod
    def get_leave_days_per_month(employee: 'ZY00') -> float:
        """
        Retourne le nombre de jours de congés acquis par mois.

        Args:
            employee: Instance de ZY00

        Returns:
            float: Jours de congés par mois (ex: 2.5)
        """
        convention = StatusService.get_applicable_convention(employee)
        if convention:
            return float(convention.jours_acquis_par_mois)
        return 2.5  # Valeur par défaut

    @staticmethod
    def get_work_time_coefficient(employee: 'ZY00') -> float:
        """
        Retourne le coefficient temps de travail.

        Args:
            employee: Instance de ZY00

        Returns:
            float: Coefficient (1.0 = temps plein, 0.5 = mi-temps)
        """
        return float(employee.coefficient_temps_travail)

    # ==================== TYPE DE DOSSIER ====================

    @staticmethod
    def is_pre_hire(employee: 'ZY00') -> bool:
        """
        Vérifie si l'employé est en pré-embauche.

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si type_dossier == 'PRE'
        """
        return employee.type_dossier == 'PRE'

    @staticmethod
    def is_employee(employee: 'ZY00') -> bool:
        """
        Vérifie si c'est un salarié validé.

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si type_dossier == 'SAL'
        """
        return employee.type_dossier == 'SAL'

    @staticmethod
    def validate_hire(employee: 'ZY00') -> bool:
        """
        Valide l'embauche (passe de PRE à SAL).

        Args:
            employee: Instance de ZY00

        Returns:
            bool: True si la validation a réussi
        """
        if employee.type_dossier != 'PRE':
            logger.warning(
                f"Tentative de validation d'embauche pour {employee.matricule} "
                f"qui n'est pas en pré-embauche"
            )
            return False

        employee.type_dossier = 'SAL'
        employee.date_validation_embauche = timezone.now().date()
        employee.save(update_fields=['type_dossier', 'date_validation_embauche'])

        logger.info(f"Embauche validée pour {employee.matricule}")
        return True

    # ==================== UTILITAIRES ====================

    @staticmethod
    def get_status_summary(employee: 'ZY00') -> dict:
        """
        Retourne un résumé complet du statut de l'employé.

        Args:
            employee: Instance de ZY00

        Returns:
            dict: Résumé du statut
        """
        current_contract = StatusService.get_current_contract(employee)
        convention = StatusService.get_applicable_convention(employee)
        seniority = StatusService.calculate_seniority_detailed(employee)

        return {
            'matricule': employee.matricule,
            'etat': employee.etat,
            'est_actif': StatusService.is_active(employee),
            'type_dossier': employee.type_dossier,
            'is_pre_hire': StatusService.is_pre_hire(employee),
            'contrat': {
                'type': current_contract.type_contrat if current_contract else None,
                'date_debut': current_contract.date_debut if current_contract else None,
                'date_fin': current_contract.date_fin if current_contract else None,
            } if current_contract else None,
            'anciennete': seniority,
            'convention': convention.nom if convention else None,
            'coefficient_temps': StatusService.get_work_time_coefficient(employee),
        }

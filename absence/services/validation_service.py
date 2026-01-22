# absence/services/validation_service.py
"""
Service de validation pour les absences.
"""
from datetime import datetime
from decimal import Decimal
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class ValidationService:
    """Service pour les validations liées aux absences."""

    @staticmethod
    def validate_date_range(date_debut, date_fin):
        """
        Valide une plage de dates.

        Args:
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            dict: Résultat de la validation avec 'valid' et 'errors'
        """
        errors = []

        if not date_debut:
            errors.append("La date de début est obligatoire")
        if not date_fin:
            errors.append("La date de fin est obligatoire")

        if date_debut and date_fin:
            if date_debut > date_fin:
                errors.append("La date de début ne peut pas être postérieure à la date de fin")

            # Vérifier que les dates ne sont pas trop anciennes
            today = timezone.now().date()
            if date_debut < today:
                errors.append("La date de début ne peut pas être dans le passé")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def check_overlap(employe, date_debut, date_fin, exclude_pk=None):
        """
        Vérifie s'il y a chevauchement avec d'autres absences.

        Args:
            employe: Instance de l'employé
            date_debut: Date de début
            date_fin: Date de fin
            exclude_pk: ID à exclure (pour les modifications)

        Returns:
            dict: Résultat avec 'has_overlap' et 'overlapping_absences'
        """
        from absence.models import Absence

        qs = Absence.objects.filter(
            employe=employe,
            statut__in=['BROUILLON', 'EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'VALIDE']
        )

        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)

        # Vérifier le chevauchement
        overlapping = qs.filter(
            date_debut__lte=date_fin,
            date_fin__gte=date_debut
        )

        return {
            'has_overlap': overlapping.exists(),
            'overlapping_absences': list(overlapping)
        }

    @staticmethod
    def parse_date_from_string(date_str, field_name='date'):
        """
        Parse une date depuis une chaîne.

        Args:
            date_str: Chaîne de date (format YYYY-MM-DD ou DD/MM/YYYY)
            field_name: Nom du champ pour les messages d'erreur

        Returns:
            dict: Résultat avec 'date' et 'error'
        """
        if not date_str:
            return {
                'date': None,
                'error': f"Le champ {field_name} est obligatoire"
            }

        # Essayer différents formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return {
                    'date': parsed_date,
                    'error': None
                }
            except ValueError:
                continue

        return {
            'date': None,
            'error': f"Format de date invalide pour {field_name}. Formats acceptés: YYYY-MM-DD, DD/MM/YYYY"
        }

    @staticmethod
    def validate_type_absence(type_absence, employe, nombre_jours):
        """
        Valide le type d'absence par rapport aux règles.

        Args:
            type_absence: Instance du type d'absence
            employe: Instance de l'employé
            nombre_jours: Nombre de jours demandés

        Returns:
            dict: Résultat de la validation
        """
        errors = []
        warnings = []

        if not type_absence.actif:
            errors.append("Ce type d'absence n'est plus actif")

        # Vérifier les limites si définies
        if type_absence.jours_max and nombre_jours > type_absence.jours_max:
            errors.append(
                f"Le nombre de jours ({nombre_jours}) dépasse la limite "
                f"autorisée ({type_absence.jours_max} jours) pour ce type d'absence"
            )

        # Avertissement pour les absences longues
        if nombre_jours > Decimal('10'):
            warnings.append(
                f"Cette demande de {nombre_jours} jours est considérée comme longue"
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def validate_solde_suffisant(employe, type_absence, nombre_jours, annee=None):
        """
        Vérifie que le solde est suffisant.

        Args:
            employe: Instance de l'employé
            type_absence: Type d'absence
            nombre_jours: Nombre de jours demandés
            annee: Année de référence

        Returns:
            dict: Résultat de la validation
        """
        from absence.services.absence_service import AbsenceService

        return AbsenceService.verifier_solde(employe, type_absence, nombre_jours, annee)

    @staticmethod
    def can_employee_submit(absence):
        """
        Vérifie si l'employé peut soumettre cette absence.

        Args:
            absence: Instance de l'absence

        Returns:
            dict: Résultat avec 'can_submit' et 'reason'
        """
        if absence.statut != 'BROUILLON':
            return {
                'can_submit': False,
                'reason': "L'absence doit être en brouillon pour être soumise"
            }

        if not absence.nombre_jours or absence.nombre_jours <= 0:
            return {
                'can_submit': False,
                'reason': "Le nombre de jours doit être supérieur à 0"
            }

        return {
            'can_submit': True,
            'reason': None
        }

    @staticmethod
    def can_manager_validate(absence, manager):
        """
        Vérifie si le manager peut valider cette absence.

        Args:
            absence: Instance de l'absence
            manager: Instance du manager (ZY00)

        Returns:
            dict: Résultat avec 'can_validate' et 'reason'
        """
        from departement.models import ZYMA

        if absence.statut != 'EN_ATTENTE_MANAGER':
            return {
                'can_validate': False,
                'reason': "L'absence n'est pas en attente de validation manager"
            }

        # Vérifier que le manager gère le département de l'employé
        affectation = absence.employe.affectations.filter(
            date_fin__isnull=True
        ).first()

        if not affectation or not affectation.poste:
            return {
                'can_validate': False,
                'reason': "L'employé n'a pas d'affectation active"
            }

        departement = affectation.poste.DEPARTEMENT

        is_manager = ZYMA.objects.filter(
            employe=manager,
            departement=departement,
            actif=True,
            date_fin__isnull=True
        ).exists()

        if not is_manager:
            return {
                'can_validate': False,
                'reason': "Vous n'êtes pas le manager du département de cet employé"
            }

        # Un manager ne peut pas valider sa propre absence
        if absence.employe == manager:
            return {
                'can_validate': False,
                'reason': "Vous ne pouvez pas valider votre propre demande d'absence"
            }

        return {
            'can_validate': True,
            'reason': None
        }

    @staticmethod
    def can_rh_validate(absence, rh_user):
        """
        Vérifie si l'utilisateur RH peut valider cette absence.

        Args:
            absence: Instance de l'absence
            rh_user: Instance de l'employé RH (ZY00)

        Returns:
            dict: Résultat avec 'can_validate' et 'reason'
        """
        if absence.statut != 'EN_ATTENTE_RH':
            return {
                'can_validate': False,
                'reason': "L'absence n'est pas en attente de validation RH"
            }

        # Vérifier que l'utilisateur a le rôle RH
        has_rh_role = rh_user.roles.filter(
            role__code__in=['DRH', 'ASSISTANT_RH']
        ).exists()

        if not has_rh_role:
            return {
                'can_validate': False,
                'reason': "Vous n'avez pas les droits RH pour valider cette absence"
            }

        # Un RH ne peut pas valider sa propre absence
        if absence.employe == rh_user:
            return {
                'can_validate': False,
                'reason': "Vous ne pouvez pas valider votre propre demande d'absence"
            }

        return {
            'can_validate': True,
            'reason': None
        }

    @staticmethod
    def can_cancel(absence, user):
        """
        Vérifie si l'utilisateur peut annuler cette absence.

        Args:
            absence: Instance de l'absence
            user: Instance de l'employé (ZY00)

        Returns:
            dict: Résultat avec 'can_cancel' et 'reason'
        """
        statuts_annulables = ['BROUILLON', 'EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'VALIDE']

        if absence.statut not in statuts_annulables:
            return {
                'can_cancel': False,
                'reason': "Cette absence ne peut pas être annulée"
            }

        # L'employé peut annuler sa propre absence
        if absence.employe == user:
            return {
                'can_cancel': True,
                'reason': None
            }

        # Les RH peuvent annuler n'importe quelle absence
        has_rh_role = user.roles.filter(
            role__code__in=['DRH', 'ASSISTANT_RH']
        ).exists()

        if has_rh_role:
            return {
                'can_cancel': True,
                'reason': None
            }

        return {
            'can_cancel': False,
            'reason': "Vous n'avez pas les droits pour annuler cette absence"
        }

# employee/services/validation_service.py
"""
Service de validation des données.
Contient les utilitaires de validation réutilisables (dates, chevauchements, etc.).
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple, Dict, Any, List
from datetime import date, datetime
import logging
import re

from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from django.db.models import Model

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service pour les validations communes.

    Ce service centralise les utilitaires de validation réutilisables
    dans toute l'application (dates, chevauchements, fichiers, etc.).

    Utilisation:
        from employee.services import ValidationService

        # Valider une plage de dates
        is_valid, errors = ValidationService.validate_date_range(start, end)

        # Vérifier les chevauchements
        has_overlap, existing = ValidationService.check_overlap(queryset, start, end)

        # Parser une date depuis une string
        parsed_date, errors = ValidationService.parse_date_from_string('2024-01-15', 'date_debut')
    """

    # ==================== VALIDATION DES DATES ====================

    @staticmethod
    def validate_date_range(
        start_date: Optional[date],
        end_date: Optional[date],
        allow_null_end: bool = True,
        field_names: Tuple[str, str] = ('date_debut', 'date_fin')
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Valide une plage de dates.

        Args:
            start_date: Date de début
            end_date: Date de fin (peut être None si allow_null_end=True)
            allow_null_end: Autoriser une date de fin nulle
            field_names: Noms des champs pour les messages d'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        errors = {}
        start_field, end_field = field_names

        # Vérifier que la date de début est fournie
        if not start_date:
            errors[start_field] = "La date de début est obligatoire."
            return False, errors

        # Vérifier que la date de fin est fournie si required
        if not allow_null_end and not end_date:
            errors[end_field] = "La date de fin est obligatoire."
            return False, errors

        # Vérifier que la date de fin est après la date de début
        if end_date and end_date <= start_date:
            errors[end_field] = "La date de fin doit être supérieure à la date de début."
            return False, errors

        return True, errors

    @staticmethod
    def validate_date_not_in_future(
        date_value: date,
        field_name: str = 'date'
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Vérifie qu'une date n'est pas dans le futur.

        Args:
            date_value: Date à valider
            field_name: Nom du champ pour le message d'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        from django.utils import timezone

        errors = {}
        if date_value > timezone.now().date():
            errors[field_name] = "La date ne peut pas être dans le futur."
            return False, errors

        return True, errors

    @staticmethod
    def validate_date_in_past(
        date_value: date,
        field_name: str = 'date'
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Vérifie qu'une date est dans le passé (strictement).

        Args:
            date_value: Date à valider
            field_name: Nom du champ pour le message d'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        from django.utils import timezone

        errors = {}
        if date_value >= timezone.now().date():
            errors[field_name] = "La date doit être dans le passé."
            return False, errors

        return True, errors

    # ==================== VÉRIFICATION DES CHEVAUCHEMENTS ====================

    @staticmethod
    def check_overlap(
        queryset: QuerySet,
        start_date: date,
        end_date: Optional[date],
        exclude_pk: Optional[Any] = None,
        start_field: str = 'date_debut',
        end_field: str = 'date_fin'
    ) -> Tuple[bool, Optional['Model']]:
        """
        Vérifie s'il y a un chevauchement de dates dans un queryset.

        Args:
            queryset: QuerySet à vérifier
            start_date: Date de début de la nouvelle période
            end_date: Date de fin de la nouvelle période (None = en cours)
            exclude_pk: PK à exclure (pour les modifications)
            start_field: Nom du champ date de début
            end_field: Nom du champ date de fin

        Returns:
            Tuple[bool, Model|None]: (has_overlap, conflicting_instance)
        """
        if exclude_pk is not None:
            queryset = queryset.exclude(pk=exclude_pk)

        for existing in queryset:
            existing_start = getattr(existing, start_field)
            existing_end = getattr(existing, end_field)

            # Vérifier les chevauchements
            # Cas 1: La nouvelle période commence pendant une période existante
            debut_chevauche = (
                existing_start <= start_date and
                (existing_end is None or existing_end >= start_date)
            )

            # Cas 2: La nouvelle période se termine pendant une période existante
            fin_chevauche = (
                end_date and
                existing_start <= end_date and
                (existing_end is None or existing_end >= end_date)
            )

            # Cas 3: La nouvelle période encadre une période existante
            encadrement = (
                start_date <= existing_start and
                (end_date is None or end_date >= existing_start)
            )

            if debut_chevauche or fin_chevauche or encadrement:
                return True, existing

        return False, None

    @staticmethod
    def check_overlap_with_message(
        queryset: QuerySet,
        start_date: date,
        end_date: Optional[date],
        exclude_pk: Optional[Any] = None,
        start_field: str = 'date_debut',
        end_field: str = 'date_fin',
        error_field: str = 'date_debut'
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Vérifie les chevauchements et retourne un message d'erreur formaté.

        Args:
            queryset: QuerySet à vérifier
            start_date: Date de début
            end_date: Date de fin
            exclude_pk: PK à exclure
            start_field: Nom du champ date de début
            end_field: Nom du champ date de fin
            error_field: Champ auquel attacher l'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        has_overlap, existing = ValidationService.check_overlap(
            queryset, start_date, end_date, exclude_pk, start_field, end_field
        )

        if has_overlap and existing:
            existing_start = getattr(existing, start_field)
            existing_end = getattr(existing, end_field)
            end_str = existing_end.strftime('%d/%m/%Y') if existing_end else 'présent'

            return False, {
                error_field: (
                    f"Chevauchement avec la période du "
                    f"{existing_start.strftime('%d/%m/%Y')} au {end_str}. "
                    f"Veuillez ajuster les dates."
                )
            }

        return True, {}

    # ==================== PARSING DES DATES ====================

    @staticmethod
    def parse_date_from_string(
        date_str: Optional[str],
        field_name: str = 'date',
        formats: Optional[List[str]] = None,
        required: bool = True
    ) -> Tuple[Optional[date], Dict[str, str]]:
        """
        Parse une date depuis une string avec plusieurs formats possibles.

        Args:
            date_str: String à parser
            field_name: Nom du champ pour le message d'erreur
            formats: Liste des formats à essayer (défaut: ISO, FR, US)
            required: Si True, une erreur est retournée si la date est vide

        Returns:
            Tuple[date|None, dict]: (parsed_date, errors_dict)
        """
        if formats is None:
            formats = [
                '%Y-%m-%d',      # ISO: 2024-01-15
                '%d/%m/%Y',      # FR: 15/01/2024
                '%d-%m-%Y',      # FR alt: 15-01-2024
                '%m/%d/%Y',      # US: 01/15/2024
                '%Y/%m/%d',      # ISO alt: 2024/01/15
            ]

        errors = {}

        if not date_str or date_str.strip() == '':
            if required:
                errors[field_name] = "Ce champ est obligatoire."
            return None, errors

        date_str = date_str.strip()

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                return parsed, {}
            except ValueError:
                continue

        errors[field_name] = f"Format de date invalide: '{date_str}'. Formats acceptés: JJ/MM/AAAA ou AAAA-MM-JJ"
        return None, errors

    @staticmethod
    def parse_dates_from_request(
        data: Dict[str, Any],
        date_fields: List[str],
        required_fields: Optional[List[str]] = None
    ) -> Tuple[Dict[str, Optional[date]], Dict[str, str]]:
        """
        Parse plusieurs dates depuis un dictionnaire (ex: request.POST).

        Args:
            data: Dictionnaire contenant les données
            date_fields: Liste des noms de champs date à parser
            required_fields: Liste des champs obligatoires

        Returns:
            Tuple[dict, dict]: (parsed_dates, errors)
        """
        if required_fields is None:
            required_fields = []

        parsed = {}
        all_errors = {}

        for field in date_fields:
            value = data.get(field, '').strip() if data.get(field) else ''
            is_required = field in required_fields

            parsed_date, errors = ValidationService.parse_date_from_string(
                value, field, required=is_required
            )

            parsed[field] = parsed_date
            all_errors.update(errors)

        return parsed, all_errors

    # ==================== VALIDATION DES FICHIERS ====================

    @staticmethod
    def validate_file_upload(
        file,
        max_size_mb: float = 5.0,
        allowed_extensions: Optional[List[str]] = None,
        field_name: str = 'fichier'
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Valide un fichier uploadé.

        Args:
            file: Fichier uploadé (InMemoryUploadedFile)
            max_size_mb: Taille maximale en MB
            allowed_extensions: Extensions autorisées (avec le point)
            field_name: Nom du champ pour le message d'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        import os

        if allowed_extensions is None:
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']

        errors = {}

        if not file:
            errors[field_name] = "Aucun fichier fourni."
            return False, errors

        # Vérifier l'extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            errors[field_name] = (
                f"Format de fichier non autorisé ({ext}). "
                f"Formats acceptés: {', '.join(allowed_extensions)}"
            )
            return False, errors

        # Vérifier la taille
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            errors[field_name] = f"Le fichier ne doit pas dépasser {max_size_mb} MB."
            return False, errors

        return True, errors

    @staticmethod
    def validate_image_upload(
        file,
        max_size_mb: float = 5.0,
        field_name: str = 'image'
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Valide une image uploadée.

        Args:
            file: Fichier image uploadé
            max_size_mb: Taille maximale en MB
            field_name: Nom du champ pour le message d'erreur

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        return ValidationService.validate_file_upload(
            file,
            max_size_mb=max_size_mb,
            allowed_extensions=['.jpg', '.jpeg', '.png', '.gif'],
            field_name=field_name
        )

    # ==================== VALIDATION DES CHAMPS TEXTE ====================

    @staticmethod
    def validate_phone_number(
        phone: Optional[str],
        field_name: str = 'telephone',
        required: bool = True
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Valide un numéro de téléphone.

        Args:
            phone: Numéro à valider
            field_name: Nom du champ pour le message d'erreur
            required: Si True, une erreur est retournée si vide

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        errors = {}

        if not phone or phone.strip() == '':
            if required:
                errors[field_name] = "Le numéro de téléphone est obligatoire."
                return False, errors
            return True, {}

        # Nettoyer le numéro
        cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)

        # Vérifier qu'il ne contient que des chiffres et éventuellement un +
        if not re.match(r'^\+?\d{8,15}$', cleaned):
            errors[field_name] = (
                "Format de numéro de téléphone invalide. "
                "Utilisez uniquement des chiffres (8-15 caractères)."
            )
            return False, errors

        return True, {}

    @staticmethod
    def validate_email(
        email: Optional[str],
        field_name: str = 'email',
        required: bool = True
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Valide une adresse email.

        Args:
            email: Email à valider
            field_name: Nom du champ pour le message d'erreur
            required: Si True, une erreur est retournée si vide

        Returns:
            Tuple[bool, dict]: (is_valid, errors_dict)
        """
        errors = {}

        if not email or email.strip() == '':
            if required:
                errors[field_name] = "L'adresse email est obligatoire."
                return False, errors
            return True, {}

        # Pattern simple pour email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            errors[field_name] = "Format d'adresse email invalide."
            return False, errors

        return True, {}

    # ==================== VALIDATION DES CHAMPS REQUIS ====================

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Dict[str, str]:
        """
        Vérifie que tous les champs requis sont présents et non vides.

        Args:
            data: Dictionnaire de données
            required_fields: Liste des champs requis

        Returns:
            dict: Dictionnaire des erreurs (vide si tout est ok)
        """
        errors = {}

        for field in required_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                errors[field] = "Ce champ est obligatoire."

        return errors

    @staticmethod
    def normalize_string(value: Optional[str]) -> str:
        """
        Normalise une chaîne (strip, etc.).

        Args:
            value: Valeur à normaliser

        Returns:
            str: Valeur normalisée
        """
        if value is None:
            return ''
        return value.strip()

    @staticmethod
    def capitalize_name(name: Optional[str]) -> str:
        """
        Met en forme un nom (majuscules).

        Args:
            name: Nom à formater

        Returns:
            str: Nom en majuscules
        """
        if not name:
            return ''
        return name.strip().upper()

    @staticmethod
    def capitalize_first_letter(text: Optional[str]) -> str:
        """
        Met la première lettre en majuscule.

        Args:
            text: Texte à formater

        Returns:
            str: Texte formaté
        """
        if not text:
            return ''
        text = text.strip()
        if text:
            return text[0].upper() + text[1:]
        return ''

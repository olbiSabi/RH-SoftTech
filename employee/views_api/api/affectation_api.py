# employee/views_api/api/affectation_api.py
"""
API modale pour la gestion des affectations (ZYAF).
Inclut des validations spécifiques: chevauchements, unicité affectation active.
"""
from typing import Dict, Any

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from departement.models import ZDPO
from employee.models import ZYAF
from employee.services.validation_service import ValidationService
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions


class AffectationValidationError(Exception):
    """Exception pour les erreurs de validation métier des affectations."""
    def __init__(self, errors: Dict[str, Any]):
        self.errors = errors
        super().__init__(str(errors))


class AffectationModalView(GenericModalCRUDView):
    """Vue modale CRUD pour les affectations avec validations métier."""

    model = ZYAF
    verbose_name = 'Affectation'
    verbose_name_plural = 'Affectations'

    fields_config = {
        'required': ['poste', 'date_debut'],
        'date_fields': ['date_debut', 'date_fin'],
        'date_range': ('date_debut', 'date_fin'),
    }

    def get_detail_data(self, obj) -> Dict[str, Any]:
        return {
            'id': obj.id,
            'poste': {
                'id': obj.poste.id,
                'LIBELLE': obj.poste.LIBELLE,
                'departement_id': obj.poste.DEPARTEMENT.id if obj.poste.DEPARTEMENT else None,
            },
            'date_debut': self.format_date(obj.date_debut),
            'date_fin': self.format_date(obj.date_fin),
            'actif': obj.actif if hasattr(obj, 'actif') else True,
        }

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        poste = get_object_or_404(ZDPO, id=request.POST.get('poste'))
        return {
            'employe': employe,
            'poste': poste,
            'date_debut': self.parsed_dates.get('date_debut'),
            'date_fin': self.parsed_dates.get('date_fin'),
        }

    def get_update_data(self, request, obj) -> Dict[str, Any]:
        poste = get_object_or_404(ZDPO, id=request.POST.get('poste'))
        return {
            'poste': poste,
            'date_debut': self.parsed_dates.get('date_debut'),
            'date_fin': self.parsed_dates.get('date_fin'),
        }

    def _validate_unique_active_assignment(self, employe, date_fin, exclude_id=None) -> Dict[str, str]:
        """Valide qu'il n'y a qu'une seule affectation active (sans date de fin)."""
        if date_fin:
            return {}  # Pas une affectation active

        queryset = ZYAF.objects.filter(
            employe=employe,
            date_fin__isnull=True
        )
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.exists():
            affectation_active = queryset.first()
            return {
                '__all__': [
                    f"Une affectation active existe déjà depuis le {affectation_active.date_debut.strftime('%d/%m/%Y')}. "
                    "Veuillez clôturer l'affectation existante avant d'en créer une nouvelle."
                ]
            }
        return {}

    def _validate_no_overlap(self, employe, date_debut, date_fin, exclude_id=None) -> Dict[str, str]:
        """Valide qu'il n'y a pas de chevauchement avec d'autres affectations."""
        queryset = ZYAF.objects.filter(employe=employe)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        has_overlap, existing = ValidationService.check_overlap(
            queryset=queryset,
            start_date=date_debut,
            end_date=date_fin,
            start_field='date_debut',
            end_field='date_fin'
        )

        if has_overlap and existing:
            date_fin_str = existing.date_fin.strftime('%d/%m/%Y') if existing.date_fin else "En cours"
            return {
                '__all__': [
                    f"Chevauchement détecté avec l'affectation du {existing.date_debut.strftime('%d/%m/%Y')} au {date_fin_str}. "
                    "Ajustez les dates pour éviter les chevauchements."
                ]
            }
        return {}

    def pre_create(self, request, employe, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation métier avant création."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')

        # Valider unicité affectation active
        errors = self._validate_unique_active_assignment(employe, date_fin)
        if errors:
            raise AffectationValidationError(errors)

        # Valider pas de chevauchement
        errors = self._validate_no_overlap(employe, date_debut, date_fin)
        if errors:
            raise AffectationValidationError(errors)

        return data

    def pre_update(self, request, obj, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation métier avant mise à jour."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')

        # Valider unicité affectation active
        errors = self._validate_unique_active_assignment(obj.employe, date_fin, exclude_id=obj.id)
        if errors:
            raise AffectationValidationError(errors)

        # Valider pas de chevauchement
        errors = self._validate_no_overlap(obj.employe, date_debut, date_fin, exclude_id=obj.id)
        if errors:
            raise AffectationValidationError(errors)

        return data


class AffectationModalViewWithValidation(AffectationModalView):
    """Version avec gestion des erreurs de validation métier."""

    def create(self, request) -> JsonResponse:
        try:
            return super().create(request)
        except AffectationValidationError as e:
            return JsonResponse({'errors': e.errors}, status=400)

    def update(self, request, id: int) -> JsonResponse:
        try:
            return super().update(request, id)
        except AffectationValidationError as e:
            return JsonResponse({'errors': e.errors}, status=400)


# Générer les fonctions de vue
(
    api_affectation_detail,
    api_affectation_create_modal,
    api_affectation_update_modal,
    api_affectation_delete_modal
) = make_modal_view_functions(AffectationModalViewWithValidation)

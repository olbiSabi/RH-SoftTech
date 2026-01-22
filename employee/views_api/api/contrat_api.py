# employee/views_api/api/contrat_api.py
"""
API modale pour la gestion des contrats (ZYCO).
Inclut des validations spécifiques: chevauchements, unicité contrat actif.
"""
from typing import Dict, Any

from django.http import JsonResponse

from employee.models import ZYCO
from employee.services.validation_service import ValidationService
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions


class ContratModalView(GenericModalCRUDView):
    """Vue modale CRUD pour les contrats avec validations métier."""

    model = ZYCO
    verbose_name = 'Contrat'
    verbose_name_plural = 'Contrats'

    fields_config = {
        'required': ['type_contrat', 'date_debut'],
        'date_fields': ['date_debut', 'date_fin'],
        'date_range': ('date_debut', 'date_fin'),
    }

    def get_detail_data(self, obj) -> Dict[str, Any]:
        return {
            'id': obj.id,
            'type_contrat': obj.type_contrat,
            'date_debut': self.format_date(obj.date_debut),
            'date_fin': self.format_date(obj.date_fin),
            'actif': obj.actif if hasattr(obj, 'actif') else True,
        }

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        return {
            'employe': employe,
            'type_contrat': request.POST.get('type_contrat'),
            'date_debut': self.parsed_dates.get('date_debut'),
            'date_fin': self.parsed_dates.get('date_fin'),
        }

    def _validate_unique_active_contract(self, employe, date_fin, exclude_id=None) -> Dict[str, str]:
        """Valide qu'il n'y a qu'un seul contrat actif (sans date de fin)."""
        if date_fin:
            return {}  # Pas un contrat actif, pas de validation nécessaire

        queryset = ZYCO.objects.filter(
            employe=employe,
            date_fin__isnull=True
        )
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.exists():
            contrat_actif = queryset.first()
            return {
                '__all__': [
                    f"Un contrat actif existe déjà depuis le {contrat_actif.date_debut.strftime('%d/%m/%Y')}. "
                    "Veuillez clôturer le contrat existant avant d'en créer un nouveau."
                ]
            }
        return {}

    def _validate_no_overlap(self, employe, date_debut, date_fin, exclude_id=None) -> Dict[str, str]:
        """Valide qu'il n'y a pas de chevauchement avec d'autres contrats."""
        queryset = ZYCO.objects.filter(employe=employe)
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
                    f"Chevauchement détecté avec le contrat du {existing.date_debut.strftime('%d/%m/%Y')} au {date_fin_str}. "
                    "Ajustez les dates pour éviter les chevauchements."
                ]
            }
        return {}

    def pre_create(self, request, employe, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation métier avant création."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')

        # Valider unicité contrat actif
        errors = self._validate_unique_active_contract(employe, date_fin)
        if errors:
            raise ContratValidationError(errors)

        # Valider pas de chevauchement
        errors = self._validate_no_overlap(employe, date_debut, date_fin)
        if errors:
            raise ContratValidationError(errors)

        return data

    def pre_update(self, request, obj, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation métier avant mise à jour."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')

        # Valider unicité contrat actif
        errors = self._validate_unique_active_contract(obj.employe, date_fin, exclude_id=obj.id)
        if errors:
            raise ContratValidationError(errors)

        # Valider pas de chevauchement
        errors = self._validate_no_overlap(obj.employe, date_debut, date_fin, exclude_id=obj.id)
        if errors:
            raise ContratValidationError(errors)

        return data


class ContratValidationError(Exception):
    """Exception pour les erreurs de validation métier des contrats."""
    def __init__(self, errors: Dict[str, Any]):
        self.errors = errors
        super().__init__(str(errors))


# Surcharger create et update pour gérer ContratValidationError
class ContratModalViewWithValidation(ContratModalView):
    """Version avec gestion des erreurs de validation métier."""

    def create(self, request) -> JsonResponse:
        try:
            return super().create(request)
        except ContratValidationError as e:
            return JsonResponse({'errors': e.errors}, status=400)

    def update(self, request, id: int) -> JsonResponse:
        try:
            return super().update(request, id)
        except ContratValidationError as e:
            return JsonResponse({'errors': e.errors}, status=400)


# Générer les fonctions de vue
(
    api_contrat_detail,
    api_contrat_create_modal,
    api_contrat_update_modal,
    api_contrat_delete_modal
) = make_modal_view_functions(ContratModalViewWithValidation)

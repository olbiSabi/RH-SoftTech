# employee/views_api/api/base.py
"""
Vue générique pour les opérations CRUD via modales.
Factorise le code répétitif des 60+ vues API modales.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional, Tuple, Type
from datetime import datetime
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from employee.services.validation_service import ValidationService

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class GenericModalCRUDView(View):
    """
    Vue générique pour les opérations CRUD via modales AJAX.

    Cette classe factorise le code répétitif des vues API modales.
    Chaque sous-classe doit définir:
        - model: Le modèle Django à manipuler
        - fields_config: Configuration des champs (requis, dates, etc.)
        - employee_field: Nom du champ ForeignKey vers ZY00 (défaut: 'employe')

    Exemple d'utilisation:
        class TelephoneModalView(GenericModalCRUDView):
            model = ZYTE
            fields_config = {
                'required': ['numero', 'date_debut_validite'],
                'date_fields': ['date_debut_validite', 'date_fin_validite'],
                'date_range': ('date_debut_validite', 'date_fin_validite'),
                'boolean_fields': ['actif'],
            }
            verbose_name = 'Téléphone'

            def get_detail_data(self, obj):
                return {
                    'id': obj.id,
                    'numero': obj.numero,
                    'date_debut_validite': self.format_date(obj.date_debut_validite),
                    'date_fin_validite': self.format_date(obj.date_fin_validite),
                    'actif': obj.actif,
                }

            def get_create_data(self, request, employe):
                return {
                    'employe': employe,
                    'numero': request.POST.get('numero'),
                    'date_debut_validite': self.parsed_dates.get('date_debut_validite'),
                    'date_fin_validite': self.parsed_dates.get('date_fin_validite'),
                    'actif': request.POST.get('actif') == 'on',
                }
    """

    # Configuration à définir dans les sous-classes
    model: Type['Model'] = None
    fields_config: Dict[str, Any] = {}
    employee_field: str = 'employe'
    verbose_name: str = 'Élément'
    verbose_name_plural: str = 'Éléments'

    # Stockage temporaire des dates parsées
    parsed_dates: Dict[str, Any] = {}

    # ==================== MÉTHODES UTILITAIRES ====================

    @staticmethod
    def format_date(date_obj) -> str:
        """Formate une date pour le JSON (format ISO)."""
        if date_obj:
            return date_obj.strftime('%Y-%m-%d')
        return ''

    def parse_dates(self, request) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Parse les dates depuis la requête POST.

        Returns:
            Tuple[dict, dict]: (dates_parsées, erreurs)
        """
        date_fields = self.fields_config.get('date_fields', [])
        required_dates = [f for f in date_fields if f in self.fields_config.get('required', [])]

        parsed, errors = ValidationService.parse_dates_from_request(
            request.POST,
            date_fields,
            required_dates
        )

        return parsed, errors

    def validate_date_range(self, errors: Dict[str, str]) -> Dict[str, str]:
        """
        Valide que la date de fin est après la date de début.

        Args:
            errors: Dictionnaire des erreurs existantes

        Returns:
            dict: Erreurs mises à jour
        """
        date_range = self.fields_config.get('date_range')
        if not date_range:
            return errors

        start_field, end_field = date_range
        start_date = self.parsed_dates.get(start_field)
        end_date = self.parsed_dates.get(end_field)

        if start_date and end_date:
            is_valid, range_errors = ValidationService.validate_date_range(
                start_date, end_date,
                allow_null_end=True,
                field_names=(start_field, end_field)
            )
            if not is_valid:
                errors.update(range_errors)

        return errors

    def validate_required_fields(self, request) -> Dict[str, str]:
        """
        Valide que les champs requis sont présents.

        Returns:
            dict: Erreurs de validation
        """
        required = self.fields_config.get('required', [])
        date_fields = self.fields_config.get('date_fields', [])

        # Ne pas valider les champs date ici, ils sont validés par parse_dates
        non_date_required = [f for f in required if f not in date_fields]

        errors = {}
        for field in non_date_required:
            value = request.POST.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors[field] = ['Ce champ est requis']

        return errors

    def get_employee(self, request) -> 'ZY00':
        """Récupère l'employé depuis la requête."""
        from employee.models import ZY00
        employe_uuid = request.POST.get('employe_uuid')
        return get_object_or_404(ZY00, uuid=employe_uuid)

    # ==================== MÉTHODES À SURCHARGER ====================

    def get_detail_data(self, obj) -> Dict[str, Any]:
        """
        Retourne les données à inclure dans la réponse JSON pour le détail.
        À surcharger dans les sous-classes.

        Args:
            obj: Instance du modèle

        Returns:
            dict: Données à retourner en JSON
        """
        raise NotImplementedError("Vous devez implémenter get_detail_data()")

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        """
        Retourne les données pour créer une nouvelle instance.
        À surcharger dans les sous-classes.

        Args:
            request: HttpRequest
            employe: Instance ZY00

        Returns:
            dict: Données pour la création
        """
        raise NotImplementedError("Vous devez implémenter get_create_data()")

    def get_update_data(self, request, obj) -> Dict[str, Any]:
        """
        Retourne les données pour mettre à jour une instance.
        Par défaut, utilise get_create_data sans l'employé.
        À surcharger si nécessaire.

        Args:
            request: HttpRequest
            obj: Instance existante

        Returns:
            dict: Données pour la mise à jour
        """
        data = self.get_create_data(request, obj.employe)
        # Retirer l'employé car on ne peut pas le modifier
        data.pop('employe', None)
        return data

    def pre_create(self, request, employe, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook appelé avant la création. Permet de modifier les données.

        Args:
            request: HttpRequest
            employe: Instance ZY00
            data: Données de création

        Returns:
            dict: Données modifiées
        """
        return data

    def post_create(self, request, obj) -> None:
        """
        Hook appelé après la création.

        Args:
            request: HttpRequest
            obj: Instance créée
        """
        pass

    def pre_update(self, request, obj, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook appelé avant la mise à jour.

        Args:
            request: HttpRequest
            obj: Instance à modifier
            data: Données de mise à jour

        Returns:
            dict: Données modifiées
        """
        return data

    def post_update(self, request, obj) -> None:
        """
        Hook appelé après la mise à jour.

        Args:
            request: HttpRequest
            obj: Instance modifiée
        """
        pass

    def pre_delete(self, request, obj) -> bool:
        """
        Hook appelé avant la suppression.

        Args:
            request: HttpRequest
            obj: Instance à supprimer

        Returns:
            bool: True pour continuer, False pour annuler
        """
        return True

    def post_delete(self, request, obj_id: int) -> None:
        """
        Hook appelé après la suppression.

        Args:
            request: HttpRequest
            obj_id: ID de l'instance supprimée
        """
        pass

    # ==================== OPÉRATIONS CRUD ====================

    def get_detail(self, request, id: int) -> JsonResponse:
        """
        Récupère les détails d'une instance.

        Args:
            request: HttpRequest
            id: ID de l'instance

        Returns:
            JsonResponse: Données de l'instance
        """
        try:
            obj = get_object_or_404(self.model, id=id)
            data = self.get_detail_data(obj)
            return JsonResponse(data)
        except Exception as e:
            logger.error(f"Erreur get_detail {self.verbose_name}: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    def create(self, request) -> JsonResponse:
        """
        Crée une nouvelle instance.

        Args:
            request: HttpRequest

        Returns:
            JsonResponse: Résultat de la création
        """
        try:
            # Récupérer l'employé
            employe = self.get_employee(request)

            # Valider les champs requis (non-date)
            errors = self.validate_required_fields(request)

            # Parser et valider les dates
            self.parsed_dates, date_errors = self.parse_dates(request)
            errors.update(date_errors)

            # Valider la plage de dates
            errors = self.validate_date_range(errors)

            if errors:
                return JsonResponse({'errors': errors}, status=400)

            # Préparer les données
            data = self.get_create_data(request, employe)
            data = self.pre_create(request, employe, data)

            # Créer l'instance
            with transaction.atomic():
                obj = self.model.objects.create(**data)

            # Hook post-création
            self.post_create(request, obj)

            logger.info(f"{self.verbose_name} créé(e): ID={obj.id}")

            return JsonResponse({
                'success': True,
                'message': f'{self.verbose_name} créé(e) avec succès',
                'id': obj.id
            })

        except ValidationError as e:
            logger.warning(f"Validation error create {self.verbose_name}: {e}")
            return JsonResponse({'errors': e.message_dict}, status=400)
        except Exception as e:
            logger.error(f"Erreur create {self.verbose_name}: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    def update(self, request, id: int) -> JsonResponse:
        """
        Met à jour une instance existante.

        Args:
            request: HttpRequest
            id: ID de l'instance

        Returns:
            JsonResponse: Résultat de la mise à jour
        """
        try:
            obj = get_object_or_404(self.model, id=id)

            # Valider les champs requis (non-date)
            errors = self.validate_required_fields(request)

            # Parser et valider les dates
            self.parsed_dates, date_errors = self.parse_dates(request)
            errors.update(date_errors)

            # Valider la plage de dates
            errors = self.validate_date_range(errors)

            if errors:
                return JsonResponse({'errors': errors}, status=400)

            # Préparer les données
            data = self.get_update_data(request, obj)
            data = self.pre_update(request, obj, data)

            # Mettre à jour l'instance
            with transaction.atomic():
                for key, value in data.items():
                    setattr(obj, key, value)
                obj.save()

            # Hook post-mise à jour
            self.post_update(request, obj)

            logger.info(f"{self.verbose_name} modifié(e): ID={obj.id}")

            return JsonResponse({
                'success': True,
                'message': f'{self.verbose_name} modifié(e) avec succès'
            })

        except ValidationError as e:
            logger.warning(f"Validation error update {self.verbose_name}: {e}")
            return JsonResponse({'errors': e.message_dict}, status=400)
        except Exception as e:
            logger.error(f"Erreur update {self.verbose_name}: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, id: int) -> JsonResponse:
        """
        Supprime une instance.

        Args:
            request: HttpRequest
            id: ID de l'instance

        Returns:
            JsonResponse: Résultat de la suppression
        """
        try:
            obj = get_object_or_404(self.model, id=id)

            # Hook pré-suppression
            if not self.pre_delete(request, obj):
                return JsonResponse({
                    'error': f'Suppression de {self.verbose_name} annulée'
                }, status=400)

            obj_id = obj.id

            with transaction.atomic():
                obj.delete()

            # Hook post-suppression
            self.post_delete(request, obj_id)

            logger.info(f"{self.verbose_name} supprimé(e): ID={obj_id}")

            return JsonResponse({
                'success': True,
                'message': f'{self.verbose_name} supprimé(e) avec succès'
            })

        except Exception as e:
            logger.error(f"Erreur delete {self.verbose_name}: {e}")
            return JsonResponse({'error': str(e)}, status=400)


def make_modal_view_functions(view_class: Type[GenericModalCRUDView]):
    """
    Factory qui génère les fonctions de vue à partir d'une classe GenericModalCRUDView.

    Usage:
        class TelephoneModalView(GenericModalCRUDView):
            ...

        detail, create, update, delete = make_modal_view_functions(TelephoneModalView)

        # Dans urls.py:
        path('api/telephone/<int:id>/', detail, name='api_telephone_detail'),
        path('api/telephone/create/', create, name='api_telephone_create'),
        path('api/telephone/<int:id>/update/', update, name='api_telephone_update'),
        path('api/telephone/<int:id>/delete/', delete, name='api_telephone_delete'),

    Args:
        view_class: Classe héritant de GenericModalCRUDView

    Returns:
        Tuple de 4 fonctions: (detail, create, update, delete)
    """
    view_instance = view_class()

    @login_required
    def detail_view(request, id):
        return view_instance.get_detail(request, id)

    @login_required
    def create_view(request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        return view_instance.create(request)

    @login_required
    def update_view(request, id):
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        return view_instance.update(request, id)

    @login_required
    def delete_view(request, id):
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        return view_instance.delete(request, id)

    # Nommer les fonctions pour le debug
    model_name = view_class.model.__name__ if view_class.model else 'Unknown'
    detail_view.__name__ = f'api_{model_name.lower()}_detail'
    create_view.__name__ = f'api_{model_name.lower()}_create_modal'
    update_view.__name__ = f'api_{model_name.lower()}_update_modal'
    delete_view.__name__ = f'api_{model_name.lower()}_delete_modal'

    return detail_view, create_view, update_view, delete_view

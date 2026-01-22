# employee/views_api/api/telephone_api.py
"""
API modale pour la gestion des téléphones (ZYTE).
"""
from typing import Dict, Any

from employee.models import ZYTE
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions


class TelephoneModalView(GenericModalCRUDView):
    """Vue modale CRUD pour les téléphones."""

    model = ZYTE
    verbose_name = 'Téléphone'
    verbose_name_plural = 'Téléphones'

    fields_config = {
        'required': ['numero', 'date_debut_validite'],
        'date_fields': ['date_debut_validite', 'date_fin_validite'],
        'date_range': ('date_debut_validite', 'date_fin_validite'),
        'boolean_fields': ['actif'],
    }

    def get_detail_data(self, obj) -> Dict[str, Any]:
        return {
            'id': obj.id,
            'numero': obj.numero,
            'date_debut_validite': self.format_date(obj.date_debut_validite),
            'date_fin_validite': self.format_date(obj.date_fin_validite),
            'actif': obj.actif,
        }

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        return {
            'employe': employe,
            'numero': request.POST.get('numero'),
            'date_debut_validite': self.parsed_dates.get('date_debut_validite'),
            'date_fin_validite': self.parsed_dates.get('date_fin_validite'),
            'actif': request.POST.get('actif') == 'on',
        }


# Générer les fonctions de vue
(
    api_telephone_detail,
    api_telephone_create_modal,
    api_telephone_update_modal,
    api_telephone_delete_modal
) = make_modal_view_functions(TelephoneModalView)

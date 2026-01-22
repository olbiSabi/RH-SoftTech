# employee/views_api/api/email_api.py
"""
API modale pour la gestion des emails (ZYME).
"""
from typing import Dict, Any

from employee.models import ZYME
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions


class EmailModalView(GenericModalCRUDView):
    """Vue modale CRUD pour les emails."""

    model = ZYME
    verbose_name = 'Email'
    verbose_name_plural = 'Emails'

    fields_config = {
        'required': ['email', 'date_debut_validite'],
        'date_fields': ['date_debut_validite', 'date_fin_validite'],
        'date_range': ('date_debut_validite', 'date_fin_validite'),
        'boolean_fields': ['actif'],
    }

    def get_detail_data(self, obj) -> Dict[str, Any]:
        return {
            'id': obj.id,
            'email': obj.email,
            'date_debut_validite': self.format_date(obj.date_debut_validite),
            'date_fin_validite': self.format_date(obj.date_fin_validite),
            'actif': obj.actif,
        }

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        return {
            'employe': employe,
            'email': request.POST.get('email'),
            'date_debut_validite': self.parsed_dates.get('date_debut_validite'),
            'date_fin_validite': self.parsed_dates.get('date_fin_validite'),
            'actif': request.POST.get('actif') == 'on',
        }


# Générer les fonctions de vue
(
    api_email_detail,
    api_email_create_modal,
    api_email_update_modal,
    api_email_delete_modal
) = make_modal_view_functions(EmailModalView)

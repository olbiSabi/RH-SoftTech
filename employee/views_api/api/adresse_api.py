# employee/views_api/api/adresse_api.py
"""
API modale pour la gestion des adresses (ZYAD).
"""
from typing import Dict, Any

from employee.models import ZYAD
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions


class AdresseModalView(GenericModalCRUDView):
    """Vue modale CRUD pour les adresses."""

    model = ZYAD
    verbose_name = 'Adresse'
    verbose_name_plural = 'Adresses'

    fields_config = {
        'required': ['type_adresse', 'rue', 'code_postal', 'ville', 'pays', 'date_debut'],
        'date_fields': ['date_debut', 'date_fin'],
        'date_range': ('date_debut', 'date_fin'),
        'boolean_fields': ['actif'],
    }

    def get_detail_data(self, obj) -> Dict[str, Any]:
        return {
            'id': obj.id,
            'type_adresse': obj.type_adresse,
            'rue': obj.rue,
            'complement': obj.complement or '',
            'code_postal': obj.code_postal,
            'ville': obj.ville,
            'pays': obj.pays,
            'date_debut': self.format_date(obj.date_debut),
            'date_fin': self.format_date(obj.date_fin),
            'actif': obj.actif,
        }

    def get_create_data(self, request, employe) -> Dict[str, Any]:
        return {
            'employe': employe,
            'type_adresse': request.POST.get('type_adresse'),
            'rue': request.POST.get('rue'),
            'complement': request.POST.get('complement', ''),
            'code_postal': request.POST.get('code_postal'),
            'ville': request.POST.get('ville'),
            'pays': request.POST.get('pays'),
            'date_debut': self.parsed_dates.get('date_debut'),
            'date_fin': self.parsed_dates.get('date_fin'),
            'actif': request.POST.get('actif') == 'on',
        }


# Générer les fonctions de vue
(
    api_adresse_detail,
    api_adresse_create_modal,
    api_adresse_update_modal,
    api_adresse_delete_modal
) = make_modal_view_functions(AdresseModalView)

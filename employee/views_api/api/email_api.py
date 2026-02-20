# employee/views_api/api/email_api.py
"""
API modale pour la gestion des emails (ZYME).
Synchronise automatiquement auth_user.email avec le ZYME actif le plus récent.
"""
import logging
from typing import Dict, Any

from employee.models import ZYME
from employee.views_api.api.base import GenericModalCRUDView, make_modal_view_functions

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _sync_user_email(employe):
        """Synchronise auth_user.email avec le ZYME actif le plus récent."""
        if not employe.user:
            return
        # ZYME.Meta.ordering = ['-date_debut_validite'] → .first() = le plus récent
        email_recent = employe.emails.filter(actif=True).first()
        if email_recent:
            employe.user.email = email_recent.email
            employe.user.save(update_fields=['email'])
            logger.info(f"Email auth_user synchronisé pour {employe.matricule}: {email_recent.email}")

    def post_create(self, request, obj):
        self._sync_user_email(obj.employe)

    def post_update(self, request, obj):
        self._sync_user_email(obj.employe)


# Générer les fonctions de vue
(
    api_email_detail,
    api_email_create_modal,
    api_email_update_modal,
    api_email_delete_modal
) = make_modal_view_functions(EmailModalView)

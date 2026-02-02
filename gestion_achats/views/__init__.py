"""
Package des vues pour le module GAC.
"""

from .dashboard_views import dashboard
from .demande_views import (
    demande_liste,
    demande_create,
    demande_detail,
    demande_update,
    demande_ligne_create,
    demande_submit,
    demande_validate_n1,
    demande_validate_n2,
    demande_refuse,
    demande_cancel,
    mes_demandes,
    demandes_a_valider,
)
from .bon_commande_views import (
    bon_commande_liste,
    bon_commande_detail,
    bon_commande_create_from_demande,
    bon_commande_emit,
    bon_commande_send,
    bon_commande_pdf,
)

__all__ = [
    # Dashboard
    'dashboard',

    # Demandes
    'demande_liste',
    'demande_create',
    'demande_detail',
    'demande_update',
    'demande_ligne_create',
    'demande_submit',
    'demande_validate_n1',
    'demande_validate_n2',
    'demande_refuse',
    'demande_cancel',
    'mes_demandes',
    'demandes_a_valider',

    # Bons de commande
    'bon_commande_liste',
    'bon_commande_detail',
    'bon_commande_create_from_demande',
    'bon_commande_emit',
    'bon_commande_send',
    'bon_commande_pdf',
]

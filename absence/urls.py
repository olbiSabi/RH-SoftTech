"""
URLs pour l'application absence
Système HR_ONIAN
"""

from django.urls import path
from . import views

app_name = 'absence'

urlpatterns = [
    # ==========================================
    # ROUTES EMPLOYÉ
    # ==========================================

    # Page principale employé
    path('mes-demandes/', views.employe_demandes, name='employe_demandes'),

    # Modification de demande
    path('demande/<uuid:demande_id>/modifier/', views.employe_modifier_demande, name='employe_modifier_demande'),

    # Suppression de demande
    path('demande/<uuid:demande_id>/supprimer/', views.employe_supprimer_demande, name='employe_supprimer_demande'),

    # Annulation de demande
    path('demande/<uuid:demande_id>/annuler/', views.employe_annuler_demande, name='employe_annuler_demande'),


    # ==========================================
    # ROUTES MANAGER
    # ==========================================

    # Page de validation manager
    path('manager/validation/', views.manager_validation, name='manager_validation'),

    # Validation/Refus par le manager
    path('manager/demande/<uuid:demande_id>/valider/', views.manager_valider_demande, name='manager_valider_demande'),
    path('manager/demande/<uuid:demande_id>/refuser/', views.manager_refuser_demande, name='manager_refuser_demande'),


    # ==========================================
    # ROUTES RH
    # ==========================================

    # Page de validation RH
    path('rh/validation/', views.rh_validation, name='rh_validation'),

    # Validation/Refus par RH
    path('rh/demande/<uuid:demande_id>/valider/', views.rh_valider_demande, name='rh_valider_demande'),
    path('rh/demande/<uuid:demande_id>/refuser/', views.rh_refuser_demande, name='rh_refuser_demande'),

    # Recherche d'employé
    path('rh/recherche-employe/', views.rh_recherche_employe, name='rh_recherche_employe'),

    # API pour l'autocomplete de recherche employé
    path('api/recherche-employe/', views.rh_recherche_employe_ajax, name='rh_recherche_employe_ajax'),


    # ==========================================
    # API ENDPOINTS (AJAX)
    # ==========================================

    # Calcul du nombre de jours
    path('api/calculer-jours/', views.api_calculer_jours, name='api_calculer_jours'),

    # Détails d'une demande
    path('api/demande/<uuid:demande_id>/', views.api_demande_detail, name='api_demande_detail'),

    # Solde d'un employé
    path('api/solde-employe/', views.api_solde_employe, name='api_solde_employe'),


    # 🆕 URLs NOTIFICATIONS
    path('notifications/', views.liste_notifications, name='liste_notifications'),
    path('notifications/json/', views.get_notifications_json, name='notifications_json'),
    path('notifications/<int:notification_id>/marquer-lue/', views.marquer_notification_lue,
         name='marquer_notification_lue'),  # ✅ <int:notification_id>
    path('notifications/marquer-toutes-lues/', views.marquer_toutes_lues, name='marquer_toutes_lues'),
]
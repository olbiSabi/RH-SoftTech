# absence/urls.py
"""
URLs principales de l'application absence.
Organisation modulaire pour une meilleure maintenabilité.

Les chemins d'URL sont préservés pour la compatibilité avec les templates existants.
"""
from django.urls import path

# Import des vues de pages depuis views_modules
from absence.views_modules import (
    # Configuration
    liste_conventions,
    liste_jours_feries,
    liste_types_absence,
    liste_parametres_calcul,
    # Acquisitions
    liste_acquisitions,
    # Absences
    liste_absences,
    creer_absence,
    modifier_absence,
    # Validation
    validation_manager,
    validation_rh,
    consultation_absences,
)

# Import des APIs depuis views_api
from absence.views_api import (
    # APIs Absence
    api_absence_detail,
    api_absence_delete,
    api_absence_annuler,
    api_valider_absence,
    api_historique_validation,
    api_verifier_solde,
    api_mes_absences_calendrier,
    # APIs Acquisition
    api_acquisition_detail,
    api_acquisition_update,
    api_acquisition_delete,
    api_recalculer_acquisition,
    api_calculer_acquisitions,
    api_calculer_acquis_a_date,
    api_acquisition_employe_annee,
    # APIs Convention
    api_convention_detail,
    api_convention_create,
    api_convention_update,
    api_convention_delete,
    api_convention_toggle_actif,
    # APIs Jour férié
    api_jour_ferie_detail,
    api_jour_ferie_create,
    api_jour_ferie_update,
    api_jour_ferie_delete,
    api_jour_ferie_toggle,
    api_dupliquer_jours_feries,
    api_jours_feries,
    # APIs Type absence
    api_type_absence_detail,
    api_type_absence_create,
    api_type_absence_update,
    api_type_absence_delete,
    api_type_absence_toggle,
    # APIs Paramètre calcul
    api_parametre_calcul_detail,
    api_parametre_calcul_create,
    api_parametre_calcul_update,
    api_parametre_calcul_delete,
    # APIs Notification
    notification_detail,
    marquer_toutes_lues,
    toutes_notifications,
    notification_counts,
    marquer_notification_lue,
)

app_name = 'absence'

urlpatterns = [
    # ===== PAGES PRINCIPALES - ABSENCES =====
    path('', liste_absences, name='liste_absences'),
    path('nouvelle/', creer_absence, name='creer_absence'),
    path('<int:id>/modifier/', modifier_absence, name='modifier_absence'),
    path('validation-manager/', validation_manager, name='validation_manager'),
    path('validation-rh/', validation_rh, name='validation_rh'),
    path('consultation/', consultation_absences, name='consultation_absences'),

    # ===== API ABSENCES =====
    path('api/mes-absences-calendrier/', api_mes_absences_calendrier, name='api_mes_absences_calendrier'),
    path('api/absence/<int:id>/', api_absence_detail, name='api_absence_detail'),
    path('api/absence/<int:id>/delete/', api_absence_delete, name='api_absence_delete'),
    path('api/absence/<int:id>/annuler/', api_absence_annuler, name='api_absence_annuler'),
    path('api/absence/<int:id>/valider/', api_valider_absence, name='api_valider_absence'),
    path('api/absence/<int:id>/historique/', api_historique_validation, name='api_historique_validation'),
    path('api/verifier-solde/', api_verifier_solde, name='api_verifier_solde'),
    path('api/acquisition-employe/<str:employe_id>/<int:annee>/', api_acquisition_employe_annee,
         name='api_acquisition_employe_annee'),

    # ===== ACQUISITIONS DE CONGÉS =====
    path('acquisitions/', liste_acquisitions, name='liste_acquisitions'),
    path('api/acquisition/<int:id>/', api_acquisition_detail, name='api_acquisition_detail'),
    path('api/acquisition/<int:id>/update/', api_acquisition_update, name='api_acquisition_update'),
    path('api/acquisition/<int:id>/delete/', api_acquisition_delete, name='api_acquisition_delete'),
    path('api/acquisition/<int:id>/recalculer/', api_recalculer_acquisition, name='api_recalculer_acquisition'),
    path('api/acquisitions/calculer/', api_calculer_acquisitions, name='api_calculer_acquisitions'),
    path('api/calculer-acquis-a-date/', api_calculer_acquis_a_date, name='api_calculer_acquis_a_date'),

    # ===== CONFIGURATION CONVENTIONNELLE =====
    path('conventions/', liste_conventions, name='liste_conventions'),
    path('api/convention/<int:id>/', api_convention_detail, name='api_convention_detail'),
    path('api/convention/create/', api_convention_create, name='api_convention_create'),
    path('api/convention/<int:id>/update/', api_convention_update, name='api_convention_update'),
    path('api/convention/<int:id>/delete/', api_convention_delete, name='api_convention_delete'),
    path('api/convention/<int:id>/toggle/', api_convention_toggle_actif, name='api_convention_toggle'),

    # ===== JOURS FÉRIÉS =====
    path('jours-feries/', liste_jours_feries, name='liste_jours_feries'),
    path('api/jour-ferie/<int:id>/', api_jour_ferie_detail, name='api_jour_ferie_detail'),
    path('api/jour-ferie/create/', api_jour_ferie_create, name='api_jour_ferie_create'),
    path('api/jour-ferie/<int:id>/update/', api_jour_ferie_update, name='api_jour_ferie_update'),
    path('api/jour-ferie/<int:id>/delete/', api_jour_ferie_delete, name='api_jour_ferie_delete'),
    path('api/jour-ferie/<int:id>/toggle/', api_jour_ferie_toggle, name='api_jour_ferie_toggle'),
    path('api/jour-ferie/dupliquer/', api_dupliquer_jours_feries, name='api_dupliquer_jours_feries'),

    # ===== TYPES D'ABSENCE =====
    path('types-absence/', liste_types_absence, name='liste_types_absence'),
    path('api/type-absence/<int:id>/', api_type_absence_detail, name='api_type_absence_detail'),
    path('api/type-absence/create/', api_type_absence_create, name='api_type_absence_create'),
    path('api/type-absence/<int:id>/update/', api_type_absence_update, name='api_type_absence_update'),
    path('api/type-absence/<int:id>/delete/', api_type_absence_delete, name='api_type_absence_delete'),
    path('api/type-absence/<int:id>/toggle/', api_type_absence_toggle, name='api_type_absence_toggle'),

    # ===== PARAMÈTRES CALCUL CONGÉS =====
    path('parametres-calcul/', liste_parametres_calcul, name='liste_parametres_calcul'),
    path('api/parametre-calcul/<int:id>/', api_parametre_calcul_detail, name='api_parametre_calcul_detail'),
    path('api/parametre-calcul/create/', api_parametre_calcul_create, name='api_parametre_calcul_create'),
    path('api/parametre-calcul/<int:id>/update/', api_parametre_calcul_update, name='api_parametre_calcul_update'),
    path('api/parametre-calcul/<int:id>/delete/', api_parametre_calcul_delete, name='api_parametre_calcul_delete'),
    path('api/jours-feries/', api_jours_feries, name='api_jours_feries'),

    # ===== NOTIFICATIONS =====
    path('notification/<int:id>/', notification_detail, name='notification_detail'),
    path('notifications/marquer-toutes-lues/', marquer_toutes_lues, name='marquer_toutes_lues'),
    path('notifications/toutes/', toutes_notifications, name='toutes_notifications'),
    path('notification/counts/', notification_counts, name='notification_counts'),
    path('notification/<int:notification_id>/marquer-lue/', marquer_notification_lue, name='marquer_notification_lue'),
]

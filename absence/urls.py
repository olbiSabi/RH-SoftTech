# absence/urls.py
from django.urls import path
from . import views

app_name = 'absence'

urlpatterns = [
    # ===== PAGES PRINCIPALES - ABSENCES =====
    path('', views.liste_absences, name='liste_absences'),
    path('nouvelle/', views.creer_absence, name='creer_absence'),
    path('<int:id>/modifier/', views.modifier_absence, name='modifier_absence'),
    path('validation-manager/', views.validation_manager, name='validation_manager'),
    path('validation-rh/', views.validation_rh, name='validation_rh'),
    path('consultation/', views.consultation_absences, name='consultation_absences'),


    # ===== API ABSENCES =====
    path('api/mes-absences-calendrier/', views.api_mes_absences_calendrier, name='api_mes_absences_calendrier'),
    path('api/absence/<int:id>/', views.api_absence_detail, name='api_absence_detail'),
    path('api/absence/<int:id>/delete/', views.api_absence_delete, name='api_absence_delete'),
    path('api/absence/<int:id>/annuler/', views.api_absence_annuler, name='api_absence_annuler'),
    path('api/absence/<int:id>/valider/', views.api_valider_absence, name='api_valider_absence'),
    path('api/absence/<int:id>/historique/', views.api_historique_validation, name='api_historique_validation'),
    path('api/verifier-solde/', views.api_verifier_solde, name='api_verifier_solde'),
    path('api/acquisition-employe/<str:employe_id>/<int:annee>/', views.api_acquisition_employe_annee,
         name='api_acquisition_employe_annee'),

    # ===== ACQUISITIONS DE CONGÉS =====
    path('acquisitions/', views.liste_acquisitions, name='liste_acquisitions'),
    path('api/acquisition/<int:id>/', views.api_acquisition_detail, name='api_acquisition_detail'),
    path('api/acquisition/<int:id>/update/', views.api_acquisition_update, name='api_acquisition_update'),
    path('api/acquisition/<int:id>/delete/', views.api_acquisition_delete, name='api_acquisition_delete'),
    path('api/acquisition/<int:id>/recalculer/', views.api_recalculer_acquisition, name='api_recalculer_acquisition'),
    path('api/acquisitions/calculer/', views.api_calculer_acquisitions, name='api_calculer_acquisitions'),
    path('api/calculer-acquis-a-date/', views.api_calculer_acquis_a_date, name='api_calculer_acquis_a_date'),

    # ===== CONFIGURATION CONVENTIONNELLE =====
    path('conventions/', views.liste_conventions, name='liste_conventions'),
    path('api/convention/<int:id>/', views.api_convention_detail, name='api_convention_detail'),
    path('api/convention/create/', views.api_convention_create, name='api_convention_create'),
    path('api/convention/<int:id>/update/', views.api_convention_update, name='api_convention_update'),
    path('api/convention/<int:id>/delete/', views.api_convention_delete, name='api_convention_delete'),
    path('api/convention/<int:id>/toggle/', views.api_convention_toggle_actif, name='api_convention_toggle'),

    # ===== JOURS FÉRIÉS =====
    path('jours-feries/', views.liste_jours_feries, name='liste_jours_feries'),
    path('api/jour-ferie/<int:id>/', views.api_jour_ferie_detail, name='api_jour_ferie_detail'),
    path('api/jour-ferie/create/', views.api_jour_ferie_create, name='api_jour_ferie_create'),
    path('api/jour-ferie/<int:id>/update/', views.api_jour_ferie_update, name='api_jour_ferie_update'),
    path('api/jour-ferie/<int:id>/delete/', views.api_jour_ferie_delete, name='api_jour_ferie_delete'),
    path('api/jour-ferie/<int:id>/toggle/', views.api_jour_ferie_toggle, name='api_jour_ferie_toggle'),
    path('api/jour-ferie/dupliquer/', views.api_dupliquer_jours_feries, name='api_dupliquer_jours_feries'),

    # ===== TYPES D'ABSENCE =====
    path('types-absence/', views.liste_types_absence, name='liste_types_absence'),
    path('api/type-absence/<int:id>/', views.api_type_absence_detail, name='api_type_absence_detail'),
    path('api/type-absence/create/', views.api_type_absence_create, name='api_type_absence_create'),
    path('api/type-absence/<int:id>/update/', views.api_type_absence_update, name='api_type_absence_update'),
    path('api/type-absence/<int:id>/delete/', views.api_type_absence_delete, name='api_type_absence_delete'),
    path('api/type-absence/<int:id>/toggle/', views.api_type_absence_toggle, name='api_type_absence_toggle'),

    # ===== PARAMÈTRES CALCUL CONGÉS =====
    path('parametres-calcul/', views.liste_parametres_calcul, name='liste_parametres_calcul'),
    path('api/parametre-calcul/<int:id>/', views.api_parametre_calcul_detail, name='api_parametre_calcul_detail'),
    path('api/parametre-calcul/create/', views.api_parametre_calcul_create, name='api_parametre_calcul_create'),
    path('api/parametre-calcul/<int:id>/update/', views.api_parametre_calcul_update, name='api_parametre_calcul_update'),
    path('api/parametre-calcul/<int:id>/delete/', views.api_parametre_calcul_delete, name='api_parametre_calcul_delete'),
    path('api/jours-feries/', views.api_jours_feries, name='api_jours_feries'),

    # Notifications
    path('notification/<int:id>/', views.notification_detail, name='notification_detail'),
    path('notifications/marquer-toutes-lues/', views.marquer_toutes_lues, name='marquer_toutes_lues'),
    path('notifications/toutes/', views.toutes_notifications, name='toutes_notifications'),
    path('notification/counts/', views.notification_counts, name='notification_counts'),
    path('notification/<int:notification_id>/marquer-lue/',views.marquer_notification_lue,name='marquer_notification_lue'),
]
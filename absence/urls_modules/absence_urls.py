# absence/urls_modules/absence_urls.py
"""
URLs pour la gestion des absences (pages et API).
"""
from django.urls import path
from absence import views

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
]

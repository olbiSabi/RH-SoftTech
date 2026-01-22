# absence/urls_modules/configuration_urls.py
"""
URLs pour la configuration des absences (conventions, jours fériés, types, paramètres).
"""
from django.urls import path
from absence import views

urlpatterns = [
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
    path('api/jours-feries/', views.api_jours_feries, name='api_jours_feries'),

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
]

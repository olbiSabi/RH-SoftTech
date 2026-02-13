"""URLs pour le module Planning."""
from django.urls import path
from . import views, views_api

app_name = 'planning'

urlpatterns = [
    # Pages
    path('', views.planning_calendar, name='planning_calendar'),
    path('mon-planning/', views.mon_planning, name='mon_planning'),

    # API Affectations
    path('api/affectations/', views_api.api_affectations, name='api_affectations'),
    path('api/affectation/create/', views_api.api_affectation_create, name='api_affectation_create'),
    path('api/affectation/<int:pk>/', views_api.api_affectation_detail, name='api_affectation_detail'),
    path('api/affectation/<int:pk>/update/', views_api.api_affectation_update, name='api_affectation_update'),
    path('api/affectation/<int:pk>/delete/', views_api.api_affectation_delete, name='api_affectation_delete'),

    # API Evenements
    path('api/evenements/', views_api.api_evenements, name='api_evenements'),
    path('api/evenement/create/', views_api.api_evenement_create, name='api_evenement_create'),
    path('api/evenement/<int:pk>/', views_api.api_evenement_detail, name='api_evenement_detail'),
    path('api/evenement/<int:pk>/update/', views_api.api_evenement_update, name='api_evenement_update'),
    path('api/evenement/<int:pk>/delete/', views_api.api_evenement_delete, name='api_evenement_delete'),

    # API utilitaire
    path('api/postes/<int:site_id>/', views_api.api_postes_par_site, name='api_postes_par_site'),

    # Gestion Sites de travail
    path('sites/', views.liste_sites, name='liste_sites'),
    path('sites/creer/', views.creer_site, name='creer_site'),
    path('sites/<int:pk>/modifier/', views.modifier_site, name='modifier_site'),
    path('sites/<int:pk>/supprimer/', views.supprimer_site, name='supprimer_site'),

    # Gestion Postes de travail
    path('postes/', views.liste_postes, name='liste_postes'),
    path('postes/creer/', views.creer_poste, name='creer_poste'),
    path('postes/<int:pk>/modifier/', views.modifier_poste, name='modifier_poste'),
    path('postes/<int:pk>/supprimer/', views.supprimer_poste, name='supprimer_poste'),

    # Gestion Plannings
    path('plannings/', views.liste_plannings, name='liste_plannings'),
    path('plannings/creer/', views.creer_planning, name='creer_planning'),
    path('plannings/<int:pk>/modifier/', views.modifier_planning, name='modifier_planning'),
    path('plannings/<int:pk>/supprimer/', views.supprimer_planning, name='supprimer_planning'),
]

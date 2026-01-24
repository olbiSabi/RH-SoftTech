# audit/urls.py
"""
URLs pour le module Conformité & Audit.
"""
from django.urls import path
from audit import views

app_name = 'audit'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Alertes
    path('alertes/', views.liste_alertes, name='liste_alertes'),
    path('alertes/<uuid:uuid>/', views.detail_alerte, name='detail_alerte'),
    path('alertes/<uuid:uuid>/resoudre/', views.resoudre_alerte, name='resoudre_alerte'),
    path('alertes/<uuid:uuid>/ignorer/', views.ignorer_alerte, name='ignorer_alerte'),
    path('alertes/verifier/', views.executer_verifications, name='executer_verifications'),

    # Logs
    path('logs/', views.liste_logs, name='liste_logs'),
    path('logs/<int:pk>/', views.detail_log, name='detail_log'),

    # Rapports
    path('rapports/', views.liste_rapports, name='liste_rapports'),
    path('rapports/generer/', views.generer_rapport, name='generer_rapport'),
    path('rapports/<uuid:uuid>/telecharger/', views.telecharger_rapport, name='telecharger_rapport'),

    # Règles de conformité
    path('regles/', views.liste_regles, name='liste_regles'),
    path('regles/nouvelle/', views.creer_regle, name='creer_regle'),
    path('regles/<int:pk>/modifier/', views.modifier_regle, name='modifier_regle'),

    # API
    path('api/stats/', views.api_stats_dashboard, name='api_stats'),
]

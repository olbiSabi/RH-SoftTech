# materiel/urls.py
"""
URLs pour le module Suivi du Matériel & Parc.
"""
from django.urls import path
from materiel import views

app_name = 'materiel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Matériels
    path('materiels/', views.liste_materiels, name='liste_materiels'),
    path('materiels/nouveau/', views.creer_materiel, name='creer_materiel'),
    path('materiels/<uuid:uuid>/', views.detail_materiel, name='detail_materiel'),
    path('materiels/<uuid:uuid>/modifier/', views.modifier_materiel, name='modifier_materiel'),
    path('materiels/<uuid:uuid>/affecter/', views.affecter_materiel, name='affecter_materiel'),
    path('materiels/<uuid:uuid>/retourner/', views.retourner_materiel, name='retourner_materiel'),
    path('materiels/<uuid:uuid>/reformer/', views.reformer_materiel, name='reformer_materiel'),
    path('materiels/export/', views.export_materiels_excel, name='export_materiels'),

    # Maintenances
    path('maintenances/', views.liste_maintenances, name='liste_maintenances'),
    path('materiels/<uuid:uuid>/maintenance/', views.creer_maintenance, name='creer_maintenance'),
    path('maintenances/<int:pk>/demarrer/', views.demarrer_maintenance, name='demarrer_maintenance'),
    path('maintenances/<int:pk>/terminer/', views.terminer_maintenance, name='terminer_maintenance'),

    # Catégories
    path('categories/', views.liste_categories, name='liste_categories'),
    path('categories/nouvelle/', views.creer_categorie, name='creer_categorie'),
    path('categories/<int:pk>/modifier/', views.modifier_categorie, name='modifier_categorie'),

    # Fournisseurs
    path('fournisseurs/', views.liste_fournisseurs, name='liste_fournisseurs'),
    path('fournisseurs/nouveau/', views.creer_fournisseur, name='creer_fournisseur'),
    path('fournisseurs/<int:pk>/modifier/', views.modifier_fournisseur, name='modifier_fournisseur'),

    # Mon matériel (vue employé)
    path('mon-materiel/', views.mon_materiel, name='mon_materiel'),

    # API
    path('api/search-employes/', views.api_search_employes, name='api_search_employes'),
    path('api/stats/', views.api_stats_dashboard, name='api_stats'),
]

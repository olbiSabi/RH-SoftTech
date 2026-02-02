"""
URLs pour le module GAC (Gestion des Achats & Commandes).
"""

from django.urls import path
from gestion_achats import views

app_name = 'gestion_achats'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Demandes d'achat
    path('demandes/', views.demande_liste, name='demande_liste'),
    path('demandes/mes-demandes/', views.mes_demandes, name='mes_demandes'),
    path('demandes/a-valider/', views.demandes_a_valider, name='demandes_a_valider'),
    path('demandes/create/', views.demande_create, name='demande_create'),
    path('demandes/<uuid:pk>/', views.demande_detail, name='demande_detail'),
    path('demandes/<uuid:pk>/update/', views.demande_update, name='demande_update'),
    path('demandes/<uuid:pk>/ligne/create/', views.demande_ligne_create, name='demande_ligne_create'),
    path('demandes/<uuid:pk>/submit/', views.demande_submit, name='demande_submit'),
    path('demandes/<uuid:pk>/validate-n1/', views.demande_validate_n1, name='demande_validate_n1'),
    path('demandes/<uuid:pk>/validate-n2/', views.demande_validate_n2, name='demande_validate_n2'),
    path('demandes/<uuid:pk>/refuse/', views.demande_refuse, name='demande_refuse'),
    path('demandes/<uuid:pk>/cancel/', views.demande_cancel, name='demande_cancel'),

    # Bons de commande
    path('bons-commande/', views.bon_commande_liste, name='bon_commande_liste'),
    path('bons-commande/<uuid:pk>/', views.bon_commande_detail, name='bon_commande_detail'),
    path('bons-commande/create-from-demande/<uuid:demande_pk>/', views.bon_commande_create_from_demande, name='bon_commande_create_from_demande'),
    path('bons-commande/<uuid:pk>/emit/', views.bon_commande_emit, name='bon_commande_emit'),
    path('bons-commande/<uuid:pk>/send/', views.bon_commande_send, name='bon_commande_send'),
    path('bons-commande/<uuid:pk>/pdf/', views.bon_commande_pdf, name='bon_commande_pdf'),
]

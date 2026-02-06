"""
URLs pour le module GAC (Gestion des Achats & Commandes).
"""

from django.urls import path
from gestion_achats.views import (
    dashboard_views,
    demande_views,
    bon_commande_views,
    fournisseur_views,
    reception_views,
    bon_retour_views,
    catalogue_views,
    budget_views,
    parametres_views,
    debug_views,
    diagnostic_validateurs,
    test_permissions,
    alt_submit,
    simple_submit,
)

app_name = 'gestion_achats'

urlpatterns = [
    # ========================================
    # DASHBOARD
    # ========================================
    path('', dashboard_views.dashboard, name='dashboard'),

    # ========================================
    # DEMANDES D'ACHAT
    # ========================================
    path('demandes/', demande_views.demande_liste, name='demande_liste'),
    path('demandes/mes-demandes/', demande_views.mes_demandes, name='mes_demandes'),
    path('demandes/a-valider/', demande_views.demandes_a_valider, name='demandes_a_valider'),
    path('demandes/create/', demande_views.demande_create, name='demande_create'),
    path('demandes/<uuid:pk>/', demande_views.demande_detail, name='demande_detail'),
    path('demandes/<uuid:pk>/update/', demande_views.demande_update, name='demande_update'),
    path('demandes/<uuid:pk>/delete/', demande_views.demande_delete, name='demande_delete'),
    path('demandes/<uuid:pk>/ligne/create/', demande_views.demande_ligne_create, name='demande_ligne_create'),
    path('demandes/<uuid:pk>/ligne/<int:ligne_pk>/update/', demande_views.demande_ligne_update, name='demande_ligne_update'),
    path('demandes/<uuid:pk>/ligne/<int:ligne_pk>/delete/', demande_views.demande_ligne_delete, name='demande_ligne_delete'),
    # Note: Utilisation de simple_submit - version ultra-simplifiée qui fonctionne à coup sûr
    path('demandes/<uuid:pk>/submit/', simple_submit.simple_demande_submit, name='demande_submit'),
    path('demandes/<uuid:pk>/validate-n1/', demande_views.demande_validate_n1, name='demande_validate_n1'),
    path('demandes/<uuid:pk>/validate-n2/', demande_views.demande_validate_n2, name='demande_validate_n2'),
    path('demandes/<uuid:pk>/refuse/', demande_views.demande_refuse, name='demande_refuse'),
    path('demandes/<uuid:pk>/cancel/', demande_views.demande_cancel, name='demande_cancel'),

    # ========================================
    # BONS DE COMMANDE
    # ========================================
    path('bons-commande/', bon_commande_views.bon_commande_liste, name='bon_commande_liste'),
    path('bons-commande/<uuid:pk>/', bon_commande_views.bon_commande_detail, name='bon_commande_detail'),
    path('bons-commande/create-from-demande/<uuid:demande_pk>/', bon_commande_views.bon_commande_create_from_demande, name='bon_commande_create_from_demande'),
    path('bons-commande/<uuid:pk>/emit/', bon_commande_views.bon_commande_emit, name='bon_commande_emit'),
    path('bons-commande/<uuid:pk>/send/', bon_commande_views.bon_commande_send, name='bon_commande_send'),
    path('bons-commande/<uuid:pk>/pdf/', bon_commande_views.bon_commande_pdf, name='bon_commande_pdf'),

    # Lignes de bons de commande
    path('bons-commande/<uuid:pk>/lignes/create/', bon_commande_views.ligne_bc_create, name='ligne_bc_create'),
    path('bons-commande/<uuid:pk>/lignes/<int:ligne_pk>/update/', bon_commande_views.ligne_bc_update, name='ligne_bc_update'),
    path('bons-commande/<uuid:pk>/lignes/<int:ligne_pk>/delete/', bon_commande_views.ligne_bc_delete, name='ligne_bc_delete'),

    # ========================================
    # FOURNISSEURS
    # ========================================
    path('fournisseurs/', fournisseur_views.fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/create/', fournisseur_views.fournisseur_create, name='fournisseur_create'),
    path('fournisseurs/<uuid:pk>/', fournisseur_views.fournisseur_detail, name='fournisseur_detail'),
    path('fournisseurs/<uuid:pk>/update/', fournisseur_views.fournisseur_update, name='fournisseur_update'),
    path('fournisseurs/<uuid:pk>/delete/', fournisseur_views.fournisseur_delete, name='fournisseur_delete'),
    path('fournisseurs/<uuid:pk>/suspend/', fournisseur_views.fournisseur_suspend, name='fournisseur_suspend'),
    path('fournisseurs/<uuid:pk>/reactivate/', fournisseur_views.fournisseur_reactivate, name='fournisseur_reactivate'),
    path('fournisseurs/<uuid:pk>/evaluer/', fournisseur_views.evaluer_fournisseur, name='fournisseur_evaluer'),

    # ========================================
    # RÉCEPTIONS
    # ========================================
    path('receptions/', reception_views.reception_list, name='reception_list'),
    path('receptions/en-attente/', reception_views.receptions_en_attente, name='receptions_en_attente'),
    path('receptions/create/<uuid:bc_pk>/', reception_views.reception_create, name='reception_create'),
    path('receptions/<uuid:pk>/', reception_views.reception_detail, name='reception_detail'),
    path('receptions/<uuid:pk>/update/', reception_views.reception_update, name='reception_update'),
    path('receptions/<uuid:pk>/validate/', reception_views.valider_reception, name='reception_validate'),
    path('receptions/<uuid:pk>/cancel/', reception_views.annuler_reception, name='reception_cancel'),

    # ========================================
    # BONS DE RETOUR
    # ========================================
    path('bons-retour/', bon_retour_views.bon_retour_list, name='bon_retour_list'),
    path('bons-retour/create-from-reception/<uuid:reception_pk>/', bon_retour_views.bon_retour_create_from_reception, name='bon_retour_create_from_reception'),
    path('bons-retour/<uuid:pk>/', bon_retour_views.bon_retour_detail, name='bon_retour_detail'),
    path('bons-retour/<uuid:pk>/emit/', bon_retour_views.bon_retour_emit, name='bon_retour_emit'),
    path('bons-retour/<uuid:pk>/send/', bon_retour_views.bon_retour_send, name='bon_retour_send'),
    path('bons-retour/<uuid:pk>/receive/', bon_retour_views.bon_retour_receive, name='bon_retour_receive'),

    # ========================================
    # CATALOGUE (Articles et Catégories)
    # ========================================
    # Articles
    path('catalogue/articles/', catalogue_views.article_list, name='article_list'),
    path('catalogue/articles/create/', catalogue_views.article_create, name='article_create'),
    path('catalogue/articles/<uuid:pk>/', catalogue_views.article_detail, name='article_detail'),
    path('catalogue/articles/<uuid:pk>/update/', catalogue_views.article_update, name='article_update'),
    path('catalogue/articles/<uuid:pk>/delete/', catalogue_views.article_delete, name='article_delete'),
    path('catalogue/articles/<uuid:pk>/desactiver/', catalogue_views.article_desactiver, name='article_desactiver'),
    path('catalogue/articles/<uuid:pk>/reactiver/', catalogue_views.article_reactiver, name='article_reactiver'),

    # Catégories
    path('catalogue/categories/', catalogue_views.categorie_list, name='categorie_list'),
    path('catalogue/categories/create/', catalogue_views.categorie_create, name='categorie_create'),
    path('catalogue/categories/<uuid:pk>/update/', catalogue_views.categorie_update, name='categorie_update'),
    path('catalogue/categories/<uuid:pk>/delete/', catalogue_views.categorie_delete, name='categorie_delete'),

    # ========================================
    # BUDGETS
    # ========================================
    path('budgets/', budget_views.budget_list, name='budget_list'),
    path('budgets/synthese/', budget_views.synthese_budgets, name='synthese_budgets'),
    path('budgets/create/', budget_views.budget_create, name='budget_create'),
    path('budgets/<uuid:pk>/', budget_views.budget_detail, name='budget_detail'),
    path('budgets/<uuid:pk>/update/', budget_views.budget_update, name='budget_update'),
    path('budgets/<uuid:pk>/historique/', budget_views.budget_historique, name='budget_historique'),

    # ========================================
    # API AJAX
    # ========================================
    path('api/articles/recherche/', catalogue_views.recherche_articles_ajax, name='api_recherche_articles'),
    path('api/fournisseurs/article/<uuid:article_pk>/', fournisseur_views.fournisseurs_pour_article_ajax, name='api_fournisseurs_article'),
    path('api/budgets/alertes/', budget_views.budgets_en_alerte_ajax, name='api_budgets_alertes'),

    # ========================================
    # PARAMÈTRES
    # ========================================
    path('parametres/', parametres_views.parametres_gac, name='parametres_gac'),

    # ========================================
    # DEBUG (À SUPPRIMER EN PRODUCTION)
    # ========================================
    path('debug/user-info/', debug_views.debug_user_info, name='debug_user_info'),
    path('debug/validateurs/', diagnostic_validateurs.diagnostic_validateurs, name='diagnostic_validateurs'),
    path('debug/test-permissions/<uuid:pk>/', test_permissions.test_submit_permission, name='test_submit_permission'),
    path('debug/alt-submit/<uuid:pk>/', alt_submit.alt_demande_submit, name='alt_demande_submit'),
]

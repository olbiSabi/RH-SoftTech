# gestion_temps_activite/urls.py

from django.urls import path
from . import views

app_name = 'gestion_temps_activite'

urlpatterns = [
    # ==================== DASHBOARD ====================
    path('', views.dashboard, name='dashboard'),

    # ==================== CLIENTS (ZDCL) ====================
    path('clients/', views.client_liste, name='client_liste'),
    path('clients/nouveau/', views.client_create, name='client_create'),
    path('clients/<uuid:pk>/', views.client_detail, name='client_detail'),
    path('clients/<uuid:pk>/modifier/', views.client_update, name='client_update'),
    path('clients/<uuid:pk>/supprimer/', views.client_delete, name='client_delete'),

    # ==================== TYPES D'ACTIVITÉS (ZDAC) ====================
    path('activites/', views.activite_liste, name='activite_liste'),
    path('activites/nouveau/', views.activite_create, name='activite_create'),
    path('activites/<uuid:pk>/modifier/', views.activite_update, name='activite_update'),
    path('activites/<uuid:pk>/supprimer/', views.activite_delete, name='activite_delete'),

    # ==================== PROJETS (ZDPJ) ====================
    path('projets/', views.projet_liste, name='projet_liste'),
    path('projets/nouveau/', views.projet_create, name='projet_create'),
    path('projets/<uuid:pk>/', views.projet_detail, name='projet_detail'),
    path('projets/<uuid:pk>/modifier/', views.projet_update, name='projet_update'),
    path('projets/<uuid:pk>/supprimer/', views.projet_delete, name='projet_delete'),

    # ==================== TÂCHES (ZDTA) ====================
    path('taches/', views.tache_liste, name='tache_liste'),
    path('taches/nouveau/', views.tache_create, name='tache_create'),
    path('taches/<uuid:pk>/', views.tache_detail, name='tache_detail'),
    path('taches/<uuid:pk>/modifier/', views.tache_update, name='tache_update'),
    path('taches/<uuid:pk>/supprimer/', views.tache_delete, name='tache_delete'),

    # ==================== DOCUMENTS (ZDDO) ====================
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<uuid:pk>/supprimer/', views.document_delete, name='document_delete'),

    # ==================== IMPUTATIONS TEMPS (ZDIT) ====================
    path('imputations/', views.imputation_liste, name='imputation_liste'),
    path('imputations/mes-temps/', views.imputation_mes_temps, name='imputation_mes_temps'),
    path('imputations/nouveau/', views.imputation_create, name='imputation_create'),
    path('imputations/<uuid:pk>/modifier/', views.imputation_update, name='imputation_update'),
    path('imputations/<uuid:pk>/supprimer/', views.imputation_delete, name='imputation_delete'),
    path('imputations/export/', views.imputation_export_excel, name='imputation_export_excel'),

    # Validation des imputations
    path('imputations/validation/', views.imputation_validation, name='imputation_validation'),
    path('imputations/<uuid:pk>/valider/', views.imputation_valider, name='imputation_valider'),
    path('imputations/<uuid:pk>/rejeter/', views.imputation_rejeter, name='imputation_rejeter'),

    # ==================== API/AJAX ====================
    path('api/projet/<uuid:projet_id>/taches/', views.api_taches_par_projet, name='api_taches_par_projet'),
    path('api/activites/en-vigueur/', views.api_activites_en_vigueur, name='api_activites_en_vigueur'),

    # Commentaires
    path('commentaires/<uuid:tache_pk>/ajouter/', views.commentaire_ajouter, name='commentaire_ajouter'),
    path('commentaires/<uuid:commentaire_pk>/repondre/', views.commentaire_repondre, name='commentaire_repondre'),
    path('commentaires/<uuid:pk>/modifier/', views.commentaire_modifier, name='commentaire_modifier'),
    path('commentaires/<uuid:pk>/supprimer/', views.commentaire_supprimer, name='commentaire_supprimer'),
    path('api/commentaires/mentions/', views.commentaire_mentions, name='commentaire_mentions'),
    # gestion_temps_activite/urls.py
    path('commentaires/<uuid:tache_pk>/ajouter/', views.commentaire_ajouter, name='commentaire_ajouter'),
]
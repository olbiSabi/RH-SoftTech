# gestion_temps_activite/views.py
"""
Module de vues pour Gestion Temps et Activités.

Ce fichier réexporte les vues depuis les modules pour maintenir
la compatibilité avec urls.py et les imports existants.

La nouvelle architecture modulaire se trouve dans:
- gestion_temps_activite/views/client_views.py
- gestion_temps_activite/views/activite_views.py
- gestion_temps_activite/views/projet_views.py
- gestion_temps_activite/views/tache_views.py
- gestion_temps_activite/views/document_views.py
- gestion_temps_activite/views/imputation_views.py
- gestion_temps_activite/views/commentaire_views.py
- gestion_temps_activite/views/notification_views.py
- gestion_temps_activite/views/dashboard_views.py
- gestion_temps_activite/views/api_views.py
"""

# Réexportation depuis les modules
from .views import (
    # Client
    client_liste,
    client_detail,
    client_create,
    client_update,
    client_delete,
    # Activite
    activite_liste,
    activite_create,
    activite_update,
    activite_delete,
    # Projet
    projet_liste,
    projet_detail,
    projet_create,
    projet_update,
    projet_delete,
    # Tache
    tache_liste,
    tache_detail,
    tache_create,
    tache_update,
    tache_delete,
    # Document
    document_upload,
    document_delete,
    # Imputation
    imputation_liste,
    imputation_mes_temps,
    imputation_create,
    imputation_update,
    imputation_delete,
    imputation_validation,
    imputation_valider,
    imputation_rejeter,
    imputation_export_excel,
    # Commentaire
    commentaire_ajouter,
    commentaire_repondre,
    commentaire_modifier,
    commentaire_supprimer,
    commentaire_mentions,
    # Notification
    notification_tache_detail,
    toutes_notifications_gta,
    marquer_notification_gta_lue,
    marquer_toutes_notifications_gta_lues,
    # Dashboard
    dashboard,
    # API
    api_taches_par_projet,
    api_activites_en_vigueur,
)

__all__ = [
    # Client
    'client_liste',
    'client_detail',
    'client_create',
    'client_update',
    'client_delete',
    # Activite
    'activite_liste',
    'activite_create',
    'activite_update',
    'activite_delete',
    # Projet
    'projet_liste',
    'projet_detail',
    'projet_create',
    'projet_update',
    'projet_delete',
    # Tache
    'tache_liste',
    'tache_detail',
    'tache_create',
    'tache_update',
    'tache_delete',
    # Document
    'document_upload',
    'document_delete',
    # Imputation
    'imputation_liste',
    'imputation_mes_temps',
    'imputation_create',
    'imputation_update',
    'imputation_delete',
    'imputation_validation',
    'imputation_valider',
    'imputation_rejeter',
    'imputation_export_excel',
    # Commentaire
    'commentaire_ajouter',
    'commentaire_repondre',
    'commentaire_modifier',
    'commentaire_supprimer',
    'commentaire_mentions',
    # Notification
    'notification_tache_detail',
    'toutes_notifications_gta',
    'marquer_notification_gta_lue',
    'marquer_toutes_notifications_gta_lues',
    # Dashboard
    'dashboard',
    # API
    'api_taches_par_projet',
    'api_activites_en_vigueur',
]

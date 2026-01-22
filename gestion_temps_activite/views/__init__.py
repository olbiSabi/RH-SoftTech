# gestion_temps_activite/views/__init__.py
"""
Vues pour l'application Gestion Temps et Activités.

Structure modulaire:
- client_views.py : Vues CRUD clients
- activite_views.py : Vues CRUD types d'activités
- projet_views.py : Vues CRUD projets
- tache_views.py : Vues CRUD tâches
- document_views.py : Vues upload/suppression documents
- imputation_views.py : Vues gestion temps
- commentaire_views.py : Vues commentaires
- notification_views.py : Vues notifications GTA
- dashboard_views.py : Vue dashboard
- api_views.py : Endpoints AJAX/API
"""

from .client_views import (
    client_liste,
    client_detail,
    client_create,
    client_update,
    client_delete,
)

from .activite_views import (
    activite_liste,
    activite_create,
    activite_update,
    activite_delete,
)

from .projet_views import (
    projet_liste,
    projet_detail,
    projet_create,
    projet_update,
    projet_delete,
)

from .tache_views import (
    tache_liste,
    tache_detail,
    tache_create,
    tache_update,
    tache_delete,
    detecter_changements,
)

from .document_views import (
    document_upload,
    document_delete,
)

from .imputation_views import (
    imputation_liste,
    imputation_mes_temps,
    imputation_create,
    imputation_update,
    imputation_delete,
    imputation_validation,
    imputation_valider,
    imputation_rejeter,
    imputation_export_excel,
)

from .commentaire_views import (
    commentaire_ajouter,
    commentaire_repondre,
    commentaire_modifier,
    commentaire_supprimer,
    commentaire_mentions,
)

from .notification_views import (
    notification_tache_detail,
    toutes_notifications_gta,
    marquer_notification_gta_lue,
    marquer_toutes_notifications_gta_lues,
    notifier_changement_statut,
    notifier_nouvelle_tache,
    notifier_reassignation_tache,
    notifier_modification_tache,
    notifier_changement_statut_tache,
    notifier_nouveau_commentaire,
    notifier_echeance_tache_proche,
)

from .dashboard_views import dashboard

from .api_views import (
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
    'detecter_changements',
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
    'notifier_changement_statut',
    'notifier_nouvelle_tache',
    'notifier_reassignation_tache',
    'notifier_modification_tache',
    'notifier_changement_statut_tache',
    'notifier_nouveau_commentaire',
    'notifier_echeance_tache_proche',
    # Dashboard
    'dashboard',
    # API
    'api_taches_par_projet',
    'api_activites_en_vigueur',
]

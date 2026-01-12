# gestion_temps_activite/context_processors.py

def gta_permissions(request):
    """
    Context processor pour les permissions GTA
    Utilise les méthodes utilitaires du modèle ZY00
    """
    permissions = {
        'can_access_gta': False,
        'can_manage_clients': False,
        'can_manage_activites': False,
        'can_manage_projets': False,
        'can_manage_taches': False,
        'can_view_taches': False,
        'can_view_mes_temps': False,
        'can_create_imputation': False,
        'can_view_all_imputations': False,
        'can_validate_imputations': False,
        'can_view_documents': False,
    }

    # Si l'utilisateur n'est pas connecté ou n'a pas d'employé
    if not request.user.is_authenticated or not hasattr(request.user, 'employe'):
        return {'gta_permissions': permissions}

    employe = request.user.employe

    # ✅ Utiliser les méthodes utilitaires du modèle
    permissions['can_access_gta'] = True
    permissions['can_manage_clients'] = employe.peut_gerer_clients()
    permissions['can_manage_activites'] = employe.peut_gerer_activites()
    permissions['can_manage_projets'] = employe.peut_gerer_projets()
    permissions['can_manage_taches'] = employe.peut_gerer_taches()
    permissions['can_view_taches'] = employe.peut_voir_taches()
    permissions['can_view_mes_temps'] = True  # Tous les employés
    permissions['can_create_imputation'] = employe.peut_creer_imputation()
    permissions['can_view_all_imputations'] = employe.peut_voir_toutes_imputations()
    permissions['can_validate_imputations'] = employe.peut_valider_imputations()
    permissions['can_view_documents'] = employe.peut_uploader_documents()

    return {'gta_permissions': permissions}
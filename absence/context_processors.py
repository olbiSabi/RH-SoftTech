"""
Context processor pour les notifications de demandes d'absence
Application: absence
Système HR_ONIAN
"""

from absence.models import ZDDA


def notifications_absence(request):
    """
    Context processor pour afficher les notifications de demandes en attente
    dans tous les templates
    """
    context = {
        'demandes_en_attente_count': 0,
        'demandes_en_attente': [],
        'demandes_rh_count': 0,
        'demandes_rh': [],
    }

    # Vérifier si l'utilisateur est connecté
    if not request.user.is_authenticated:
        return context

    try:
        # Récupérer l'employé connecté
        employe = request.user.employe

        # Vérifier si l'employé est manager
        # Utiliser la méthode get_manager_responsable() qui existe déjà sur ZY00
        # Pour trouver les demandes dont l'employé connecté est le manager
        demandes_en_attente = ZDDA.objects.filter(
            statut='EN_ATTENTE'
        ).select_related('employe', 'type_absence')

        # Filtrer pour ne garder que les demandes où l'employé connecté est le manager
        demandes_manager = []
        for demande in demandes_en_attente:
            try:
                manager_responsable = demande.employe.get_manager_responsable()
                if manager_responsable and manager_responsable.pk == employe.pk:
                    demandes_manager.append(demande)
            except:
                pass

        if demandes_manager:
            context['demandes_en_attente_count'] = len(demandes_manager)
            context['demandes_en_attente'] = demandes_manager[:10]  # Max 10 notifications

        # Vérifier si l'utilisateur est RH (staff ou superuser)
        if request.user.is_staff or request.user.is_superuser:
            # Compter les demandes validées par le manager en attente de validation RH
            demandes_rh = ZDDA.objects.filter(
                statut='VALIDEE_MANAGER'
            ).select_related('employe', 'type_absence').order_by('-created_at')[:10]

            context['demandes_rh_count'] = demandes_rh.count()
            context['demandes_rh'] = demandes_rh

    except AttributeError:
        # L'utilisateur n'a pas d'employé associé
        pass
    except Exception as e:
        # Autre erreur, ne pas bloquer l'application
        pass

    return context
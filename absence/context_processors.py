"""
Context processor basé sur les rôles
À remplacer dans absence/context_processors.py
"""
from .models import ZANO


def notifications(request):
    """Context processor pour les notifications"""
    context = {
        'notifications_non_lues': [],
        'nb_notifications_non_lues': 0,
    }

    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # Trouver l'employé correspondant à l'utilisateur
            if hasattr(request.user, 'employe'):
                employe = request.user.employe

                # Récupérer les notifications non lues
                notifications_non_lues = ZANO.objects.filter(
                    destinataire=employe,
                    lue=False
                ).select_related('demande_absence', 'demande_absence__type_absence').order_by('-date_creation')[:10]

                # Compter le nombre total de notifications non lues
                nb_notifications_non_lues = ZANO.objects.filter(
                    destinataire=employe,
                    lue=False
                ).count()

                context = {
                    'notifications_non_lues': notifications_non_lues,
                    'nb_notifications_non_lues': nb_notifications_non_lues,
                }
        except Exception as e:
            print(f"Erreur context processor notifications: {e}")

    return context
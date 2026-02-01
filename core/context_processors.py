# core/context_processors.py
from absence.models import NotificationAbsence


def notifications_unifiees(request):
    """
    Context processor unifié pour toutes les notifications.
    Retourne une liste unique de notifications triées par date.
    """
    context = {
        'notifications': [],
        'notifications_count': 0,
    }

    if request.user.is_authenticated and hasattr(request.user, 'employe'):
        employe = request.user.employe

        # Récupérer toutes les notifications non lues, triées par date
        notifications_non_lues = NotificationAbsence.get_non_lues(employe).order_by('-date_creation')[:10]

        # Compter le total
        total_non_lues = NotificationAbsence.count_non_lues(employe)

        context.update({
            'notifications': notifications_non_lues,
            'notifications_count': total_non_lues,
        })

    return context
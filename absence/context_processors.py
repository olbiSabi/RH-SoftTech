# absence/context_processors.py
from absence.models import NotificationAbsence


def notifications_absences(request):
    """
    Context processor pour les notifications d'absence (version compatible)
    """
    if request.user.is_authenticated and hasattr(request.user, 'employe'):
        notifications_non_lues = NotificationAbsence.get_notifications_absences(
            request.user.employe
        ).filter(lue=False)

        return {
            'notifications_absences': notifications_non_lues[:5],
            'notifications_absences_count': notifications_non_lues.count(),
            # ⚠️ Ces clés ne seront utilisées que si le context processor unifié n'est pas activé
        }

    return {
        'notifications_absences': [],
        'notifications_absences_count': 0
    }
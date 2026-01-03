from .models import NotificationAbsence


def notifications_absences(request):
    """
    Context processor pour ajouter les notifications d'absence
    dans tous les templates
    """
    if request.user.is_authenticated and hasattr(request.user, 'employe'):
        notifications_non_lues = NotificationAbsence.get_non_lues(request.user.employe)
        count_non_lues = notifications_non_lues.count()

        return {
            'notifications_absences': notifications_non_lues[:5],  # 5 dernières
            'notifications_absences_count': count_non_lues
        }

    return {
        'notifications_absences': [],
        'notifications_absences_count': 0
    }
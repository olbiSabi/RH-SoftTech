# core/context_processors.py (ou votre app principale)
from absence.models import NotificationAbsence


def notifications_unifiees(request):
    """
    Context processor unifié pour toutes les notifications
    Combine les notifications d'absences et de tâches GTA
    """
    context = {
        'notifications_absences': [],
        'notifications_absences_count': 0,
        'notifications_gta': [],
        'notifications_gta_count': 0,
        'notifications_total_count': 0,
    }

    if request.user.is_authenticated and hasattr(request.user, 'employe'):
        employe = request.user.employe

        # 1. Notifications d'absences
        notifications_absences = NotificationAbsence.get_notifications_absences(employe)
        notifications_absences_non_lues = notifications_absences.filter(lue=False)

        # 2. Notifications GTA
        notifications_gta = NotificationAbsence.get_notifications_taches(employe)
        notifications_gta_non_lues = notifications_gta.filter(lue=False)

        # 3. Totaux
        total_non_lues = NotificationAbsence.count_non_lues(employe)

        context.update({
            'notifications_absences': notifications_absences_non_lues[:5],  # 5 dernières
            'notifications_absences_count': notifications_absences_non_lues.count(),
            'notifications_gta': notifications_gta_non_lues[:5],  # 5 dernières
            'notifications_gta_count': notifications_gta_non_lues.count(),
            'notifications_total_count': total_non_lues,
        })

    return context
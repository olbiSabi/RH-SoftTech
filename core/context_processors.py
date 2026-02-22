# core/context_processors.py
from absence.models import NotificationAbsence


def entreprise_context(request):
    """
    Rend l'entreprise et son logo disponibles dans tous les templates.
    """
    context = {
        'entreprise_logo_url': None,
        'entreprise_nom': '',
    }

    try:
        from entreprise.models import Entreprise
        entreprise = Entreprise.objects.first()
        if entreprise:
            context['entreprise_nom'] = entreprise.nom
            if entreprise.logo:
                context['entreprise_logo_url'] = entreprise.logo.url
    except Exception:
        pass

    return context


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
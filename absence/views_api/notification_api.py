# absence/views_api/notification_api.py
"""
API et vues pour la gestion des notifications d'absence.
"""
import logging

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from absence.models import NotificationAbsence

logger = logging.getLogger(__name__)


@login_required
def notification_detail(request, id):
    """Marquer une notification comme lue et rediriger selon le CONTEXTE"""
    notification = get_object_or_404(
        NotificationAbsence,
        id=id,
        destinataire=request.user.employe
    )

    notification.marquer_comme_lue()
    contexte = notification.contexte

    if contexte == 'MANAGER':
        return redirect('absence:validation_manager')
    elif contexte == 'RH':
        return redirect('absence:validation_rh')
    else:
        return redirect('absence:liste_absences')


@login_required
def marquer_toutes_lues(request):
    """Marquer toutes les notifications comme lues"""
    NotificationAbsence.objects.filter(
        destinataire=request.user.employe,
        lue=False
    ).update(lue=True, date_lecture=timezone.now())

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


@login_required
def toutes_notifications(request):
    """Page listant toutes les notifications avec filtres"""
    notifications = NotificationAbsence.objects.filter(
        destinataire=request.user.employe
    ).select_related('absence', 'absence__employe', 'absence__type_absence').order_by('-date_creation')

    statut_filter = request.GET.get('statut', '')
    type_filter = request.GET.get('type', '')

    if statut_filter == 'non_lues':
        notifications = notifications.filter(lue=False)
    elif statut_filter == 'lues':
        notifications = notifications.filter(lue=True)

    if type_filter:
        notifications = notifications.filter(type_notification=type_filter)

    notifications_count = NotificationAbsence.objects.filter(
        destinataire=request.user.employe,
        lue=False
    ).count()

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'notifications_count': notifications_count,
        'title': 'Toutes les notifications'
    }

    return render(request, 'absence/toutes_notifications.html', context)


@login_required
def notification_counts(request):
    """Retourne le compte des notifications non lues"""
    try:
        user_employe = request.user.employe

        notifications_non_lues = NotificationAbsence.objects.filter(
            destinataire=user_employe,
            lue=False
        ).count()

        return JsonResponse({
            'all': notifications_non_lues,
            'pending': notifications_non_lues,
            'approved': 0,
            'rejected': 0,
            'total': notifications_non_lues
        })

    except Exception as e:
        return JsonResponse({
            'all': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'total': 0
        })


@login_required
def marquer_notification_lue(request, notification_id):
    """Marque une notification comme lue via AJAX"""
    try:
        notification = NotificationAbsence.objects.get(
            id=notification_id,
            destinataire=request.user.employe
        )

        notification.marquer_comme_lue()

        return JsonResponse({'success': True})

    except NotificationAbsence.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

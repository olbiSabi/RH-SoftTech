# gestion_temps_activite/views/notification_views.py
"""Vues et fonctions de notification pour le module GTA."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from absence.models import NotificationAbsence
from gestion_temps_activite.services import NotificationService


@login_required
def notification_tache_detail(request, notification_id):
    """Afficher une notification et rediriger vers la tâche."""
    notification = get_object_or_404(NotificationAbsence, pk=notification_id)

    # Marquer comme lue
    if not notification.lue:
        notification.lue = True
        notification.save()

    # Rediriger vers la tâche si disponible
    if notification.tache:
        return redirect('gestion_temps_activite:tache_detail', pk=notification.tache.pk)

    return redirect('gestion_temps_activite:dashboard')


@login_required
def toutes_notifications_gta(request):
    """Liste de toutes les notifications GTA de l'utilisateur."""
    if not hasattr(request.user, 'employe'):
        messages.error(request, "Vous devez avoir un profil employé.")
        return redirect('gestion_temps_activite:dashboard')

    employe = request.user.employe

    notifications = NotificationAbsence.objects.filter(
        destinataire=employe,
        contexte='GTA'
    ).order_by('-date_creation')

    # Filtres
    filtre_lue = request.GET.get('lue', '')
    if filtre_lue:
        notifications = notifications.filter(lue=(filtre_lue == 'True'))

    filtre_type = request.GET.get('type', '')
    if filtre_type:
        notifications = notifications.filter(type_notification=filtre_type)

    context = {
        'notifications': notifications,
        'total_non_lues': notifications.filter(lue=False).count(),
        'filtre_lue': filtre_lue,
        'filtre_type': filtre_type
    }

    return render(request, 'gestion_temps_activite/notifications_liste.html', context)


@login_required
def marquer_notification_gta_lue(request, notification_id):
    """Marquer une notification comme lue."""
    notification = get_object_or_404(NotificationAbsence, pk=notification_id)

    if hasattr(request.user, 'employe') and notification.destinataire == request.user.employe:
        notification.lue = True
        notification.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

    return redirect('gestion_temps_activite:toutes_notifications_gta')


@login_required
def marquer_toutes_notifications_gta_lues(request):
    """Marquer toutes les notifications GTA comme lues."""
    if not hasattr(request.user, 'employe'):
        return redirect('gestion_temps_activite:dashboard')

    employe = request.user.employe

    NotificationAbsence.objects.filter(
        destinataire=employe,
        contexte='GTA',
        lue=False
    ).update(lue=True)

    messages.success(request, "Toutes les notifications ont été marquées comme lues.")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('gestion_temps_activite:toutes_notifications_gta')


# =============================================================================
# FONCTIONS UTILITAIRES DE NOTIFICATION (appelées par les autres vues)
# =============================================================================

def notifier_changement_statut(notification):
    """Wrapper pour la compatibilité."""
    pass  # Remplacé par notifier_changement_statut_tache


def notifier_nouvelle_tache(tache, createur):
    """Notifier l'assigné d'une nouvelle tâche."""
    return NotificationService.notifier_nouvelle_tache(tache, createur)


def notifier_reassignation_tache(tache, ancien_assignee, nouvel_assignee):
    """Notifier lors d'une réassignation de tâche."""
    return NotificationService.notifier_reassignation(tache, ancien_assignee, nouvel_assignee)


def notifier_modification_tache(tache, employe_modifiant, changements):
    """Notifier l'assigné d'une modification de tâche."""
    return NotificationService.notifier_modification(tache, employe_modifiant, changements)


def notifier_changement_statut_tache(tache, ancien_statut, nouveau_statut):
    """Notifier le changement de statut d'une tâche."""
    return NotificationService.notifier_changement_statut(tache, ancien_statut, nouveau_statut)


def notifier_nouveau_commentaire(commentaire, auteur):
    """Notifier les personnes concernées par un nouveau commentaire."""
    destinataires = NotificationService.get_destinataires_commentaire(commentaire, auteur)
    return NotificationService.notifier_commentaire(commentaire, destinataires)


def notifier_echeance_tache_proche(tache, jours_restants):
    """Notifier que l'échéance d'une tâche approche."""
    return NotificationService.notifier_echeance_proche(tache, jours_restants)

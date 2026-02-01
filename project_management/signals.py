"""
Signaux Django pour le module Project Management.
Gère les notifications automatiques lors des événements clés.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import JRTicket, JRProject, JRCommentaire
from .services.notification_service import NotificationService


# ============================================================================
# STOCKAGE TEMPORAIRE DES ANCIENNES VALEURS
# ============================================================================

# Dictionnaire pour stocker les anciennes valeurs avant modification
_ticket_old_values = {}
_project_old_values = {}


# ============================================================================
# SIGNAUX POUR LES TICKETS
# ============================================================================

@receiver(pre_save, sender=JRTicket)
def ticket_pre_save(sender, instance, **kwargs):
    """
    Capture les valeurs avant la sauvegarde du ticket.
    """
    if instance.pk:
        try:
            old_instance = JRTicket.objects.get(pk=instance.pk)
            _ticket_old_values[instance.pk] = {
                'statut': old_instance.statut,
                'assigne': old_instance.assigne,
            }
        except JRTicket.DoesNotExist:
            pass


@receiver(post_save, sender=JRTicket)
def ticket_post_save(sender, instance, created, **kwargs):
    """
    Déclenche les notifications après sauvegarde d'un ticket.
    """
    if created:
        # Nouveau ticket - notifier l'assigné s'il y en a un
        if instance.assigne:
            NotificationService.notifier_assignation_ticket(instance)
    else:
        # Modification d'un ticket existant
        old_values = _ticket_old_values.pop(instance.pk, None)

        if old_values:
            # Vérifier si le statut a changé
            if old_values['statut'] != instance.statut:
                NotificationService.notifier_changement_statut_ticket(
                    instance,
                    old_values['statut'],
                    instance.statut
                )

            # Vérifier si l'assigné a changé
            if old_values['assigne'] != instance.assigne:
                NotificationService.notifier_assignation_ticket(
                    instance,
                    ancien_assigne=old_values['assigne']
                )


# ============================================================================
# SIGNAUX POUR LES PROJETS
# ============================================================================

@receiver(pre_save, sender=JRProject)
def project_pre_save(sender, instance, **kwargs):
    """
    Capture les valeurs avant la sauvegarde du projet.
    """
    if instance.pk:
        try:
            old_instance = JRProject.objects.get(pk=instance.pk)
            _project_old_values[instance.pk] = {
                'statut': old_instance.statut,
                'chef_projet': old_instance.chef_projet,
            }
        except JRProject.DoesNotExist:
            pass


@receiver(post_save, sender=JRProject)
def project_post_save(sender, instance, created, **kwargs):
    """
    Déclenche les notifications après sauvegarde d'un projet.
    """
    if created:
        # Nouveau projet - notifier le chef de projet s'il y en a un
        if instance.chef_projet:
            NotificationService.notifier_assignation_projet(instance, instance.chef_projet)
    else:
        # Modification d'un projet existant
        old_values = _project_old_values.pop(instance.pk, None)

        if old_values:
            # Vérifier si le statut a changé
            if old_values['statut'] != instance.statut:
                NotificationService.notifier_changement_statut_projet(
                    instance,
                    old_values['statut'],
                    instance.statut
                )

            # Vérifier si le chef de projet a changé
            if old_values['chef_projet'] != instance.chef_projet:
                NotificationService.notifier_assignation_projet(
                    instance,
                    instance.chef_projet,
                    ancien_chef_projet=old_values['chef_projet']
                )


# ============================================================================
# SIGNAUX POUR LES COMMENTAIRES
# ============================================================================

@receiver(post_save, sender=JRCommentaire)
def commentaire_post_save(sender, instance, created, **kwargs):
    """
    Déclenche les notifications après création d'un commentaire.
    """
    if created:
        # Nouveau commentaire - notifier l'équipe
        NotificationService.notifier_commentaire_ticket(
            instance,
            auteur=instance.auteur
        )

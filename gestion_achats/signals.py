"""
Signaux pour le module Gestion des Achats & Commandes (GAC).

Ce fichier contient les signaux pour gérer les notifications automatiques
et les actions déclenchées par certains événements.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone

from gestion_achats.models import (
    GACDemandeAchat,
    GACBonCommande,
    GACReception,
    GACBudget,
)
from gestion_achats.services.notification_service import NotificationService
from gestion_achats.services.historique_service import HistoriqueService

import logging

logger = logging.getLogger(__name__)


# ========== Signaux personnalisés ==========

# Signal émis lors d'un changement de statut de demande
demande_statut_change = Signal()

# Signal émis lors d'un changement de statut de BC
bon_commande_statut_change = Signal()

# Signal émis lors d'un changement de statut de réception
reception_statut_change = Signal()

# Signal émis lors d'un dépassement de seuil budgétaire
budget_seuil_atteint = Signal()


# ========== Signaux pour les Demandes d'Achat ==========

@receiver(pre_save, sender=GACDemandeAchat)
def demande_pre_save(sender, instance, **kwargs):
    """
    Avant la sauvegarde d'une demande, stocker l'ancien statut
    pour détecter les changements.
    """
    if instance.pk:
        try:
            old_instance = GACDemandeAchat.objects.get(pk=instance.pk)
            instance._old_statut = old_instance.statut
        except GACDemandeAchat.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=GACDemandeAchat)
def demande_post_save(sender, instance, created, **kwargs):
    """
    Après la sauvegarde d'une demande, gérer les notifications.
    """
    try:
        # Si c'est une nouvelle demande
        if created:
            logger.info(f"Nouvelle demande créée: {instance.numero}")
            # Enregistrer dans l'historique
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CREATION',
                description=f"Demande {instance.numero} créée par {instance.demandeur}",
                utilisateur=instance.demandeur
            )
            return

        # Si le statut a changé
        old_statut = getattr(instance, '_old_statut', None)
        if old_statut and old_statut != instance.statut:
            logger.info(f"Changement de statut de {instance.numero}: {old_statut} → {instance.statut}")

            # Émettre le signal de changement de statut
            demande_statut_change.send(
                sender=sender,
                instance=instance,
                old_statut=old_statut,
                new_statut=instance.statut
            )

            # Enregistrer dans l'historique
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CHANGEMENT_STATUT',
                description=f"Statut changé de {old_statut} à {instance.statut}",
                utilisateur=instance.modifie_par if hasattr(instance, 'modifie_par') else None
            )

            # Gérer les notifications selon le nouveau statut
            _gerer_notifications_demande(instance, old_statut, instance.statut)

    except Exception as e:
        logger.error(f"Erreur dans demande_post_save: {str(e)}")


def _gerer_notifications_demande(demande, old_statut, new_statut):
    """Gère les notifications selon le changement de statut de la demande."""

    # Demande soumise → Notifier validateurs N1
    if new_statut == 'SOUMISE':
        NotificationService.notifier_demande_soumise(demande)

    # Demande validée N1 → Notifier validateurs N2
    elif new_statut == 'VALIDEE_N1':
        NotificationService.notifier_demande_validee_n1(demande)

    # Demande validée N2 → Notifier demandeur et acheteur
    elif new_statut == 'VALIDEE_N2':
        NotificationService.notifier_demande_validee_n2(demande)

    # Demande refusée → Notifier demandeur
    elif new_statut == 'REFUSEE':
        NotificationService.notifier_demande_refusee(demande)

    # Demande annulée → Notifier parties prenantes
    elif new_statut == 'ANNULEE':
        NotificationService.notifier_demande_annulee(demande)

    # Demande convertie en BC → Notifier acheteur
    elif new_statut == 'CONVERTIE_BC':
        NotificationService.notifier_demande_convertie(demande)


# ========== Signaux pour les Bons de Commande ==========

@receiver(pre_save, sender=GACBonCommande)
def bon_commande_pre_save(sender, instance, **kwargs):
    """Avant la sauvegarde d'un BC, stocker l'ancien statut."""
    if instance.pk:
        try:
            old_instance = GACBonCommande.objects.get(pk=instance.pk)
            instance._old_statut = old_instance.statut
        except GACBonCommande.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=GACBonCommande)
def bon_commande_post_save(sender, instance, created, **kwargs):
    """Après la sauvegarde d'un BC, gérer les notifications."""
    try:
        # Si c'est un nouveau BC
        if created:
            logger.info(f"Nouveau bon de commande créé: {instance.numero}")
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CREATION',
                description=f"Bon de commande {instance.numero} créé",
                utilisateur=instance.acheteur
            )
            return

        # Si le statut a changé
        old_statut = getattr(instance, '_old_statut', None)
        if old_statut and old_statut != instance.statut:
            logger.info(f"Changement de statut de {instance.numero}: {old_statut} → {instance.statut}")

            # Émettre le signal
            bon_commande_statut_change.send(
                sender=sender,
                instance=instance,
                old_statut=old_statut,
                new_statut=instance.statut
            )

            # Enregistrer dans l'historique
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CHANGEMENT_STATUT',
                description=f"Statut changé de {old_statut} à {instance.statut}",
                utilisateur=None
            )

            # Gérer les notifications
            _gerer_notifications_bc(instance, old_statut, instance.statut)

    except Exception as e:
        logger.error(f"Erreur dans bon_commande_post_save: {str(e)}")


def _gerer_notifications_bc(bon_commande, old_statut, new_statut):
    """Gère les notifications selon le changement de statut du BC."""

    # BC émis → Notifier acheteur
    if new_statut == 'EMIS':
        NotificationService.notifier_bc_emis(bon_commande)

    # BC envoyé → Notifier fournisseur et réceptionnaire
    elif new_statut == 'ENVOYE':
        NotificationService.notifier_bc_envoye(bon_commande)

    # BC confirmé → Notifier acheteur
    elif new_statut == 'CONFIRME':
        NotificationService.notifier_bc_confirme(bon_commande)

    # Réception partielle → Notifier acheteur
    elif new_statut == 'RECU_PARTIEL':
        NotificationService.notifier_bc_recu_partiel(bon_commande)

    # Réception complète → Notifier acheteur et demandeur
    elif new_statut == 'RECU_COMPLET':
        NotificationService.notifier_bc_recu_complet(bon_commande)

    # BC annulé → Notifier parties prenantes
    elif new_statut == 'ANNULE':
        NotificationService.notifier_bc_annule(bon_commande)


# ========== Signaux pour les Réceptions ==========

@receiver(pre_save, sender=GACReception)
def reception_pre_save(sender, instance, **kwargs):
    """Avant la sauvegarde d'une réception, stocker l'ancien statut."""
    if instance.pk:
        try:
            old_instance = GACReception.objects.get(pk=instance.pk)
            instance._old_statut = old_instance.statut
        except GACReception.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=GACReception)
def reception_post_save(sender, instance, created, **kwargs):
    """Après la sauvegarde d'une réception, gérer les notifications."""
    try:
        # Si c'est une nouvelle réception
        if created:
            logger.info(f"Nouvelle réception créée: {instance.numero}")
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CREATION',
                description=f"Réception {instance.numero} créée",
                utilisateur=instance.receptionnaire
            )
            # Notifier l'acheteur
            NotificationService.notifier_reception_creee(instance)
            return

        # Si le statut a changé
        old_statut = getattr(instance, '_old_statut', None)
        if old_statut and old_statut != instance.statut:
            logger.info(f"Changement de statut de {instance.numero}: {old_statut} → {instance.statut}")

            # Émettre le signal
            reception_statut_change.send(
                sender=sender,
                instance=instance,
                old_statut=old_statut,
                new_statut=instance.statut
            )

            # Enregistrer dans l'historique
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CHANGEMENT_STATUT',
                description=f"Statut changé de {old_statut} à {instance.statut}",
                utilisateur=instance.validateur if instance.validateur else None
            )

            # Gérer les notifications
            _gerer_notifications_reception(instance, old_statut, instance.statut)

    except Exception as e:
        logger.error(f"Erreur dans reception_post_save: {str(e)}")


def _gerer_notifications_reception(reception, old_statut, new_statut):
    """Gère les notifications selon le changement de statut de la réception."""

    # Réception validée → Notifier acheteur et demandeur
    if new_statut == 'VALIDEE':
        NotificationService.notifier_reception_validee(reception)

    # Réception annulée → Notifier parties prenantes
    elif new_statut == 'ANNULEE':
        NotificationService.notifier_reception_annulee(reception)


# ========== Signaux pour les Budgets ==========

@receiver(pre_save, sender=GACBudget)
def budget_pre_save(sender, instance, **kwargs):
    """Avant la sauvegarde d'un budget, stocker les anciens montants."""
    if instance.pk:
        try:
            old_instance = GACBudget.objects.get(pk=instance.pk)
            instance._old_montant_engage = old_instance.montant_engage
            instance._old_montant_commande = old_instance.montant_commande
            instance._old_montant_consomme = old_instance.montant_consomme
            instance._old_taux = old_instance.taux_consommation()
        except GACBudget.DoesNotExist:
            instance._old_montant_engage = 0
            instance._old_montant_commande = 0
            instance._old_montant_consomme = 0
            instance._old_taux = 0
    else:
        instance._old_montant_engage = 0
        instance._old_montant_commande = 0
        instance._old_montant_consomme = 0
        instance._old_taux = 0


@receiver(post_save, sender=GACBudget)
def budget_post_save(sender, instance, created, **kwargs):
    """Après la sauvegarde d'un budget, vérifier les seuils d'alerte."""
    try:
        # Si c'est un nouveau budget
        if created:
            logger.info(f"Nouveau budget créé: {instance.code}")
            HistoriqueService.enregistrer_action(
                objet=instance,
                action='CREATION',
                description=f"Budget {instance.code} créé avec un montant initial de {instance.montant_initial}",
                utilisateur=instance.cree_par
            )
            return

        # Vérifier les seuils d'alerte
        taux_actuel = instance.taux_consommation()
        old_taux = getattr(instance, '_old_taux', 0)

        # Seuil d'alerte 1 franchi
        if taux_actuel >= instance.seuil_alerte_1 and old_taux < instance.seuil_alerte_1:
            if not instance.alerte_1_envoyee:
                logger.warning(f"Seuil d'alerte 1 atteint pour {instance.code}: {taux_actuel}%")
                budget_seuil_atteint.send(
                    sender=sender,
                    instance=instance,
                    niveau=1,
                    taux=taux_actuel
                )
                NotificationService.notifier_budget_seuil_1(instance, taux_actuel)
                instance.alerte_1_envoyee = True
                instance.date_alerte_1 = timezone.now()
                GACBudget.objects.filter(pk=instance.pk).update(
                    alerte_1_envoyee=True,
                    date_alerte_1=timezone.now()
                )

        # Seuil d'alerte 2 franchi
        if taux_actuel >= instance.seuil_alerte_2 and old_taux < instance.seuil_alerte_2:
            if not instance.alerte_2_envoyee:
                logger.error(f"Seuil d'alerte 2 atteint pour {instance.code}: {taux_actuel}%")
                budget_seuil_atteint.send(
                    sender=sender,
                    instance=instance,
                    niveau=2,
                    taux=taux_actuel
                )
                NotificationService.notifier_budget_seuil_2(instance, taux_actuel)
                instance.alerte_2_envoyee = True
                instance.date_alerte_2 = timezone.now()
                GACBudget.objects.filter(pk=instance.pk).update(
                    alerte_2_envoyee=True,
                    date_alerte_2=timezone.now()
                )

        # Enregistrer les changements de montants dans l'historique
        if hasattr(instance, '_old_montant_engage'):
            old_engage = getattr(instance, '_old_montant_engage', 0)
            if old_engage != instance.montant_engage:
                HistoriqueService.enregistrer_action(
                    objet=instance,
                    action='MODIFICATION',
                    description=f"Montant engagé modifié: {old_engage} → {instance.montant_engage}",
                    utilisateur=None
                )

    except Exception as e:
        logger.error(f"Erreur dans budget_post_save: {str(e)}")


# ========== Connexion des signaux personnalisés ==========

@receiver(demande_statut_change)
def handle_demande_statut_change(sender, instance, old_statut, new_statut, **kwargs):
    """Handler pour les changements de statut de demande."""
    logger.info(f"Handler: Demande {instance.numero} - {old_statut} → {new_statut}")


@receiver(bon_commande_statut_change)
def handle_bc_statut_change(sender, instance, old_statut, new_statut, **kwargs):
    """Handler pour les changements de statut de BC."""
    logger.info(f"Handler: BC {instance.numero} - {old_statut} → {new_statut}")


@receiver(reception_statut_change)
def handle_reception_statut_change(sender, instance, old_statut, new_statut, **kwargs):
    """Handler pour les changements de statut de réception."""
    logger.info(f"Handler: Réception {instance.numero} - {old_statut} → {new_statut}")


@receiver(budget_seuil_atteint)
def handle_budget_seuil(sender, instance, niveau, taux, **kwargs):
    """Handler pour les dépassements de seuil budgétaire."""
    logger.warning(f"Handler: Budget {instance.code} - Seuil {niveau} atteint ({taux}%)")

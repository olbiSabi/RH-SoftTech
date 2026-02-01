"""
Signaux Django pour le module Absence.
Gère les notifications automatiques et la mise à jour des soldes.
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from .models import ZDDA, ZANO
from .views import mettre_a_jour_solde_conges

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ZDDA)
def gerer_notifications_demande_absence(sender, instance, created, **kwargs):
    """
    Signal pour gérer les notifications lors des changements de statut
    """
    logger.debug(
        f"Signal déclenché pour demande: {instance.numero_demande}, "
        f"créé: {created}, statut: {instance.statut}"
    )

    # Éviter les boucles infinies
    if hasattr(instance, '_notifications_envoyees'):
        return

    try:
        # 1. NOUVELLE DEMANDE - Notifier le manager
        if created and instance.statut == 'EN_ATTENTE':
            logger.debug("Nouvelle demande créée - notification manager")
            manager = instance.get_manager()

            if manager and manager.employe:
                logger.debug(f"Manager trouvé: {manager.employe.nom} {manager.employe.prenoms}")
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_NOUVELLE',
                    destinataire=manager.employe
                )
                logger.debug("Notification créée pour le manager")
            else:
                logger.warning(f"Aucun manager trouvé pour {instance.employe.nom}")

        # 2. VALIDATION MANAGER - Notifier l'employé et les RH
        elif not created and instance.statut == 'VALIDEE_MANAGER':
            logger.debug("Validation manager - notification employé et RH")

            # Notifier l'employé
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_VALIDEE_MANAGER',
                destinataire=instance.employe
            )
            logger.debug("Notification créée pour l'employé")

            # Notifier les RH
            employes_rh = obtenir_employes_rh()
            logger.debug(f"{len(employes_rh)} employé(s) RH trouvé(s)")

            for employe_rh in employes_rh:
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_NOUVELLE',
                    destinataire=employe_rh
                )
                logger.debug(f"Notification créée pour RH: {employe_rh.nom} {employe_rh.prenoms}")

        # 3. REFUS MANAGER - Notifier l'employé
        elif not created and instance.statut == 'REFUSEE_MANAGER':
            logger.debug("Refus manager - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_REJETEE_MANAGER',
                destinataire=instance.employe
            )
            logger.debug("Notification rejet créée pour l'employé")

        # 4. VALIDATION RH - Notifier l'employé
        elif not created and instance.statut == 'VALIDEE_RH':
            logger.debug("Validation RH - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_VALIDEE_RH',
                destinataire=instance.employe
            )
            logger.debug("Notification validation RH créée pour l'employé")

        # 5. REFUS RH - Notifier l'employé
        elif not created and instance.statut == 'REFUSEE_RH':
            logger.debug("Refus RH - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_REJETEE_RH',
                destinataire=instance.employe
            )
            logger.debug("Notification rejet RH créée pour l'employé")

        # 6. ANNULATION - Notifier le manager et les RH
        elif not created and instance.statut == 'ANNULEE':
            logger.debug("Annulation - notification manager et RH")

            # Notifier le manager
            manager = instance.get_manager()
            if manager and manager.employe:
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_ANNULEE',
                    destinataire=manager.employe
                )
                logger.debug("Notification annulation créée pour le manager")

            # Notifier les RH si déjà validée par le manager
            if instance.validee_manager:
                employes_rh = obtenir_employes_rh()
                for employe_rh in employes_rh:
                    ZANO.creer_notification_absence(
                        demande_absence=instance,
                        type_notification='ABSENCE_ANNULEE',
                        destinataire=employe_rh
                    )
                    logger.debug(f"Notification annulation créée pour RH: {employe_rh.nom}")

    except Exception as e:
        logger.exception(f"Erreur dans signal notifications: {e}")


def obtenir_employes_rh():
    """
    Retourne la liste des employés ayant le rôle DRH actif
    Utilise la méthode has_role() existante
    """
    from employee.models import ZY00, ZYRE, ZYRO

    employes_rh = []

    try:
        logger.debug("Recherche des employés avec rôle DRH...")

        # Méthode optimisée : requête directe sur ZYRE
        attributions_drh = ZYRE.objects.filter(
            role__CODE='DRH',
            actif=True,
            date_fin__isnull=True
        ).select_related('employe')

        for attribution in attributions_drh:
            employes_rh.append(attribution.employe)
            logger.debug(
                f"DRH trouvé: {attribution.employe.matricule} - "
                f"{attribution.employe.nom} {attribution.employe.prenoms}"
            )

        if not employes_rh:
            logger.warning("Aucun employé avec le rôle DRH actif trouvé")

            # Debug: afficher tous les rôles RH disponibles
            logger.debug("Recherche de rôles contenant 'RH' ou 'DRH':")
            roles_rh = ZYRO.objects.filter(CODE__icontains='RH')
            for role in roles_rh:
                logger.debug(f"  - {role.CODE}: {role.LIBELLE}")

                # Chercher les attributions de ces rôles
                attributions = ZYRE.objects.filter(
                    role=role,
                    actif=True,
                    date_fin__isnull=True
                )
                if attributions.exists():
                    logger.debug(f"    {attributions.count()} attribution(s) active(s)")
                    for attr in attributions:
                        employes_rh.append(attr.employe)
                        logger.debug(f"    {attr.employe.matricule} - {attr.employe.nom}")

    except Exception as e:
        logger.exception(f"Erreur lors de la recherche des RH: {e}")

    # Dédupliquer la liste
    employes_rh = list(set(employes_rh))
    logger.debug(f"Total RH trouvés: {len(employes_rh)}")
    return employes_rh


@receiver(pre_save, sender=ZDDA)
def detecter_changement_statut(sender, instance, **kwargs):
    """
    Détecte les changements de statut pour enregistrer l'ancien statut
    """
    if instance.pk:
        try:
            old_instance = ZDDA.objects.get(pk=instance.pk)
            instance._old_statut = old_instance.statut
        except ZDDA.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=ZDDA)
def mettre_a_jour_solde_apres_demande(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement le solde après chaque modification d'une demande
    """
    if instance.type_absence.CODE in ['CPN', 'RTT']:
        logger.debug(
            f"Signal: Demande {instance.numero_demande} "
            f"{'créée' if created else 'modifiée'}, date: {instance.date_debut}"
        )
        mettre_a_jour_solde_conges(instance.employe, instance.date_debut)


@receiver(post_delete, sender=ZDDA)
def mettre_a_jour_solde_apres_suppression(sender, instance, **kwargs):
    """
    Met à jour automatiquement le solde après suppression d'une demande
    """
    if instance.type_absence.CODE in ['CPN', 'RTT']:
        logger.debug(f"Signal: Demande {instance.numero_demande} supprimée")
        mettre_a_jour_solde_conges(instance.employe, instance.date_debut.year)

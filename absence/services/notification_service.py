# absence/services/notification_service.py
"""
Service de gestion des notifications d'absences.
"""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour gérer les notifications liées aux absences."""

    # Types de notifications
    DEMANDE_CREEE = 'DEMANDE_CREEE'
    DEMANDE_VALIDEE_MANAGER = 'DEMANDE_VALIDEE_MANAGER'
    VALIDATION_MANAGER = 'VALIDATION_MANAGER'
    REJET_MANAGER = 'REJET_MANAGER'
    VALIDATION_RH = 'VALIDATION_RH'
    REJET_RH = 'REJET_RH'
    ABSENCE_ANNULEE = 'ABSENCE_ANNULEE'

    # Contextes
    CONTEXTE_EMPLOYE = 'EMPLOYE'
    CONTEXTE_MANAGER = 'MANAGER'
    CONTEXTE_RH = 'RH'

    @staticmethod
    def notifier_nouvelle_demande(absence):
        """
        Notifie le manager d'une nouvelle demande d'absence.

        Args:
            absence: Instance de l'absence créée
        """
        from absence.models import NotificationAbsence
        from departement.models import ZYMA

        try:
            # Trouver le manager du département de l'employé
            affectation = absence.employe.affectations.filter(
                date_fin__isnull=True
            ).first()

            if affectation and affectation.poste:
                departement = affectation.poste.DEPARTEMENT
                manager_relation = ZYMA.objects.filter(
                    departement=departement,
                    actif=True,
                    date_fin__isnull=True
                ).first()

                if manager_relation:
                    message = (
                        f"Nouvelle demande d'absence de {absence.employe.nom} "
                        f"{absence.employe.prenoms} du {absence.date_debut.strftime('%d/%m/%Y')} "
                        f"au {absence.date_fin.strftime('%d/%m/%Y')}"
                    )

                    NotificationAbsence.creer_notification(
                        destinataire=manager_relation.employe,
                        type_notif=NotificationService.DEMANDE_CREEE,
                        message=message,
                        contexte=NotificationService.CONTEXTE_MANAGER,
                        absence=absence
                    )
                    logger.info(
                        "Notification nouvelle demande envoyée au manager %s pour absence %s",
                        manager_relation.employe.matricule, absence.id
                    )

        except Exception as e:
            logger.error("Erreur notification nouvelle demande: %s", e)

    @staticmethod
    def notifier_validation_manager(absence, action):
        """
        Notifie suite à la décision du manager.

        Args:
            absence: Instance de l'absence
            action: 'VALIDE' ou 'REJETE'
        """
        from absence.models import NotificationAbsence
        from employee.models import ZY00

        try:
            if action == 'VALIDE':
                # Notification à l'employé
                message_employe = (
                    f"Votre demande d'absence du {absence.date_debut.strftime('%d/%m/%Y')} "
                    f"au {absence.date_fin.strftime('%d/%m/%Y')} a été validée par votre manager"
                )
                NotificationAbsence.creer_notification(
                    destinataire=absence.employe,
                    type_notif=NotificationService.VALIDATION_MANAGER,
                    message=message_employe,
                    contexte=NotificationService.CONTEXTE_EMPLOYE,
                    absence=absence
                )

                # Notification aux RH
                employes_rh = ZY00.objects.filter(
                    roles__role__code__in=['DRH', 'ASSISTANT_RH'],
                    statut_employe='ACTIF'
                ).distinct()

                for employe_rh in employes_rh:
                    message_rh = (
                        f"Demande d'absence de {absence.employe.nom} {absence.employe.prenoms} "
                        f"validée par le manager, en attente de validation RH"
                    )
                    NotificationAbsence.creer_notification(
                        destinataire=employe_rh,
                        type_notif=NotificationService.DEMANDE_VALIDEE_MANAGER,
                        message=message_rh,
                        contexte=NotificationService.CONTEXTE_RH,
                        absence=absence
                    )

            elif action == 'REJETE':
                message = (
                    f"Votre demande d'absence du {absence.date_debut.strftime('%d/%m/%Y')} "
                    f"au {absence.date_fin.strftime('%d/%m/%Y')} a été rejetée par votre manager"
                )
                if absence.commentaire_manager:
                    message += f". Motif: {absence.commentaire_manager}"

                NotificationAbsence.creer_notification(
                    destinataire=absence.employe,
                    type_notif=NotificationService.REJET_MANAGER,
                    message=message,
                    contexte=NotificationService.CONTEXTE_EMPLOYE,
                    absence=absence
                )

            logger.info(
                "Notification validation manager (%s) envoyée pour absence %s",
                action, absence.id
            )

        except Exception as e:
            logger.error("Erreur notification validation manager: %s", e)

    @staticmethod
    def notifier_validation_rh(absence, action):
        """
        Notifie suite à la décision RH.

        Args:
            absence: Instance de l'absence
            action: 'VALIDE' ou 'REJETE'
        """
        from absence.models import NotificationAbsence

        try:
            if action == 'VALIDE':
                message = (
                    f"Votre demande d'absence du {absence.date_debut.strftime('%d/%m/%Y')} "
                    f"au {absence.date_fin.strftime('%d/%m/%Y')} a été validée par les RH"
                )
                NotificationAbsence.creer_notification(
                    destinataire=absence.employe,
                    type_notif=NotificationService.VALIDATION_RH,
                    message=message,
                    contexte=NotificationService.CONTEXTE_EMPLOYE,
                    absence=absence
                )

            elif action == 'REJETE':
                message = (
                    f"Votre demande d'absence du {absence.date_debut.strftime('%d/%m/%Y')} "
                    f"au {absence.date_fin.strftime('%d/%m/%Y')} a été rejetée par les RH"
                )
                if absence.commentaire_rh:
                    message += f". Motif: {absence.commentaire_rh}"

                NotificationAbsence.creer_notification(
                    destinataire=absence.employe,
                    type_notif=NotificationService.REJET_RH,
                    message=message,
                    contexte=NotificationService.CONTEXTE_EMPLOYE,
                    absence=absence
                )

            logger.info(
                "Notification validation RH (%s) envoyée pour absence %s",
                action, absence.id
            )

        except Exception as e:
            logger.error("Erreur notification validation RH: %s", e)

    @staticmethod
    def notifier_annulation(absence, par_utilisateur):
        """
        Notifie l'annulation d'une absence.

        Args:
            absence: Instance de l'absence annulée
            par_utilisateur: Utilisateur ayant annulé
        """
        from absence.models import NotificationAbsence
        from departement.models import ZYMA
        from employee.models import ZY00

        try:
            message_base = (
                f"L'absence de {absence.employe.nom} {absence.employe.prenoms} "
                f"du {absence.date_debut.strftime('%d/%m/%Y')} au {absence.date_fin.strftime('%d/%m/%Y')} "
                f"a été annulée"
            )

            # Notifier le manager
            affectation = absence.employe.affectations.filter(
                date_fin__isnull=True
            ).first()

            if affectation and affectation.poste:
                departement = affectation.poste.DEPARTEMENT
                manager_relation = ZYMA.objects.filter(
                    departement=departement,
                    actif=True,
                    date_fin__isnull=True
                ).first()

                if manager_relation:
                    NotificationAbsence.creer_notification(
                        destinataire=manager_relation.employe,
                        type_notif=NotificationService.ABSENCE_ANNULEE,
                        message=message_base,
                        contexte=NotificationService.CONTEXTE_MANAGER,
                        absence=absence
                    )

            # Notifier les RH
            employes_rh = ZY00.objects.filter(
                roles__role__code__in=['DRH', 'ASSISTANT_RH'],
                statut_employe='ACTIF'
            ).distinct()

            for employe_rh in employes_rh:
                NotificationAbsence.creer_notification(
                    destinataire=employe_rh,
                    type_notif=NotificationService.ABSENCE_ANNULEE,
                    message=message_base,
                    contexte=NotificationService.CONTEXTE_RH,
                    absence=absence
                )

            logger.info("Notifications annulation envoyées pour absence %s", absence.id)

        except Exception as e:
            logger.error("Erreur notification annulation: %s", e)

    @staticmethod
    def get_notifications_non_lues(employe):
        """
        Récupère les notifications non lues d'un employé.

        Args:
            employe: Instance de l'employé

        Returns:
            QuerySet: Notifications non lues
        """
        from absence.models import NotificationAbsence

        return NotificationAbsence.objects.filter(
            destinataire=employe,
            lue=False,
            absence__isnull=False  # Uniquement les notifications d'absence
        ).order_by('-date_creation')

    @staticmethod
    def get_notifications_count(employe):
        """
        Compte les notifications non lues d'un employé.

        Args:
            employe: Instance de l'employé

        Returns:
            int: Nombre de notifications non lues
        """
        from absence.models import NotificationAbsence

        return NotificationAbsence.objects.filter(
            destinataire=employe,
            lue=False,
            absence__isnull=False
        ).count()

    @staticmethod
    def marquer_comme_lue(notification):
        """
        Marque une notification comme lue.

        Args:
            notification: Instance de la notification
        """
        notification.lue = True
        notification.save(update_fields=['lue'])

    @staticmethod
    def marquer_toutes_lues(employe):
        """
        Marque toutes les notifications d'absence d'un employé comme lues.

        Args:
            employe: Instance de l'employé

        Returns:
            int: Nombre de notifications marquées comme lues
        """
        from absence.models import NotificationAbsence

        return NotificationAbsence.objects.filter(
            destinataire=employe,
            lue=False,
            absence__isnull=False
        ).update(lue=True)

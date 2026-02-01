"""
Service de gestion des notifications pour le module Project Management.
Utilise le modèle NotificationAbsence avec le contexte 'PM' (Project Management).
"""
import logging
from absence.models import NotificationAbsence

logger = logging.getLogger(__name__)


class NotificationService:
    """Service centralisé pour les notifications du module Project Management."""

    # Types de notifications PM
    TYPE_PROJET_ASSIGNE = 'PROJET_ASSIGNE'
    TYPE_PROJET_REASSIGNE = 'PROJET_REASSIGNE'
    TYPE_TICKET_ASSIGNE = 'TICKET_ASSIGNE'
    TYPE_TICKET_REASSIGNE = 'TICKET_REASSIGNE'
    TYPE_STATUT_PROJET_CHANGE = 'STATUT_PROJET_CHANGE'
    TYPE_STATUT_TICKET_CHANGE = 'STATUT_TICKET_CHANGE'
    TYPE_COMMENTAIRE_TICKET = 'COMMENTAIRE_TICKET'
    TYPE_ECHEANCE_PROCHE = 'ECHEANCE_PROCHE'

    # Messages templates pour les changements de statut ticket
    MESSAGES_STATUT_TICKET = {
        ('OUVERT', 'EN_COURS'): "🚀 Le ticket '{code}' est passé en cours",
        ('EN_COURS', 'EN_REVUE'): "👀 Le ticket '{code}' est en revue",
        ('EN_REVUE', 'TERMINE'): "✅ Le ticket '{code}' est terminé",
        ('EN_COURS', 'OUVERT'): "↩️ Le ticket '{code}' est revenu à Ouvert",
        ('EN_REVUE', 'EN_COURS'): "🔄 Le ticket '{code}' est retourné en cours",
    }

    # Messages templates pour les changements de statut projet
    MESSAGES_STATUT_PROJET = {
        ('PLANIFIE', 'EN_COURS'): "🚀 Le projet '{nom}' a démarré",
        ('EN_COURS', 'TERMINE'): "✅ Le projet '{nom}' est terminé",
        ('EN_COURS', 'EN_PAUSE'): "⏸️ Le projet '{nom}' est en pause",
        ('EN_PAUSE', 'EN_COURS'): "▶️ Le projet '{nom}' a repris",
    }

    @classmethod
    def _creer_notification(cls, destinataire, type_notif, message, ticket=None, projet=None):
        """
        Crée une notification via le modèle NotificationAbsence.

        Args:
            destinataire: Employé destinataire
            type_notif: Type de notification
            message: Message de la notification
            ticket: Instance JRTicket (optionnel)
            projet: Instance JRProject (optionnel)

        Returns:
            NotificationAbsence ou None
        """
        if not destinataire:
            return None

        return NotificationAbsence.creer_notification(
            destinataire=destinataire,
            type_notif=type_notif,
            message=message,
            contexte='PM',
            ticket=ticket,
            projet=projet
        )

    @classmethod
    def _get_equipe_employe(cls, employe):
        """
        Récupère les membres de l'équipe (même département) d'un employé.

        Args:
            employe: Instance ZY00

        Returns:
            list: Liste des employés de la même équipe
        """
        if not employe:
            return []

        try:
            from employee.models import ZYAF, ZY00

            dept = employe.get_departement_actuel()
            if not dept:
                return []

            # Récupérer tous les employés du même département
            membres_ids = ZYAF.objects.filter(
                poste__DEPARTEMENT=dept,
                date_fin__isnull=True,
                employe__etat='actif'
            ).exclude(
                employe=employe
            ).values_list('employe', flat=True).distinct()

            return list(ZY00.objects.filter(pk__in=membres_ids))

        except Exception as e:
            logger.warning(f"Erreur récupération équipe: {e}")
            return []

    @classmethod
    def _get_manager_employe(cls, employe):
        """
        Récupère le manager d'un employé (manager du département).

        Args:
            employe: Instance ZY00

        Returns:
            ZY00 ou None
        """
        if not employe:
            return None

        try:
            from departement.models import ZYMA

            dept = employe.get_departement_actuel()
            if not dept:
                return None

            manager_dept = ZYMA.objects.filter(
                departement=dept,
                actif=True,
                date_fin__isnull=True
            ).first()

            if manager_dept:
                return manager_dept.employe

        except Exception as e:
            logger.warning(f"Erreur récupération manager: {e}")

        return None

    # =========================================================================
    # NOTIFICATIONS D'ASSIGNATION
    # =========================================================================

    @classmethod
    def notifier_assignation_projet(cls, projet, employe_assigne, ancien_chef_projet=None):
        """
        Notifie un employé qu'il a été assigné à un projet.

        Args:
            projet: Instance JRProject
            employe_assigne: Employé assigné (chef de projet)
            ancien_chef_projet: Ancien chef de projet (si réassignation)

        Returns:
            list: Liste des notifications créées
        """
        notifications = []

        # Notifier le nouveau chef de projet
        if employe_assigne:
            message = f"📋 Vous avez été assigné au projet '{projet.nom}'"
            notif = cls._creer_notification(
                destinataire=employe_assigne,
                type_notif=cls.TYPE_PROJET_ASSIGNE,
                message=message,
                projet=projet
            )
            if notif:
                notifications.append(notif)

        # Notifier l'ancien chef de projet si réassignation
        if ancien_chef_projet and ancien_chef_projet != employe_assigne:
            nouveau_nom = f"{employe_assigne.nom} {employe_assigne.prenoms}" if employe_assigne else "personne"
            message = f"ℹ️ Le projet '{projet.nom}' a été réassigné à {nouveau_nom}"
            notif = cls._creer_notification(
                destinataire=ancien_chef_projet,
                type_notif=cls.TYPE_PROJET_REASSIGNE,
                message=message,
                projet=projet
            )
            if notif:
                notifications.append(notif)

        return notifications

    @classmethod
    def notifier_assignation_ticket(cls, ticket, ancien_assigne=None):
        """
        Notifie l'assigné d'un ticket.

        Args:
            ticket: Instance JRTicket
            ancien_assigne: Ancien assigné (si réassignation)

        Returns:
            list: Liste des notifications créées
        """
        notifications = []

        # Notifier le nouvel assigné
        if ticket.assigne:
            message = f"📋 Vous avez été assigné au ticket '{ticket.code}' - {ticket.titre}"
            notif = cls._creer_notification(
                destinataire=ticket.assigne,
                type_notif=cls.TYPE_TICKET_ASSIGNE,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)

        # Notifier l'ancien assigné si réassignation
        if ancien_assigne and ancien_assigne != ticket.assigne:
            nouvel_nom = f"{ticket.assigne.nom} {ticket.assigne.prenoms}" if ticket.assigne else "personne"
            message = f"ℹ️ Le ticket '{ticket.code}' a été réassigné à {nouvel_nom}"
            notif = cls._creer_notification(
                destinataire=ancien_assigne,
                type_notif=cls.TYPE_TICKET_REASSIGNE,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)

        return notifications

    # =========================================================================
    # NOTIFICATIONS DE CHANGEMENT DE STATUT
    # =========================================================================

    @classmethod
    def notifier_changement_statut_projet(cls, projet, ancien_statut, nouveau_statut):
        """
        Notifie le changement de statut d'un projet.
        Destinataires: chef de projet, équipe, manager.

        Args:
            projet: Instance JRProject
            ancien_statut: Ancien statut
            nouveau_statut: Nouveau statut

        Returns:
            list: Liste des notifications créées
        """
        notifications = []
        destinataires_notifies = set()

        # Construire le message
        cle = (ancien_statut, nouveau_statut)
        if cle in cls.MESSAGES_STATUT_PROJET:
            message = cls.MESSAGES_STATUT_PROJET[cle].format(nom=projet.nom)
        else:
            message = f"🔄 Le projet '{projet.nom}' est passé de {ancien_statut} à {nouveau_statut}"

        # 1. Notifier le chef de projet
        if projet.chef_projet:
            notif = cls._creer_notification(
                destinataire=projet.chef_projet,
                type_notif=cls.TYPE_STATUT_PROJET_CHANGE,
                message=message,
                projet=projet
            )
            if notif:
                notifications.append(notif)
                destinataires_notifies.add(projet.chef_projet.pk)

        # 2. Notifier l'équipe du chef de projet
        if projet.chef_projet:
            equipe = cls._get_equipe_employe(projet.chef_projet)
            for membre in equipe:
                if membre.pk not in destinataires_notifies:
                    notif = cls._creer_notification(
                        destinataire=membre,
                        type_notif=cls.TYPE_STATUT_PROJET_CHANGE,
                        message=message,
                        projet=projet
                    )
                    if notif:
                        notifications.append(notif)
                        destinataires_notifies.add(membre.pk)

        # 3. Notifier le manager du chef de projet
        if projet.chef_projet:
            manager = cls._get_manager_employe(projet.chef_projet)
            if manager and manager.pk not in destinataires_notifies:
                notif = cls._creer_notification(
                    destinataire=manager,
                    type_notif=cls.TYPE_STATUT_PROJET_CHANGE,
                    message=message,
                    projet=projet
                )
                if notif:
                    notifications.append(notif)

        return notifications

    @classmethod
    def notifier_changement_statut_ticket(cls, ticket, ancien_statut, nouveau_statut):
        """
        Notifie le changement de statut d'un ticket.
        Destinataires: assigné, équipe de l'assigné, manager de l'assigné.

        Args:
            ticket: Instance JRTicket
            ancien_statut: Ancien statut
            nouveau_statut: Nouveau statut

        Returns:
            list: Liste des notifications créées
        """
        notifications = []
        destinataires_notifies = set()

        # Construire le message
        cle = (ancien_statut, nouveau_statut)
        if cle in cls.MESSAGES_STATUT_TICKET:
            message = cls.MESSAGES_STATUT_TICKET[cle].format(code=ticket.code)
        else:
            message = f"🔄 Le ticket '{ticket.code}' est passé de {ancien_statut} à {nouveau_statut}"

        # 1. Notifier l'assigné du ticket
        if ticket.assigne:
            notif = cls._creer_notification(
                destinataire=ticket.assigne,
                type_notif=cls.TYPE_STATUT_TICKET_CHANGE,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)
                destinataires_notifies.add(ticket.assigne.pk)

            # 2. Notifier l'équipe de l'assigné
            equipe = cls._get_equipe_employe(ticket.assigne)
            for membre in equipe:
                if membre.pk not in destinataires_notifies:
                    notif = cls._creer_notification(
                        destinataire=membre,
                        type_notif=cls.TYPE_STATUT_TICKET_CHANGE,
                        message=message,
                        ticket=ticket
                    )
                    if notif:
                        notifications.append(notif)
                        destinataires_notifies.add(membre.pk)

            # 3. Notifier le manager de l'assigné
            manager = cls._get_manager_employe(ticket.assigne)
            if manager and manager.pk not in destinataires_notifies:
                notif = cls._creer_notification(
                    destinataire=manager,
                    type_notif=cls.TYPE_STATUT_TICKET_CHANGE,
                    message=message,
                    ticket=ticket
                )
                if notif:
                    notifications.append(notif)

        # 4. Notifier aussi le chef de projet si différent
        if ticket.projet.chef_projet and ticket.projet.chef_projet.pk not in destinataires_notifies:
            notif = cls._creer_notification(
                destinataire=ticket.projet.chef_projet,
                type_notif=cls.TYPE_STATUT_TICKET_CHANGE,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)

        return notifications

    # =========================================================================
    # NOTIFICATIONS DE COMMENTAIRES
    # =========================================================================

    @classmethod
    def notifier_commentaire_ticket(cls, commentaire, auteur):
        """
        Notifie l'équipe de l'assigné d'un nouveau commentaire.

        Args:
            commentaire: Instance JRCommentaire
            auteur: Employé qui a écrit le commentaire

        Returns:
            list: Liste des notifications créées
        """
        notifications = []
        destinataires_notifies = set()
        ticket = commentaire.ticket

        # Ne pas notifier l'auteur
        if auteur:
            destinataires_notifies.add(auteur.pk)

        message = f"💬 Nouveau commentaire sur le ticket '{ticket.code}'"

        # 1. Notifier l'assigné du ticket (sauf si c'est l'auteur)
        if ticket.assigne and ticket.assigne.pk not in destinataires_notifies:
            notif = cls._creer_notification(
                destinataire=ticket.assigne,
                type_notif=cls.TYPE_COMMENTAIRE_TICKET,
                message=f"💬 Nouveau commentaire sur votre ticket '{ticket.code}'",
                ticket=ticket
            )
            if notif:
                notifications.append(notif)
                destinataires_notifies.add(ticket.assigne.pk)

        # 2. Notifier l'équipe de l'assigné
        if ticket.assigne:
            equipe = cls._get_equipe_employe(ticket.assigne)
            for membre in equipe:
                if membre.pk not in destinataires_notifies:
                    notif = cls._creer_notification(
                        destinataire=membre,
                        type_notif=cls.TYPE_COMMENTAIRE_TICKET,
                        message=message,
                        ticket=ticket
                    )
                    if notif:
                        notifications.append(notif)
                        destinataires_notifies.add(membre.pk)

        # 3. Notifier les personnes mentionnées
        for mentionne in commentaire.mentions.all():
            if mentionne.pk not in destinataires_notifies:
                notif = cls._creer_notification(
                    destinataire=mentionne,
                    type_notif=cls.TYPE_COMMENTAIRE_TICKET,
                    message=f"💬 Vous avez été mentionné dans un commentaire sur '{ticket.code}'",
                    ticket=ticket
                )
                if notif:
                    notifications.append(notif)
                    destinataires_notifies.add(mentionne.pk)

        # 4. Notifier le chef de projet
        if ticket.projet.chef_projet and ticket.projet.chef_projet.pk not in destinataires_notifies:
            notif = cls._creer_notification(
                destinataire=ticket.projet.chef_projet,
                type_notif=cls.TYPE_COMMENTAIRE_TICKET,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)

        return notifications

    # =========================================================================
    # NOTIFICATIONS D'ÉCHÉANCE
    # =========================================================================

    @classmethod
    def notifier_echeance_proche(cls, ticket, jours_restants):
        """
        Notifie que l'échéance d'un ticket approche.

        Args:
            ticket: Instance JRTicket
            jours_restants: Nombre de jours avant l'échéance

        Returns:
            list: Liste des notifications créées
        """
        notifications = []

        if not ticket.assigne or not ticket.date_echeance:
            return notifications

        if jours_restants == 0:
            message = f"⚠️ Le ticket '{ticket.code}' arrive à échéance aujourd'hui!"
        elif jours_restants == 1:
            message = f"⏳ Le ticket '{ticket.code}' arrive à échéance demain"
        else:
            message = f"⏳ Le ticket '{ticket.code}' arrive à échéance dans {jours_restants} jours"

        # Notifier l'assigné
        notif = cls._creer_notification(
            destinataire=ticket.assigne,
            type_notif=cls.TYPE_ECHEANCE_PROCHE,
            message=message,
            ticket=ticket
        )
        if notif:
            notifications.append(notif)

        # Notifier le chef de projet si échéance très proche
        if jours_restants <= 1 and ticket.projet.chef_projet and ticket.projet.chef_projet != ticket.assigne:
            notif = cls._creer_notification(
                destinataire=ticket.projet.chef_projet,
                type_notif=cls.TYPE_ECHEANCE_PROCHE,
                message=message,
                ticket=ticket
            )
            if notif:
                notifications.append(notif)

        return notifications

# gestion_temps_activite/services/notification_service.py
"""
Service de gestion des notifications pour le module GTA.
"""
from absence.models import NotificationAbsence


class NotificationService:
    """Service centralisé pour les notifications GTA."""

    # Types de notifications GTA
    TYPE_TACHE_ASSIGNEE = 'TACHE_ASSIGNEE'
    TYPE_TACHE_REASSIGNEE = 'TACHE_REASSIGNEE'
    TYPE_TACHE_MODIFIEE = 'TACHE_MODIFIEE'
    TYPE_STATUT_CHANGE = 'STATUT_TACHE_CHANGE'
    TYPE_COMMENTAIRE = 'COMMENTAIRE_TACHE'
    TYPE_ECHEANCE_PROCHE = 'ECHEANCE_TACHE_PROCHE'

    # Messages templates pour les changements de statut
    MESSAGES_STATUT = {
        ('A_FAIRE', 'EN_COURS'): "🚀 Votre tâche '{titre}' est maintenant en cours",
        ('EN_COURS', 'TERMINE'): "✅ La tâche '{titre}' a été marquée comme terminée",
        ('EN_COURS', 'EN_ATTENTE'): "⏸️ La tâche '{titre}' est en attente",
        ('EN_ATTENTE', 'EN_COURS'): "▶️ La tâche '{titre}' a repris",
        ('EN_COURS', 'A_FAIRE'): "↩️ La tâche '{titre}' est revenue à 'À faire'",
    }

    @classmethod
    def notifier_nouvelle_tache(cls, tache, createur):
        """
        Notifier l'assigné d'une nouvelle tâche.

        Args:
            tache: Instance ZDTA
            createur: Employé qui a créé la tâche

        Returns:
            NotificationAbsence ou None
        """
        if not tache.assignee:
            return None

        return NotificationAbsence.creer_notification(
            destinataire=tache.assignee,
            type_notif=cls.TYPE_TACHE_ASSIGNEE,
            message=f"📋 Nouvelle tâche assignée : {tache.titre}",
            contexte='GTA',
            tache=tache
        )

    @classmethod
    def notifier_reassignation(cls, tache, ancien_assignee, nouvel_assignee):
        """
        Notifier l'ancien et le nouvel assigné lors d'une réassignation.

        Args:
            tache: Instance ZDTA
            ancien_assignee: Ancien employé assigné
            nouvel_assignee: Nouvel employé assigné

        Returns:
            list: Liste des notifications créées
        """
        notifications = []

        if nouvel_assignee:
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=nouvel_assignee,
                    type_notif=cls.TYPE_TACHE_REASSIGNEE,
                    message=f"📋 Tâche réassignée : {tache.titre}",
                    contexte='GTA',
                    tache=tache
                )
            )

        if ancien_assignee and ancien_assignee != nouvel_assignee:
            nouvel_nom = nouvel_assignee.nom if nouvel_assignee else 'un autre employé'
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=ancien_assignee,
                    type_notif=cls.TYPE_TACHE_REASSIGNEE,
                    message=f"ℹ️ La tâche '{tache.titre}' a été réassignée à {nouvel_nom}",
                    contexte='GTA',
                    tache=tache
                )
            )

        return notifications

    @classmethod
    def notifier_modification(cls, tache, employe_modifiant, changements):
        """
        Notifier l'assigné d'une modification de tâche.

        Args:
            tache: Instance ZDTA
            employe_modifiant: Employé qui a fait la modification
            changements: Liste des champs modifiés

        Returns:
            NotificationAbsence ou None
        """
        if not tache.assignee or tache.assignee == employe_modifiant:
            return None

        message = f"✏️ Votre tâche '{tache.titre}' a été modifiée"
        if changements:
            message += f" : {', '.join(changements)}"

        return NotificationAbsence.creer_notification(
            destinataire=tache.assignee,
            type_notif=cls.TYPE_TACHE_MODIFIEE,
            message=message,
            contexte='GTA',
            tache=tache
        )

    @classmethod
    def notifier_changement_statut(cls, tache, ancien_statut, nouveau_statut):
        """
        Notifier le changement de statut d'une tâche.

        Args:
            tache: Instance ZDTA
            ancien_statut: Ancien statut
            nouveau_statut: Nouveau statut

        Returns:
            NotificationAbsence ou None
        """
        if not tache.assignee:
            return None

        cle = (ancien_statut, nouveau_statut)
        if cle in cls.MESSAGES_STATUT:
            message = cls.MESSAGES_STATUT[cle].format(titre=tache.titre)

            return NotificationAbsence.creer_notification(
                destinataire=tache.assignee,
                type_notif=cls.TYPE_STATUT_CHANGE,
                message=message,
                contexte='GTA',
                tache=tache
            )

        return None

    @classmethod
    def notifier_commentaire(cls, commentaire, destinataires_avec_messages):
        """
        Notifier les personnes concernées par un commentaire.

        Args:
            commentaire: Instance ZDCM
            destinataires_avec_messages: dict {employe: message}

        Returns:
            list: Liste des notifications créées
        """
        notifications = []

        for destinataire, message in destinataires_avec_messages.items():
            notifications.append(
                NotificationAbsence.creer_notification(
                    destinataire=destinataire,
                    type_notif=cls.TYPE_COMMENTAIRE,
                    message=message,
                    contexte='GTA',
                    tache=commentaire.tache
                )
            )

        return notifications

    @classmethod
    def notifier_echeance_proche(cls, tache, jours_restants):
        """
        Notifier que l'échéance d'une tâche approche.

        Args:
            tache: Instance ZDTA
            jours_restants: Nombre de jours avant l'échéance

        Returns:
            NotificationAbsence ou None
        """
        if not tache.assignee or not tache.date_fin_prevue:
            return None

        if 0 <= jours_restants <= 2:
            message = f"⏳ Échéance proche ({jours_restants} jour(s)) : {tache.titre}"

            return NotificationAbsence.creer_notification(
                destinataire=tache.assignee,
                type_notif=cls.TYPE_ECHEANCE_PROCHE,
                message=message,
                contexte='GTA',
                tache=tache
            )

        return None

    @classmethod
    def get_destinataires_commentaire(cls, commentaire, auteur):
        """
        Détermine les destinataires d'une notification de commentaire.

        Args:
            commentaire: Instance ZDCM
            auteur: Employé qui a écrit le commentaire

        Returns:
            dict: {destinataire: message_personnalisé}
        """
        from employee.models import ZY00
        from departement.models import ZYMA
        from employee.models import ZYAF

        destinataires = {}
        tache = commentaire.tache

        # 1. L'assigné de la tâche
        if tache.assignee and tache.assignee != auteur:
            destinataires[tache.assignee] = f"💬 Nouveau commentaire sur votre tâche '{tache.titre}'"

        # 2. Le chef de projet
        if tache.projet and tache.projet.chef_projet and tache.projet.chef_projet != auteur:
            if tache.projet.chef_projet not in destinataires:
                destinataires[tache.projet.chef_projet] = f"💬 Nouveau commentaire sur la tâche '{tache.titre}' de votre projet"

        # 3. Les personnes mentionnées
        for mentionne in commentaire.mentions.all():
            if mentionne != auteur and mentionne not in destinataires:
                destinataires[mentionne] = f"💬 Vous avez été mentionné dans un commentaire sur la tâche '{tache.titre}'"

        # 4. Le manager du département de l'assigné
        if tache.assignee:
            try:
                manager_dept = ZYMA.objects.filter(
                    departement=tache.assignee.get_departement_actuel(),
                    actif=True,
                    date_fin__isnull=True
                ).first()

                if manager_dept and manager_dept.employe != auteur and manager_dept.employe not in destinataires:
                    destinataires[manager_dept.employe] = f"💬 Nouveau commentaire sur la tâche '{tache.titre}'"
            except Exception:
                pass

        return destinataires

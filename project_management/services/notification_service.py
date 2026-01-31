from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


class NotificationService:
    """Service pour la gestion des notifications"""
    
    @staticmethod
    def creer_notification(utilisateur, titre, message, type_notification='INFO', 
                          objet_id=None, objet_type=None, priorite='normale'):
        """
        Crée une notification pour un utilisateur
        
        Args:
            utilisateur: L'utilisateur qui recevra la notification
            titre: Titre de la notification
            message: Message détaillé
            type_notification: Type de notification (INFO, WARNING, ERROR, SUCCESS)
            objet_id: ID de l'objet lié (ticket, projet, etc.)
            objet_type: Type de l'objet lié
            priorite: Priorité (basse, normale, haute, urgente)
        """
        # Pour l'instant, on utilise un modèle simple
        # Dans une implémentation complète, on aurait un modèle Notification
        
        notification = {
            'utilisateur': utilisateur,
            'titre': titre,
            'message': message,
            'type_notification': type_notification,
            'objet_id': objet_id,
            'objet_type': objet_type,
            'priorite': priorite,
            'created_at': timezone.now(),
            'lue': False
        }
        
        # Envoyer l'email si configuré
        if getattr(settings, 'ENVOI_EMAIL_NOTIFICATIONS', False):
            NotificationService._envoyer_email_notification(notification)
        
        return notification
    
    @staticmethod
    def _envoyer_email_notification(notification):
        """Envoie une notification par email"""
        try:
            sujet = f"[HR_ONIAN] {notification['titre']}"
            
            context = {
                'utilisateur': notification['utilisateur'],
                'titre': notification['titre'],
                'message': notification['message'],
                'type_notification': notification['type_notification'],
                'objet_id': notification['objet_id'],
                'objet_type': notification['objet_type'],
            }
            
            # Rendre le template email
            html_message = render_to_string(
                'project_management/emails/notification.html', 
                context
            )
            text_message = render_to_string(
                'project_management/emails/notification.txt', 
                context
            )
            
            # Envoyer l'email
            send_mail(
                sujet,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [notification['utilisateur'].email],
                html_message=html_message,
                fail_silently=False
            )
            
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer le processus
            print(f"Erreur lors de l'envoi de l'email: {e}")
    
    @staticmethod
    def notifier_creation_ticket(ticket):
        """Notifie la création d'un nouveau ticket"""
        notifications = []
        
        # Notifier le chef de projet
        if ticket.projet.chef_projet:
            notification = NotificationService.creer_notification(
                utilisateur=ticket.projet.chef_projet,
                titre=f"Nouveau ticket créé : {ticket.code}",
                message=f"Un nouveau ticket '{ticket.titre}' a été créé pour le projet {ticket.projet.nom}",
                type_notification='INFO',
                objet_id=ticket.id,
                objet_type='ticket'
            )
            notifications.append(notification)
        
        # Notifier les membres de l'équipe du projet (optionnel)
        # Ici on pourrait notifier tous les employés qui ont travaillé sur le projet
        
        return notifications
    
    @staticmethod
    def notifier_changement_statut_ticket(ticket, ancien_statut, nouveau_statut):
        """Notifie le changement de statut d'un ticket"""
        notifications = []
        
        # Notifier l'assigné du ticket
        if ticket.assigne:
            notification = NotificationService.creer_notification(
                utilisateur=ticket.assigne,
                titre=f"Changement de statut : {ticket.code}",
                message=f"Le ticket '{ticket.titre}' est passé de {ancien_statut} à {nouveau_statut}",
                type_notification='INFO',
                objet_id=ticket.id,
                objet_type='ticket'
            )
            notifications.append(notification)
        
        # Notifier le chef de projet
        if ticket.projet.chef_projet and ticket.projet.chef_projet != ticket.assigne:
            notification = NotificationService.creer_notification(
                utilisateur=ticket.projet.chef_projet,
                titre=f"Changement de statut : {ticket.code}",
                message=f"Le ticket '{ticket.titre}' est passé de {ancien_statut} à {nouveau_statut}",
                type_notification='INFO',
                objet_id=ticket.id,
                objet_type='ticket'
            )
            notifications.append(notification)
        
        # Notification spéciale pour les tickets critiques
        if ticket.priorite == 'CRITIQUE' and nouveau_statut == 'TERMINE':
            notification = NotificationService.creer_notification(
                utilisateur=ticket.projet.chef_projet,
                titre=f"Ticket critique terminé : {ticket.code}",
                message=f"Le ticket critique '{ticket.titre}' a été terminé",
                type_notification='SUCCESS',
                objet_id=ticket.id,
                objet_type='ticket',
                priorite='haute'
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notifier_assignation_ticket(ticket, ancien_assigne=None):
        """Notifie l'assignation d'un ticket"""
        notifications = []
        
        if ticket.assigne:
            notification = NotificationService.creer_notification(
                utilisateur=ticket.assigne,
                titre=f"Nouvelle assignation : {ticket.code}",
                message=f"Vous avez été assigné au ticket '{ticket.titre}' ({ticket.priorite})",
                type_notification='INFO',
                objet_id=ticket.id,
                objet_type='ticket'
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notifier_imputation_en_attente(imputation):
        """Notifie qu'une imputation est en attente de validation"""
        notifications = []
        
        # Notifier le chef de projet
        projet = imputation.ticket.projet
        if projet.chef_projet:
            notification = NotificationService.creer_notification(
                utilisateur=projet.chef_projet,
                titre=f"Imputation en attente : {imputation.ticket.code}",
                message=f"{imputation.employe} a imputé {imputation.total_heures}h sur le ticket '{imputation.ticket.titre}'",
                type_notification='INFO',
                objet_id=imputation.id,
                objet_type='imputation'
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notifier_validation_imputation(imputation, action):
        """Notifie la validation/rejet d'une imputation"""
        notifications = []
        
        message_validation = ""
        type_notif = 'SUCCESS'
        
        if action == 'valider':
            message_validation = f"Votre imputation de {imputation.total_heures}h a été validée"
            type_notif = 'SUCCESS'
        elif action == 'rejeter':
            message_validation = f"Votre imputation de {imputation.total_heures}h a été rejetée"
            type_notif = 'WARNING'
        
        notification = NotificationService.creer_notification(
            utilisateur=imputation.employe,
            titre=f"Imputation {action}e : {imputation.ticket.code}",
            message=message_validation,
            type_notification=type_notif,
            objet_id=imputation.id,
            objet_type='imputation'
        )
        notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notifier_sprint_termine(sprint):
        """Notifie la fin d'un sprint"""
        notifications = []
        
        # Statistiques du sprint
        tickets_termines = sprint.tickets.filter(statut='TERMINE').count()
        tickets_total = sprint.tickets.count()
        
        # Notifier le chef de projet
        if sprint.projet.chef_projet:
            notification = NotificationService.creer_notification(
                utilisateur=sprint.projet.chef_projet,
                titre=f"Sprint terminé : {sprint.nom}",
                message=f"Le sprint '{sprint.nom}' est terminé. {tickets_termines}/{tickets_total} tickets terminés.",
                type_notification='INFO',
                objet_id=sprint.id,
                objet_type='sprint'
            )
            notifications.append(notification)
        
        # Notifier les participants au sprint
        participants = sprint.tickets.values_list('assigne', flat=True).distinct()
        for participant_id in participants:
            try:
                from employee.models import ZY00
                participant = ZY00.objects.get(pk=participant_id)
                
                if participant != sprint.projet.chef_projet:
                    notification = NotificationService.creer_notification(
                        utilisateur=participant,
                        titre=f"Sprint terminé : {sprint.nom}",
                        message=f"Le sprint '{sprint.nom}' est terminé. {tickets_termines}/{tickets_total} tickets terminés.",
                        type_notification='INFO',
                        objet_id=sprint.id,
                        objet_type='sprint'
                    )
                    notifications.append(notification)
                    
            except ZY00.DoesNotExist:
                continue
        
        return notifications
    
    @staticmethod
    def notifier_ticket_en_retard(ticket):
        """Notifie qu'un ticket est en retard"""
        notifications = []
        
        notification = NotificationService.creer_notification(
            utilisateur=ticket.projet.chef_projet,
            titre=f"Ticket en retard : {ticket.code}",
            message=f"Le ticket '{ticket.titre}' ({ticket.priorite}) aurait dû être terminé le {ticket.date_echeance}",
            type_notification='WARNING',
            objet_id=ticket.id,
            objet_type='ticket',
            priorite='haute' if ticket.priorite == 'CRITIQUE' else 'normale'
        )
        notifications.append(notification)
        
        # Notifier aussi l'assigné
        if ticket.assigne and ticket.assigne != ticket.projet.chef_projet:
            notification = NotificationService.creer_notification(
                utilisateur=ticket.assigne,
                titre=f"Ticket en retard : {ticket.code}",
                message=f"Votre ticket '{ticket.titre}' est en retard (échéance: {ticket.date_echeance})",
                type_notification='WARNING',
                objet_id=ticket.id,
                objet_type='ticket',
                priorite='haute' if ticket.priorite == 'CRITIQUE' else 'normale'
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notifier_rappel_imputation(employe, date):
        """Notifie un employé pour lui rappeler d'imputer son temps"""
        notification = NotificationService.creer_notification(
            utilisateur=employe,
            titre="Rappel d'imputation de temps",
            message=f"N'oubliez pas d'imputer votre temps pour le {date}",
            type_notification='INFO',
            priorite='normale'
        )
        
        return [notification]
    
    @staticmethod
    def get_notifications_utilisateur(utilisateur, non_lues_seulement=False):
        """Récupère les notifications d'un utilisateur"""
        # Dans une implémentation complète, cela interrogerait un modèle Notification
        # Pour l'instant, on retourne une liste vide
        return []
    
    @staticmethod
    def marquer_notification_lue(notification_id, utilisateur):
        """Marque une notification comme lue"""
        # Dans une implémentation complète, cela mettrait à jour le modèle Notification
        pass
    
    @staticmethod
    def marquer_toutes_notifications_lues(utilisateur):
        """Marque toutes les notifications d'un utilisateur comme lues"""
        # Dans une implémentation complète, cela mettrait à jour plusieurs notifications
        pass
    
    @staticmethod
    def supprimer_notifications_anciennes(jours=30):
        """Supprime les anciennes notifications"""
        date_limite = timezone.now() - timezone.timedelta(days=jours)
        
        # Dans une implémentation complète, cela supprimerait du modèle Notification
        pass
    
    @staticmethod
    def envoyer_rapport_hebdomadaire(utilisateur):
        """Envoie un rapport hebdomadaire des activités"""
        from ..services import ImputationService
        
        # Générer le rapport
        rapport = ImputationService.get_rapport_hebdomadaire(utilisateur)
        
        if rapport['total_heures'] > 0:
            notification = NotificationService.creer_notification(
                utilisateur=utilisateur,
                titre="Rapport hebdomadaire",
                message=f"Cette semaine: {rapport['total_heures']}h imputées sur {rapport['total_imputations']} tâches",
                type_notification='INFO',
                priorite='basse'
            )
            
            return [notification]
        
        return []

from django.utils import timezone
from django.db import transaction
from ..models import JRTicket, JRHistorique, JRImputation, JRSprint


class WorkflowService:
    """Service pour la gestion des workflows et automatisations"""
    
    @staticmethod
    def executer_workflow_ticket(ticket, utilisateur, action, **kwargs):
        """Exécute un workflow pour un ticket"""
        
        if action == 'changer_statut':
            return WorkflowService._changer_statut_workflow(
                ticket, utilisateur, kwargs.get('nouveau_statut')
            )
        elif action == 'assigner':
            return WorkflowService._assigner_workflow(
                ticket, utilisateur, kwargs.get('assigne')
            )
        elif action == 'ajouter_au_sprint':
            return WorkflowService._ajouter_sprint_workflow(
                ticket, utilisateur, kwargs.get('sprint')
            )
        else:
            raise ValueError(f"Action de workflow non reconnue: {action}")
    
    @staticmethod
    def _changer_statut_workflow(ticket, utilisateur, nouveau_statut):
        """Workflow pour le changement de statut"""
        ancien_statut = ticket.statut
        
        # Validation de la transition
        from .ticket_service import TicketService
        if not TicketService.valider_transition_statut(ancien_statut, nouveau_statut):
            raise ValueError(f"Transition {ancien_statut} → {nouveau_statut} non autorisée")
        
        # Actions automatiques selon la transition
        with transaction.atomic():
            ticket.statut = nouveau_statut
            
            # Transition OUVERT → EN_COURS
            if ancien_statut == 'OUVERT' and nouveau_statut == 'EN_COURS':
                if not ticket.assigne:
                    raise ValueError("Le ticket doit être assigné pour passer en EN_COURS")
                
                # Sortir du backlog si nécessaire
                if ticket.dans_backlog:
                    ticket.dans_backlog = False
                    ticket.ordre_backlog = 0
            
            # Transition EN_COURS → EN_REVue
            elif ancien_statut == 'EN_COURS' and nouveau_statut == 'EN_REVue':
                # Vérifier qu'il y a eu du temps imputé
                temps_impute = JRImputation.objects.filter(
                    ticket=ticket,
                    statut_validation='VALIDE'
                ).exists()
                
                if not temps_impute:
                    # Avertissement mais pas d'erreur bloquante
                    pass
            
            # Transition EN_REVue → TERMINE
            elif ancien_statut == 'EN_REVue' and nouveau_statut == 'TERMINE':
                # Vérifier que le temps est validé
                temps_en_attente = JRImputation.objects.filter(
                    ticket=ticket,
                    statut_validation='EN_ATTENTE'
                ).exists()
                
                if temps_en_attente:
                    raise ValueError(
                        "Impossible de terminer le ticket : il y a des imputations en attente de validation"
                    )
            
            ticket.save()
            
            # Créer l'historique
            TicketService.creer_historique(
                ticket=ticket,
                utilisateur=utilisateur,
                type_changement='STATUT',
                champ_modifie='statut',
                ancienne_valeur=ancien_statut,
                nouvelle_valeur=nouveau_statut,
                description=f"Changement de statut : {ancien_statut} → {nouveau_statut}"
            )
            
            # Notifications automatiques
            WorkflowService._notifier_changement_statut(ticket, ancien_statut, nouveau_statut)
            
            return ticket
    
    @staticmethod
    def _assigner_workflow(ticket, utilisateur, assigne):
        """Workflow pour l'assignation d'un ticket"""
        ancien_assigne = ticket.assigne
        
        with transaction.atomic():
            ticket.assigne = assigne
            ticket.save()
            
            # Si le ticket est dans le backlog et qu'on l'assigne, on peut le proposer pour le prochain sprint
            if ticket.dans_backlog and assigne:
                pass  # Logique optionnelle
            
            # Créer l'historique
            from .ticket_service import TicketService
            TicketService.creer_historique(
                ticket=ticket,
                utilisateur=utilisateur,
                type_changement='ASSIGNATION',
                champ_modifie='assigne',
                ancienne_valeur=str(ancien_assigne) if ancien_assigne else 'Non assigné',
                nouvelle_valeur=str(assigne) if assigne else 'Non assigné',
                description=f"Réassignation du ticket"
            )
            
            # Notifications
            if assigne and assigne != ancien_assigne:
                WorkflowService._notifier_assignation(ticket, assigne)
            
            return ticket
    
    @staticmethod
    def _ajouter_sprint_workflow(ticket, utilisateur, sprint):
        """Workflow pour ajouter un ticket à un sprint"""
        with transaction.atomic():
            # Retirer le ticket du backlog
            if ticket.dans_backlog:
                ticket.dans_backlog = False
                ticket.ordre_backlog = 0
            
            # Ajouter au sprint
            sprint.tickets.add(ticket)
            
            # Créer l'historique
            from .ticket_service import TicketService
            TicketService.creer_historique(
                ticket=ticket,
                utilisateur=utilisateur,
                type_changement='MODIFICATION',
                champ_modifie='sprint',
                ancienne_valeur='Backlog' if ticket.dans_backlog else 'Aucun',
                nouvelle_valeur=sprint.nom,
                description=f"Ajout au sprint {sprint.nom}"
            )
            
            return ticket
    
    @staticmethod
    def _notifier_changement_statut(ticket, ancien_statut, nouveau_statut):
        """Notifications automatiques lors du changement de statut"""
        # Importer ici pour éviter les imports circulaires
        try:
            from .notification_service import NotificationService
            
            # Notifier l'assigné
            if ticket.assigne:
                NotificationService.creer_notification(
                    utilisateur=ticket.assigne,
                    titre=f"Changement de statut du ticket {ticket.code}",
                    message=f"Le ticket {ticket.titre} est passé de {ancien_statut} à {nouveau_statut}",
                    type_notification='CHANGEMENT_STATUT',
                    objet_id=ticket.id,
                    objet_type='ticket'
                )
            
            # Notifier le chef de projet
            if ticket.projet.chef_projet and ticket.projet.chef_projet != ticket.assigne:
                NotificationService.creer_notification(
                    utilisateur=ticket.projet.chef_projet,
                    titre=f"Changement de statut du ticket {ticket.code}",
                    message=f"Le ticket {ticket.titre} est passé de {ancien_statut} à {nouveau_statut}",
                    type_notification='CHANGEMENT_STATUT',
                    objet_id=ticket.id,
                    objet_type='ticket'
                )
                
        except ImportError:
            # Le service de notification n'est pas encore implémenté
            pass
    
    @staticmethod
    def _notifier_assignation(ticket, assigne):
        """Notifications lors de l'assignation d'un ticket"""
        try:
            from .notification_service import NotificationService
            
            NotificationService.creer_notification(
                utilisateur=assigne,
                titre=f"Nouvelle assignation : {ticket.code}",
                message=f"Vous avez été assigné au ticket {ticket.titre}",
                type_notification='ASSIGNATION',
                objet_id=ticket.id,
                objet_type='ticket'
            )
                
        except ImportError:
            pass
    
    @staticmethod
    def verifier_alertes_automatiques():
        """Vérifie et génère des alertes automatiques"""
        alertes = []
        
        # Tickets en retard
        tickets_en_retard = JRTicket.objects.filter(
            date_echeance__lt=timezone.now().date(),
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        ).select_related('projet', 'assigne')
        
        for ticket in tickets_en_retard:
            alertes.append({
                'type': 'ticket_en_retard',
                'titre': f"Ticket en retard : {ticket.code}",
                'message': f"Le ticket {ticket.titre} aurait dû être terminé le {ticket.date_echeance}",
                'priorite': 'haute' if ticket.priorite == 'CRITIQUE' else 'moyenne',
                'objet': ticket
            })
        
        # Imputations en attente depuis plus de 3 jours
        delai_alerte = timezone.now() - timezone.timedelta(days=3)
        imputations_anciennes = JRImputation.objects.filter(
            statut_validation='EN_ATTENTE',
            created_at__lt=delai_alerte
        ).select_related('employe', 'ticket', 'ticket__projet')
        
        for imp in imputations_anciennes:
            alertes.append({
                'type': 'imputation_en_attente',
                'titre': f"Imputation en attente : {imp.ticket.code}",
                'message': f"L'imputation de {imp.employe} est en attente depuis le {imp.created_at.date()}",
                'priorite': 'moyenne',
                'objet': imp
            })
        
        # Sprints qui se terminent bientôt (dans 2 jours)
        fin_sprint_proche = timezone.now().date() + timezone.timedelta(days=2)
        sprints_fin_proche = JRSprint.objects.filter(
            statut='ACTIF',
            date_fin=fin_sprint_proche
        ).select_related('projet')
        
        for sprint in sprints_fin_proche:
            tickets_non_termines = sprint.tickets.filter(
                statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
            ).count()
            
            if tickets_non_termines > 0:
                alertes.append({
                    'type': 'sprint_fin_proche',
                    'titre': f"Sprint bientôt terminé : {sprint.nom}",
                    'message': f"Le sprint se termine demain avec {tickets_non_termines} ticket(s) non terminé(s)",
                    'priorite': 'haute',
                    'objet': sprint
                })
        
        return alertes
    
    @staticmethod
    def nettoyer_donnees_anciennes(jours=365):
        """Nettoie les anciennes données (historique, etc.)"""
        date_limite = timezone.now() - timezone.timedelta(days=jours)
        
        # Supprimer l'historique ancien
        historique_supprime = JRHistorique.objects.filter(
            created_at__lt=date_limite
        ).delete()
        
        # Archiver les tickets terminés depuis longtemps
        tickets_archives = JRTicket.objects.filter(
            statut='TERMINE',
            updated_at__lt=date_limite
        ).update(statut='ARCHIVE')  # Supposer qu'on a un statut ARCHIVE
        
        return {
            'historique_supprime': historique_supprime[0],
            'tickets_archives': tickets_archives
        }
    
    @staticmethod
    def generer_rapport_quotidien():
        """Génère un rapport quotidien de l'activité"""
        aujourd_hui = timezone.now().date()
        
        # Tickets créés aujourd'hui
        tickets_crees = JRTicket.objects.filter(
            created_at__date=aujourd_hui
        ).count()
        
        # Tickets terminés aujourd'hui
        tickets_termines = JRTicket.objects.filter(
            updated_at__date=aujourd_hui,
            statut='TERMINE'
        ).count()
        
        # Imputations validées aujourd'hui
        imputations_validees = JRImputation.objects.filter(
            date_validation__date=aujourd_hui,
            statut_validation='VALIDE'
        ).count()
        
        # Heures imputées aujourd'hui
        heures_imputees = JRImputation.objects.filter(
            date_validation__date=aujourd_hui,
            statut_validation='VALIDE'
        ).aggregate(
            total=models.Sum(models.F('heures') + models.F('minutes') / 60.0)
        )['total'] or 0
        
        return {
            'date': aujourd_hui,
            'tickets_crees': tickets_crees,
            'tickets_termines': tickets_termines,
            'imputations_validees': imputations_validees,
            'heures_imputees': heures_imputees,
        }
    
    @staticmethod
    def calculer_kpi_projet(projet):
        """Calcule les KPI pour un projet"""
        tickets = JRTicket.objects.filter(projet=projet)
        
        # Taux de complétion
        total_tickets = tickets.count()
        tickets_termines = tickets.filter(statut='TERMINE').count()
        taux_completion = (tickets_termines / total_tickets * 100) if total_tickets > 0 else 0
        
        # Temps moyen de résolution
        tickets_resolus = tickets.filter(statut='TERMINE')
        temps_moyen_resolution = 0
        if tickets_resolus.exists():
            temps_total = sum(
                (ticket.updated_at - ticket.created_at).total_seconds() / 3600
                for ticket in tickets_resolus
            )
            temps_moyen_resolution = temps_total / tickets_resolus.count()
        
        # Respect des délais
        tickets_en_retard = tickets.filter(
            date_echeance__lt=models.F('updated_at'),
            statut='TERMINE'
        ).count()
        
        respect_delais = ((tickets_termines - tickets_en_retard) / tickets_termines * 100) if tickets_termines > 0 else 0
        
        # Estimation vs Réel
        estimation_totale = tickets.aggregate(
            total=models.Sum('estimation_heures')
        )['total'] or 0
        
        temps_reel = tickets.aggregate(
            total=models.Sum('temps_passe')
        )['total'] or 0
        
        precision_estimation = (estimation_totale / temps_reel * 100) if temps_reel > 0 else 100
        
        return {
            'taux_completion': round(taux_completion, 2),
            'temps_moyen_resolution': round(temps_moyen_resolution, 2),
            'respect_delais': round(respect_delais, 2),
            'precision_estimation': round(precision_estimation, 2),
            'estimation_totale': estimation_totale,
            'temps_reel': temps_reel,
        }

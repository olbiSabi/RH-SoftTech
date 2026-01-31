from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..models import JRTicket, JRHistorique
from employee.models import ZY00

User = get_user_model()


class TicketService:
    """Service pour la gestion des tickets"""

    @staticmethod
    def get_employe_from_user(user):
        """
        Récupère l'employé ZY00 à partir d'un utilisateur Django.
        Accepte soit un User Django soit directement un ZY00.
        """
        if user is None:
            return None

        # Si c'est déjà un ZY00, le retourner directement
        if isinstance(user, ZY00):
            return user

        # Sinon, essayer de récupérer le ZY00 lié à cet utilisateur
        try:
            return ZY00.objects.get(user=user)
        except ZY00.DoesNotExist:
            return None

    @staticmethod
    def creer_historique(ticket, utilisateur, type_changement,
                        champ_modifie=None, ancienne_valeur=None,
                        nouvelle_valeur=None, description=None):
        """Crée une entrée dans l'historique du ticket"""
        # Convertir l'utilisateur Django en ZY00 si nécessaire
        employe = TicketService.get_employe_from_user(utilisateur)

        if employe is None:
            # Si aucun employé trouvé, ne pas créer l'historique
            return None

        return JRHistorique.objects.create(
            ticket=ticket,
            utilisateur=employe,
            type_changement=type_changement,
            champ_modifie=champ_modifie,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description or f"{type_changement} sur le ticket {ticket.code}"
        )
    
    @staticmethod
    def tracker_changements(old_instance, new_instance, utilisateur):
        """Track les changements entre deux versions d'un ticket"""
        changements = []
        
        # Champs à tracker
        champs_tracker = [
            'titre', 'description', 'priorite', 'statut', 'assigne_id',
            'type_ticket', 'estimation_heures', 'date_echeance',
            'dans_backlog', 'ordre_backlog'
        ]
        
        for champ in champs_tracker:
            ancienne_valeur = getattr(old_instance, champ)
            nouvelle_valeur = getattr(new_instance, champ)
            
            if ancienne_valeur != nouvelle_valeur:
                # Formater les valeurs pour l'affichage
                ancienne_formatee = TicketService.formater_valeur(champ, ancienne_valeur)
                nouvelle_formatee = TicketService.formater_valeur(champ, nouvelle_valeur)
                
                # Déterminer le type de changement
                type_changement = TicketService.get_type_changement(champ)
                
                # Créer l'historique
                TicketService.creer_historique(
                    ticket=new_instance,
                    utilisateur=utilisateur,
                    type_changement=type_changement,
                    champ_modifie=champ,
                    ancienne_valeur=ancienne_formatee,
                    nouvelle_valeur=nouvelle_formatee,
                    description=f"Modification du champ {champ}: {ancienne_formatee} → {nouvelle_formatee}"
                )
                
                changements.append({
                    'champ': champ,
                    'ancienne': ancienne_formatee,
                    'nouvelle': nouvelle_formatee
                })
        
        return changements
    
    @staticmethod
    def formater_valeur(champ, valeur):
        """Formate une valeur pour l'affichage dans l'historique"""
        if valeur is None:
            return 'Aucune'
        
        if champ == 'assigne_id':
            if valeur:
                try:
                    from employee.models import ZY00
                    employe = ZY00.objects.get(pk=valeur)
                    return f"{employe.nom} {employe.prenom}"
                except ZY00.DoesNotExist:
                    return f"Employé #{valeur}"
            return 'Non assigné'
        
        if champ == 'date_echeance':
            return valeur.strftime('%d/%m/%Y') if valeur else 'Aucune'
        
        if champ == 'estimation_heures':
            return f"{valeur}h" if valeur else 'Aucune'
        
        if champ == 'dans_backlog':
            return 'Oui' if valeur else 'Non'
        
        if champ == 'ordre_backlog':
            return str(valeur) if valeur else '0'
        
        # Pour les champs avec choices
        if champ == 'priorite':
            return dict(JRTicket.PRIORITE_CHOICES).get(valeur, valeur)
        
        if champ == 'statut':
            return dict(JRTicket.STATUT_CHOICES).get(valeur, valeur)
        
        if champ == 'type_ticket':
            return dict(JRTicket.TYPE_CHOICES).get(valeur, valeur)
        
        return str(valeur)
    
    @staticmethod
    def get_type_changement(champ):
        """Détermine le type de changement en fonction du champ"""
        mapping = {
            'statut': 'STATUT',
            'assigne_id': 'ASSIGNATION',
            'priorite': 'PRIORITE',
            'titre': 'MODIFICATION',
            'description': 'MODIFICATION',
            'type_ticket': 'MODIFICATION',
            'estimation_heures': 'MODIFICATION',
            'date_echeance': 'MODIFICATION',
            'dans_backlog': 'MODIFICATION',
            'ordre_backlog': 'MODIFICATION',
        }
        
        return mapping.get(champ, 'MODIFICATION')
    
    @staticmethod
    def valider_transition_statut(ancien_statut, nouveau_statut):
        """Valide si une transition de statut est autorisée"""
        # Matrice des transitions autorisées
        transitions_autorisees = {
            'OUVERT': ['EN_COURS', 'TERMINE'],
            'EN_COURS': ['OUVERT', 'EN_REVue', 'TERMINE'],
            'EN_REVue': ['EN_COURS', 'TERMINE'],
            'TERMINE': ['OUVERT', 'EN_COURS', 'EN_REVue'],  # Réouverture possible
        }
        
        return nouveau_statut in transitions_autorisees.get(ancien_statut, [])
    
    @staticmethod
    def get_tickets_en_retard():
        """Retourne les tickets en retard (date d'échéance dépassée)"""
        return JRTicket.objects.filter(
            date_echeance__lt=timezone.now().date(),
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        ).select_related('projet', 'assigne')
    
    @staticmethod
    def get_tickets_sans_assignation():
        """Retourne les tickets non assignés"""
        return JRTicket.objects.filter(
            assigne__isnull=True,
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        ).select_related('projet')
    
    @staticmethod
    def get_tickets_critiques():
        """Retourne les tickets avec priorité critique"""
        return JRTicket.objects.filter(
            priorite='CRITIQUE',
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        ).select_related('projet', 'assigne')
    
    @staticmethod
    def calculer_charge_projet(projet):
        """Calcule la charge de travail totale d'un projet"""
        tickets = JRTicket.objects.filter(projet=projet)
        
        charge_totale = 0
        charge_par_statut = {}
        
        for statut, label in JRTicket.STATUT_CHOICES:
            tickets_statut = tickets.filter(statut=statut)
            charge = sum(
                ticket.estimation_heures or 0 
                for ticket in tickets_statut
            )
            charge_par_statut[statut] = {
                'label': label,
                'nombre': tickets_statut.count(),
                'charge_estimee': charge,
                'charge_reelle': sum(
                    ticket.temps_passe or 0 
                    for ticket in tickets_statut
                )
            }
            charge_totale += charge
        
        return {
            'charge_totale': charge_totale,
            'par_statut': charge_par_statut,
            'nombre_total': tickets.count()
        }
    
    @staticmethod
    def get_stats_employe(employe):
        """Retourne les statistiques d'un employé"""
        tickets = JRTicket.objects.filter(assigne=employe)
        
        stats = {
            'total_assignes': tickets.count(),
            'termines': tickets.filter(statut='TERMINE').count(),
            'en_cours': tickets.filter(statut='EN_COURS').count(),
            'en_retard': tickets.filter(
                date_echeance__lt=timezone.now().date(),
                statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
            ).count(),
            'charge_totale': sum(
                ticket.estimation_heures or 0 
                for ticket in tickets
            ),
            'temps_passe_total': sum(
                ticket.temps_passe or 0 
                for ticket in tickets
            ),
            'par_priorite': {},
            'par_type': {},
        }
        
        # Stats par priorité
        for priorite, label in JRTicket.PRIORITE_CHOICES:
            stats['par_priorite'][priorite] = {
                'label': label,
                'nombre': tickets.filter(priorite=priorite).count()
            }
        
        # Stats par type
        for type_ticket, label in JRTicket.TYPE_CHOICES:
            stats['par_type'][type_ticket] = {
                'label': label,
                'nombre': tickets.filter(type_ticket=type_ticket).count()
            }
        
        return stats
    
    @staticmethod
    def rechercher_tickets(requete, utilisateur=None):
        """Recherche avancée de tickets"""
        queryset = JRTicket.objects.select_related('projet', 'assigne', 'projet__client')
        
        # Filtrer par utilisateur si spécifié
        if utilisateur:
            queryset = queryset.filter(
                models.Q(assigne=utilisateur) | 
                models.Q(projet__chef_projet=utilisateur)
            )
        
        # Recherche textuelle
        if requete:
            queryset = queryset.filter(
                models.Q(titre__icontains=requete) |
                models.Q(code__icontains=requete) |
                models.Q(description__icontains=requete) |
                models.Q(projet__nom__icontains=requete) |
                models.Q(projet__client__raison_sociale__icontains=requete)
            )
        
        return queryset.distinct()

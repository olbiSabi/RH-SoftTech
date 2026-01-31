from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, Count, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import JRTicket, JRProject
from ..forms import BacklogForm


@method_decorator(login_required, name='dispatch')
class BacklogListView(LoginRequiredMixin, ListView):
    """Vue pour la gestion du backlog"""
    model = JRTicket
    template_name = 'project_management/backlog/backlog.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        # Récupérer le projet sélectionné
        projet_id = self.request.GET.get('projet')
        
        if projet_id:
            self.projet = get_object_or_404(JRProject, pk=projet_id)
            queryset = JRTicket.objects.filter(
                projet=self.projet,
                dans_backlog=True
            ).select_related('assigne').order_by('ordre_backlog', 'created_at')
        else:
            self.projet = None
            queryset = JRTicket.objects.filter(
                dans_backlog=True
            ).select_related('projet', 'assigne').order_by('ordre_backlog', 'created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projet'] = self.projet
        context['projets'] = JRProject.objects.filter(
            statut__in=['PLANIFIE', 'ACTIF']
        ).order_by('nom')

        # Statistiques du backlog (toujours fournies)
        tickets_backlog = context['tickets']
        context['stats'] = {
            'total': tickets_backlog.count(),
            'non_assignes': tickets_backlog.filter(assigne__isnull=True).count(),
            'haute_priorite': tickets_backlog.filter(priorite='HAUTE').count(),
            'critique': tickets_backlog.filter(priorite='CRITIQUE').count(),
        }

        return context


@login_required
def backlog_projet(request, pk):
    """Vue pour le backlog d'un projet spécifique"""
    projet = get_object_or_404(JRProject, pk=pk)
    
    # Tickets dans le backlog
    tickets_backlog = JRTicket.objects.filter(
        projet=projet,
        dans_backlog=True
    ).select_related('assigne').order_by('ordre_backlog', 'created_at')
    
    # Tickets non dans le backlog (pour pouvoir les ajouter)
    tickets_disponibles = JRTicket.objects.filter(
        projet=projet,
        dans_backlog=False,
        statut='OUVERT'
    ).select_related('assigne').order_by('-created_at')
    
    context = {
        'projet': projet,
        'tickets_backlog': tickets_backlog,
        'tickets_disponibles': tickets_disponibles,
        'stats': {
            'total': tickets_backlog.count(),
            'non_assignes': tickets_backlog.filter(assigne__isnull=True).count(),
            'haute_priorite': tickets_backlog.filter(priorite='HAUTE').count(),
            'critique': tickets_backlog.filter(priorite='CRITIQUE').count(),
        }
    }
    
    return render(request, 'project_management/backlog/backlog_projet.html', context)


@login_required
@require_POST
def backlog_ajouter_ticket(request, pk):
    """Vue pour ajouter un ticket au backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    ticket_id = request.POST.get('ticket_id')
    
    if ticket_id:
        ticket = get_object_or_404(JRTicket, pk=ticket_id, projet=projet)
        
        if not ticket.dans_backlog:
            ticket.dans_backlog = True
            # Définir l'ordre comme le plus élevé existant + 1
            max_ordre = JRTicket.objects.filter(
                projet=projet,
                dans_backlog=True
            ).aggregate(max_ordre=Max('ordre_backlog'))['max_ordre'] or 0
            ticket.ordre_backlog = max_ordre + 1
            ticket.save()
            
            messages.success(request, f'Ticket {ticket.code} ajouté au backlog.')
        else:
            messages.warning(request, f'Ticket {ticket.code} est déjà dans le backlog.')
    
    return redirect('pm:backlog_projet', pk=pk)


@login_required
@require_POST
def backlog_retirer_ticket(request, pk):
    """Vue pour retirer un ticket du backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    ticket_id = request.POST.get('ticket_id')
    
    if ticket_id:
        ticket = get_object_or_404(JRTicket, pk=ticket_id, projet=projet)
        
        if ticket.dans_backlog:
            ticket.dans_backlog = False
            ticket.ordre_backlog = 0
            ticket.save()
            
            messages.success(request, f'Ticket {ticket.code} retiré du backlog.')
        else:
            messages.warning(request, f'Ticket {ticket.code} n\'est pas dans le backlog.')
    
    return redirect('pm:backlog_projet', pk=pk)


@csrf_exempt
@login_required
@require_POST
def backlog_reorganiser(request):
    """Vue pour réorganiser l'ordre des tickets dans le backlog (AJAX)"""
    ticket_orders = request.POST.get('orders', '{}')
    
    try:
        import json
        orders = json.loads(ticket_orders)
        
        for ticket_id, ordre in orders.items():
            try:
                ticket = JRTicket.objects.get(pk=ticket_id, dans_backlog=True)
                ticket.ordre_backlog = int(ordre)
                ticket.save()
            except JRTicket.DoesNotExist:
                continue
        
        return JsonResponse({'success': True})
    
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Format invalide'})


@login_required
def backlog_priorisation(request, pk):
    """Vue pour la priorisation du backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    
    # Tickets dans le backlog organisés par priorité
    tickets_backlog = JRTicket.objects.filter(
        projet=projet,
        dans_backlog=True
    ).select_related('assigne').order_by('-priorite', 'ordre_backlog')
    
    # Regrouper par priorité
    tickets_par_priorite = {}
    for priorite, label in JRTicket.PRIORITE_CHOICES:
        tickets_par_priorite[priorite] = tickets_backlog.filter(priorite=priorite)
    
    context = {
        'projet': projet,
        'tickets_par_priorite': tickets_par_priorite,
        'priorite_choices': JRTicket.PRIORITE_CHOICES,
    }
    
    return render(request, 'project_management/backlog/backlog_priorisation.html', context)


@login_required
@require_POST
def backlog_changer_priorite(request, pk):
    """Vue pour changer la priorité d'un ticket dans le backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    ticket_id = request.POST.get('ticket_id')
    nouvelle_priorite = request.POST.get('priorite')
    
    if ticket_id and nouvelle_priorite:
        ticket = get_object_or_404(JRTicket, pk=ticket_id, projet=projet)
        
        if nouvelle_priorite in dict(JRTicket.PRIORITE_CHOICES):
            ancienne_priorite = ticket.priorite
            ticket.priorite = nouvelle_priorite
            ticket.save()
            
            # Créer l'historique
            from ..services import TicketService
            TicketService.creer_historique(
                ticket=ticket,
                utilisateur=request.user,
                type_changement='PRIORITE',
                champ_modifie='priorite',
                ancienne_valeur=ancienne_priorite,
                nouvelle_valeur=nouvelle_priorite,
                description=f"Changement de priorité dans le backlog : {ancienne_priorite} → {nouvelle_priorite}"
            )
            
            messages.success(
                request, 
                f'Priorité du ticket {ticket.code} changée en {nouvelle_priorite}.'
            )
        else:
            messages.error(request, 'Priorité invalide.')
    
    return redirect('pm:backlog_priorisation', pk=pk)


@login_required
def backlog_planning_sprint(request, pk):
    """Vue pour planifier un sprint à partir du backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    
    # Tickets dans le backlog
    tickets_backlog = JRTicket.objects.filter(
        projet=projet,
        dans_backlog=True
    ).select_related('assigne').order_by('ordre_backlog')
    
    # Estimation de la capacité (basée sur les sprints précédents ou par défaut)
    capacite_heures = 40  # Par défaut : 1 semaine * 8h/jour * 5 jours
    
    # Calculer la charge totale du backlog
    charge_totale = sum(
        ticket.estimation_heures or 0 
        for ticket in tickets_backlog
    )
    
    context = {
        'projet': projet,
        'tickets_backlog': tickets_backlog,
        'capacite_heures': capacite_heures,
        'charge_totale': charge_totale,
        'tickets_suggerees': [],  # Suggestion basée sur la capacité
    }
    
    # Suggérer des tickets pour le sprint
    charge_actuelle = 0
    for ticket in tickets_backlog:
        estimation = ticket.estimation_heures or 0
        if charge_actuelle + estimation <= capacite_heures:
            context['tickets_suggerees'].append(ticket)
            charge_actuelle += estimation
        else:
            break
    
    return render(request, 'project_management/backlog/backlog_planning_sprint.html', context)


@login_required
@require_POST
def backlog_creer_sprint(request, pk):
    """Vue pour créer un sprint à partir des tickets sélectionnés du backlog"""
    projet = get_object_or_404(JRProject, pk=pk)
    
    from ..models import JRSprint
    from ..forms import SprintForm
    
    if request.method == 'POST':
        form = SprintForm(request.POST)
        ticket_ids = request.POST.getlist('tickets')
        
        if form.is_valid() and ticket_ids:
            # Créer le sprint
            sprint = form.save(commit=False)
            sprint.projet = projet
            sprint.save()
            
            # Ajouter les tickets au sprint
            tickets = JRTicket.objects.filter(
                pk__in=ticket_ids,
                projet=projet,
                dans_backlog=True
            )
            
            sprint.tickets.set(tickets)
            
            # Retirer les tickets du backlog
            tickets.update(dans_backlog=False, ordre_backlog=0)
            
            messages.success(
                request, 
                f'Sprint "{sprint.nom}" créé avec {tickets.count()} ticket(s).'
            )
            
            return redirect('pm:sprint_detail', pk=sprint.pk)
        else:
            messages.error(request, 'Erreur lors de la création du sprint.')
    
    return redirect('pm:backlog_planning_sprint', pk=pk)


@login_required
def backlog_stats_api(request, pk=None):
    """API pour les statistiques du backlog"""
    if pk:
        projet = get_object_or_404(JRProject, pk=pk)
        tickets = JRTicket.objects.filter(projet=projet, dans_backlog=True)
    else:
        projet = None
        tickets = JRTicket.objects.filter(dans_backlog=True)
    
    stats = {
        'total_tickets': tickets.count(),
        'par_priorite': list(
            tickets.values('priorite')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'par_type': list(
            tickets.values('type_ticket')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'non_assignes': tickets.filter(assigne__isnull=True).count(),
        'avec_estimation': tickets.filter(estimation_heures__isnull=False).count(),
        'estimation_totale': tickets.aggregate(
            total=Sum('estimation_heures')
        )['total'] or 0,
    }
    
    if projet:
        stats['projet'] = {
            'code': projet.code,
            'nom': projet.nom,
        }
    
    return JsonResponse(stats)

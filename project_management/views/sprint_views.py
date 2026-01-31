from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, FloatField, ExpressionWrapper
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

from ..models import JRSprint, JRProject, JRTicket, JRImputation
from ..forms import SprintForm, SprintSearchForm, SprintTicketForm


@method_decorator(login_required, name='dispatch')
class SprintListView(LoginRequiredMixin, ListView):
    """Vue pour la liste des sprints"""
    model = JRSprint
    template_name = 'project_management/sprint/sprint_list.html'
    context_object_name = 'sprints'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = JRSprint.objects.select_related('projet', 'projet__client')
        
        # Recherche
        search_form = SprintSearchForm(self.request.GET)
        if search_form.is_valid():
            recherche = search_form.cleaned_data.get('recherche')
            projet = search_form.cleaned_data.get('projet')
            statut = search_form.cleaned_data.get('statut')
            date_debut_min = search_form.cleaned_data.get('date_debut_min')
            date_debut_max = search_form.cleaned_data.get('date_debut_max')
            
            if recherche:
                queryset = queryset.filter(
                    Q(nom__icontains=recherche) |
                    Q(description__icontains=recherche)
                )
            
            if projet:
                queryset = queryset.filter(projet=projet)
            
            if statut:
                queryset = queryset.filter(statut=statut)
            
            if date_debut_min:
                queryset = queryset.filter(date_debut__gte=date_debut_min)
            
            if date_debut_max:
                queryset = queryset.filter(date_debut__lte=date_debut_max)
        
        return queryset.order_by('-date_debut')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SprintSearchForm(self.request.GET)

        # Données pour les filtres
        context['projets'] = JRProject.objects.all().order_by('nom')

        # Statistiques
        context['total_sprints'] = JRSprint.objects.count()
        context['sprints_actifs'] = JRSprint.objects.filter(statut='ACTIF').count()
        context['sprints_planifies'] = JRSprint.objects.filter(statut='PLANIFIE').count()
        context['sprints_termines'] = JRSprint.objects.filter(statut='TERMINE').count()

        return context


@method_decorator(login_required, name='dispatch')
class SprintCreateView(LoginRequiredMixin, CreateView):
    """Vue pour la création d'un sprint"""
    model = JRSprint
    form_class = SprintForm
    template_name = 'project_management/sprint/sprint_form.html'
    success_url = reverse_lazy('pm:sprint_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sprint {form.instance.nom} créé avec succès.')
        return response


@method_decorator(login_required, name='dispatch')
class SprintUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour la modification d'un sprint"""
    model = JRSprint
    form_class = SprintForm
    template_name = 'project_management/sprint/sprint_form.html'
    success_url = reverse_lazy('pm:sprint_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sprint {form.instance.nom} modifié avec succès.')
        return response


@login_required
def sprint_detail(request, pk):
    """Vue pour le détail d'un sprint"""
    sprint = get_object_or_404(
        JRSprint.objects.select_related('projet', 'projet__client'),
        pk=pk
    )
    
    # Tickets du sprint
    tickets = sprint.tickets.select_related('assigne').order_by('ordre_backlog', 'created_at')
    
    # Statistiques des tickets
    stats_tickets = {
        'total': tickets.count(),
        'ouverts': tickets.filter(statut='OUVERT').count(),
        'en_cours': tickets.filter(statut='EN_COURS').count(),
        'en_revue': tickets.filter(statut='EN_REVue').count(),
        'termines': tickets.filter(statut='TERMINE').count(),
    }
    
    # Imputations du sprint
    imputations = JRImputation.objects.filter(
        ticket__in=tickets,
        statut_validation='VALIDE'
    ).select_related('employe', 'ticket')
    
    # Temps total par employé
    temps_par_employe = imputations.values('employe__nom', 'employe__prenoms').annotate(
        total_heures=ExpressionWrapper(
            Sum('heures') + Sum('minutes') / 60.0,
            output_field=FloatField()
        )
    ).order_by('-total_heures')
    
    # Estimation vs réel
    estimation_totale = sum(ticket.estimation_heures or 0 for ticket in tickets)
    temps_reel = sum(item['total_heures'] for item in temps_par_employe)
    
    context = {
        'sprint': sprint,
        'tickets': tickets,
        'stats_tickets': stats_tickets,
        'temps_par_employe': temps_par_employe,
        'estimation_totale': estimation_totale,
        'temps_reel': temps_reel,
        'total_heures_sprint': temps_reel,
    }
    
    return render(request, 'project_management/sprint/sprint_detail.html', context)


@login_required
def sprint_board(request, pk):
    """Vue pour le tableau Kanban du sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    # Tickets du sprint organisés par statut
    tickets = sprint.tickets.select_related('assigne')
    
    tickets_par_statut = {
        'OUVERT': tickets.filter(statut='OUVERT'),
        'EN_COURS': tickets.filter(statut='EN_COURS'),
        'EN_REVue': tickets.filter(statut='EN_REVue'),
        'TERMINE': tickets.filter(statut='TERMINE'),
    }
    
    context = {
        'sprint': sprint,
        'tickets_par_statut': tickets_par_statut,
    }
    
    return render(request, 'project_management/sprint/sprint_board.html', context)


@login_required
def sprint_tickets(request, pk):
    """Vue pour gérer les tickets d'un sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    if request.method == 'POST':
        form = SprintTicketForm(sprint.projet, request.POST, instance=sprint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tickets du sprint mis à jour avec succès.')
            return redirect('pm:sprint_detail', pk=pk)
    else:
        form = SprintTicketForm(sprint.projet, instance=sprint)
    
    # Tickets disponibles pour le sprint (non terminés et pas dans d'autres sprints actifs)
    tickets_disponibles = JRTicket.objects.filter(
        projet=sprint.projet,
        statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
    ).exclude(
        id__in=sprint.tickets.all()
    ).select_related('assigne').order_by('ordre_backlog', 'created_at')
    
    context = {
        'sprint': sprint,
        'form': form,
        'tickets_disponibles': tickets_disponibles,
        'tickets_actuels': sprint.tickets.select_related('assigne').order_by('ordre_backlog'),
    }
    
    return render(request, 'project_management/sprint/sprint_tickets.html', context)


@login_required
@require_POST
def sprint_demarrer(request, pk):
    """Vue pour démarrer un sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    if sprint.statut == 'PLANIFIE':
        # Vérifier qu'il n'y a pas déjà un sprint actif pour ce projet
        sprint_actif = JRSprint.objects.filter(
            projet=sprint.projet,
            statut='ACTIF'
        ).first()
        
        if sprint_actif:
            messages.error(
                request, 
                f'Impossible de démarrer ce sprint : le sprint "{sprint_actif.nom}" est déjà actif.'
            )
        else:
            sprint.statut = 'ACTIF'
            sprint.save()
            messages.success(request, f'Sprint "{sprint.nom}" démarré avec succès.')
    else:
        messages.warning(request, 'Seuls les sprints planifiés peuvent être démarrés.')

    return redirect('pm:sprint_detail', pk=pk)


@login_required
@require_POST
def sprint_terminer(request, pk):
    """Vue pour terminer un sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    if sprint.statut == 'ACTIF':
        sprint.statut = 'TERMINE'
        sprint.save()
        messages.success(request, f'Sprint "{sprint.nom}" terminé avec succès.')
        
        # Optionnel : déplacer les tickets non terminés vers le backlog
        tickets_non_termines = sprint.tickets.filter(
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
        )
        
        if tickets_non_termines.exists():
            tickets_non_termines.update(dans_backlog=True, ordre_backlog=0)
            messages.info(
                request, 
                f'{tickets_non_termines.count()} ticket(s) non terminé(s) ont été déplacés dans le backlog.'
            )
    else:
        messages.warning(request, 'Seuls les sprints actifs peuvent être terminés.')

    return redirect('pm:sprint_detail', pk=pk)


@login_required
@require_POST
def sprint_supprimer(request, pk):
    """Vue pour supprimer un sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    if sprint.statut == 'ACTIF':
        messages.error(request, 'Impossible de supprimer un sprint actif.')
        return redirect('pm:sprint_detail', pk=pk)

    nom_sprint = sprint.nom
    sprint.delete()
    messages.success(request, f'Sprint "{nom_sprint}" supprimé avec succès.')
    return redirect('pm:sprint_list')


@login_required
def sprint_rapport(request, pk):
    """Vue pour le rapport d'un sprint"""
    sprint = get_object_or_404(JRSprint, pk=pk)
    
    # Tickets du sprint
    tickets = sprint.tickets.select_related('assigne')
    
    # Imputations du sprint
    imputations = JRImputation.objects.filter(
        ticket__in=tickets,
        statut_validation='VALIDE'
    ).select_related('employe', 'ticket')
    
    # Statistiques détaillées
    rapport = {
        'sprint': {
            'nom': sprint.nom,
            'description': sprint.description,
            'duree_jours': sprint.duree_jours,
            'statut': sprint.statut,
            'date_debut': sprint.date_debut,
            'date_fin': sprint.date_fin,
        },
        'tickets': {
            'total': tickets.count(),
            'termines': tickets.filter(statut='TERMINE').count(),
            'non_termines': tickets.filter(
                statut__in=['OUVERT', 'EN_COURS', 'EN_REVue']
            ).count(),
            'par_type': list(
                tickets.values('type_ticket')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'par_priorite': list(
                tickets.values('priorite')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        },
        'temps': {
            'estimation_totale': sum(
                ticket.estimation_heures or 0 for ticket in tickets
            ),
            'temps_reel': imputations.aggregate(
                total=ExpressionWrapper(
                    Sum('heures') + Sum('minutes') / 60.0,
                    output_field=FloatField()
                )
            )['total'] or 0,
            'par_employe': list(
                imputations.values('employe__nom', 'employe__prenoms')
                .annotate(
                    total_heures=ExpressionWrapper(
                        Sum('heures') + Sum('minutes') / 60.0,
                        output_field=FloatField()
                    ),
                    nombre_tickets=Count('ticket', distinct=True)
                )
                .order_by('-total_heures')
            ),
            'par_type_activite': list(
                imputations.values('type_activite')
                .annotate(
                    total_heures=ExpressionWrapper(
                        Sum('heures') + Sum('minutes') / 60.0,
                        output_field=FloatField()
                    ),
                    count=Count('id')
                )
                .order_by('-total_heures')
            ),
        },
        'performance': {
            'progression': sprint.progression,
            'efficacite': 0,  # Temps estimé / Temps réel
        }
    }
    
    # Calculer l'efficacité
    if rapport['temps']['estimation_totale'] > 0:
        rapport['performance']['efficacite'] = (
            rapport['temps']['estimation_totale'] / 
            max(rapport['temps']['temps_reel'], 0.01)
        ) * 100
    
    context = {
        'sprint': sprint,
        'rapport': rapport,
    }
    
    return render(request, 'project_management/sprint/sprint_rapport.html', context)


@login_required
def sprint_stats_api(request):
    """API pour les statistiques des sprints"""
    stats = {
        'total_sprints': JRSprint.objects.count(),
        'par_statut': list(
            JRSprint.objects.values('statut')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'sprints_actifs': JRSprint.objects.filter(statut='ACTIF').count(),
        'duree_moyenne': JRSprint.objects.aggregate(
            avg_duree=Count('id')
        )['avg_duree'] or 0,
        'par_projet': list(
            JRSprint.objects.values('projet__code', 'projet__nom')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        ),
    }
    
    return JsonResponse(stats)

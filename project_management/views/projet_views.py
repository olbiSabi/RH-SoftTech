from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg, F, FloatField, ExpressionWrapper
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils import timezone

from ..models import JRProject, JRClient, JRTicket, JRImputation
from ..forms import ProjetForm, ProjetSearchForm
from ..mixins import ProjectPermissionMixin, project_permission_required
from employee.models import ZY00


@method_decorator(login_required, name='dispatch')
class ProjetListView(LoginRequiredMixin, ListView):
    """Vue pour la liste des projets - Accessible à tous les utilisateurs connectés"""
    model = JRProject
    template_name = 'project_management/projet/projet_list.html'
    context_object_name = 'projets'
    paginate_by = 20

    def get_queryset(self):
        queryset = JRProject.objects.select_related('client', 'chef_projet')

        # Recherche
        search_form = ProjetSearchForm(self.request.GET)
        if search_form.is_valid():
            recherche = search_form.cleaned_data.get('recherche')
            client = search_form.cleaned_data.get('client')
            chef_projet = search_form.cleaned_data.get('chef_projet')
            statut = search_form.cleaned_data.get('statut')
            date_debut_min = search_form.cleaned_data.get('date_debut_min')
            date_debut_max = search_form.cleaned_data.get('date_debut_max')

            if recherche:
                queryset = queryset.filter(
                    Q(nom__icontains=recherche) |
                    Q(code__icontains=recherche) |
                    Q(description__icontains=recherche)
                )

            if client:
                queryset = queryset.filter(client=client)

            if chef_projet:
                queryset = queryset.filter(chef_projet=chef_projet)

            if statut:
                queryset = queryset.filter(statut=statut)

            if date_debut_min:
                queryset = queryset.filter(date_debut__gte=date_debut_min)

            if date_debut_max:
                queryset = queryset.filter(date_debut__lte=date_debut_max)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProjetSearchForm(self.request.GET)

        # Liste des clients pour le filtre
        context['clients'] = JRClient.objects.all().order_by('raison_sociale')

        # Statistiques
        context['total_projets'] = JRProject.objects.count()
        context['projets_planifies'] = JRProject.objects.filter(statut='PLANIFIE').count()
        context['projets_actifs'] = JRProject.objects.filter(statut='ACTIF').count()
        context['projets_termines'] = JRProject.objects.filter(statut='TERMINE').count()

        # Budget total
        context['budget_total'] = JRProject.objects.aggregate(
            total=Sum('montant_total')
        )['total'] or 0

        # Permission de gestion des projets
        context['peut_gerer_projets'] = (
            self.request.user.is_superuser or
            self.request.user.is_staff or
            (hasattr(self.request.user, 'employe') and
             self.request.user.employe and
             self.request.user.employe.peut_gerer_projets())
        )

        # Permission de gestion des clients
        context['peut_gerer_clients'] = (
            self.request.user.is_superuser or
            self.request.user.is_staff or
            (hasattr(self.request.user, 'employe') and
             self.request.user.employe and
             self.request.user.employe.peut_gerer_clients())
        )

        return context


@method_decorator(login_required, name='dispatch')
class ProjetCreateView(ProjectPermissionMixin, LoginRequiredMixin, CreateView):
    """Vue pour la création d'un projet"""
    model = JRProject
    form_class = ProjetForm
    template_name = 'project_management/projet/projet_form.html'
    success_url = reverse_lazy('pm:projet_list')

    def form_valid(self, form):
        messages.success(self.request, f'Projet {form.instance.nom} créé avec succès.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ProjetUpdateView(ProjectPermissionMixin, LoginRequiredMixin, UpdateView):
    """Vue pour la modification d'un projet"""
    model = JRProject
    form_class = ProjetForm
    template_name = 'project_management/projet/projet_form.html'
    success_url = reverse_lazy('pm:projet_list')

    def form_valid(self, form):
        messages.success(self.request, f'Projet {form.instance.nom} modifié avec succès.')
        return super().form_valid(form)


@login_required
def projet_detail(request, pk):
    """Vue pour le détail d'un projet - Accessible à tous les utilisateurs connectés"""
    projet = get_object_or_404(
        JRProject.objects.select_related('client', 'chef_projet'),
        pk=pk
    )

    # Tickets du projet
    tickets = JRTicket.objects.filter(projet=projet).select_related('assigne')

    # Statistiques des tickets
    stats_tickets = {
        'total': tickets.count(),
        'ouverts': tickets.filter(statut='OUVERT').count(),
        'en_cours': tickets.filter(statut='EN_COURS').count(),
        'en_revue': tickets.filter(statut='EN_REVUE').count(),
        'termines': tickets.filter(statut='TERMINE').count(),
    }

    # Imputations du projet
    imputations = JRImputation.objects.filter(
        ticket__projet=projet,
        statut_validation='VALIDE'
    ).select_related('employe', 'ticket')

    # Temps total par employé
    temps_par_employe = imputations.values('employe__nom', 'employe__prenoms').annotate(
        total_heures=ExpressionWrapper(
            Sum('heures') + Sum('minutes') / 60.0,
            output_field=FloatField()
        )
    ).order_by('-total_heures')

    # Calculer le total du projet
    temps_list = list(temps_par_employe)
    total_heures_projet = sum(item['total_heures'] or 0 for item in temps_list)

    # Permission de gestion
    peut_gerer_projets = (
        request.user.is_superuser or
        request.user.is_staff or
        (hasattr(request.user, 'employe') and
         request.user.employe and
         request.user.employe.peut_gerer_projets())
    )

    # Permission de gestion des clients
    peut_gerer_clients = (
        request.user.is_superuser or
        request.user.is_staff or
        (hasattr(request.user, 'employe') and
         request.user.employe and
         request.user.employe.peut_gerer_clients())
    )

    context = {
        'projet': projet,
        'tickets': tickets[:10],  # 10 derniers tickets
        'stats_tickets': stats_tickets,
        'temps_par_employe': temps_list,
        'total_heures_projet': total_heures_projet,
        'peut_gerer_projets': peut_gerer_projets,
        'peut_gerer_clients': peut_gerer_clients,
    }

    return render(request, 'project_management/projet/projet_detail.html', context)


@login_required
def projet_tickets(request, pk):
    """Vue pour les tickets d'un projet"""
    projet = get_object_or_404(JRProject, pk=pk)
    tickets = JRTicket.objects.filter(projet=projet).select_related('assigne')

    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'projet': projet,
        'page_obj': page_obj,
    }

    return render(request, 'project_management/projet/projet_tickets.html', context)


@login_required
def projet_imputations(request, pk):
    """Vue pour les imputations d'un projet"""
    projet = get_object_or_404(JRProject, pk=pk)
    imputations = JRImputation.objects.filter(
        ticket__projet=projet
    ).select_related('employe', 'ticket', 'valide_par').order_by('-date_imputation')

    # Pagination
    paginator = Paginator(imputations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'projet': projet,
        'page_obj': page_obj,
    }

    return render(request, 'project_management/projet/projet_imputations.html', context)


@login_required
@project_permission_required
@require_POST
def projet_delete(request, pk):
    """Vue pour supprimer un projet"""
    projet = get_object_or_404(JRProject, pk=pk)

    # Vérifier si le projet a des tickets
    if projet.tickets.exists():
        messages.error(request, 'Impossible de supprimer ce projet car il a des tickets associés.')
        return redirect('pm:projet_detail', pk=pk)

    projet.delete()
    messages.success(request, f'Projet {projet.nom} supprimé avec succès.')
    return redirect('pm:projet_list')


@login_required
def projet_stats_api(request):
    """API pour les statistiques des projets"""
    stats = {
        'total_projets': JRProject.objects.count(),
        'par_statut': list(
            JRProject.objects.values('statut')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'budget_total': JRProject.objects.aggregate(
            total=Sum('montant_total')
        )['total'] or 0,
        'projets_en_retard': JRProject.objects.filter(
            statut__in=['PLANIFIE', 'ACTIF'],
            date_fin_prevue__lt=timezone.now().date()
        ).count(),
        'par_client': list(
            JRProject.objects.values('client__raison_sociale')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        ),
    }

    return JsonResponse(stats)


@login_required
def search_employes_api(request):
    """API pour rechercher des employés (autocomplete)"""
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        employes = ZY00.objects.filter(
            Q(nom__icontains=query) |
            Q(prenoms__icontains=query) |
            Q(matricule__icontains=query)
        ).filter(etat='actif').order_by('nom', 'prenoms')[:15]

        results = [
            {
                'id': str(emp.pk),  # pk = matricule (clé primaire de ZY00)
                'text': f"{emp.nom} {emp.prenoms or ''} ({emp.matricule})",
                'nom': emp.nom,
                'prenoms': emp.prenoms or '',
                'matricule': emp.matricule,
            }
            for emp in employes
        ]

        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e), 'results': []}, status=500)

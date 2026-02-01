from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

from ..models import JRClient, JRProject
from ..forms import ClientForm, ClientSearchForm
from ..mixins import ClientPermissionMixin, client_permission_required


@method_decorator(login_required, name='dispatch')
class ClientListView(ClientPermissionMixin, LoginRequiredMixin, ListView):
    """Vue pour la liste des clients"""
    model = JRClient
    template_name = 'project_management/client/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        queryset = JRClient.objects.all()

        # Recherche
        search_form = ClientSearchForm(self.request.GET)
        if search_form.is_valid():
            recherche = search_form.cleaned_data.get('recherche')
            statut = search_form.cleaned_data.get('statut')
            pays = search_form.cleaned_data.get('pays')

            if recherche:
                queryset = queryset.filter(
                    Q(raison_sociale__icontains=recherche) |
                    Q(code_client__icontains=recherche) |
                    Q(contact_principal__icontains=recherche) |
                    Q(email_contact__icontains=recherche)
                )

            if statut:
                queryset = queryset.filter(statut=statut)

            if pays:
                queryset = queryset.filter(pays__icontains=pays)

        return queryset.order_by('raison_sociale')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ClientSearchForm(self.request.GET)

        # Statistiques
        context['total_clients'] = JRClient.objects.count()
        context['clients_actifs'] = JRClient.objects.filter(statut='ACTIF').count()
        context['total_projets'] = JRProject.objects.count()
        context['ca_total'] = JRProject.objects.aggregate(
            total=Sum('montant_total')
        )['total'] or 0

        return context


@method_decorator(login_required, name='dispatch')
class ClientCreateView(ClientPermissionMixin, LoginRequiredMixin, CreateView):
    """Vue pour la création d'un client"""
    model = JRClient
    form_class = ClientForm
    template_name = 'project_management/client/client_form.html'
    success_url = reverse_lazy('pm:client_list')

    def form_valid(self, form):
        messages.success(self.request, f'Client {form.instance.raison_sociale} créé avec succès.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ClientUpdateView(ClientPermissionMixin, LoginRequiredMixin, UpdateView):
    """Vue pour la modification d'un client"""
    model = JRClient
    form_class = ClientForm
    template_name = 'project_management/client/client_form.html'
    success_url = reverse_lazy('pm:client_list')

    def form_valid(self, form):
        messages.success(self.request, f'Client {form.instance.raison_sociale} modifié avec succès.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ClientDetailView(ClientPermissionMixin, LoginRequiredMixin, ListView):
    """Vue pour le détail d'un client avec ses projets"""
    model = JRProject
    template_name = 'project_management/client/client_detail.html'
    context_object_name = 'projets'
    paginate_by = 10

    def get_queryset(self):
        self.client = get_object_or_404(JRClient, pk=self.kwargs['pk'])
        return JRProject.objects.filter(client=self.client).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.client

        # Statistiques des projets
        projets = self.get_queryset()
        context['total_projets'] = projets.count()
        context['projets_actifs'] = projets.filter(statut='ACTIF').count()
        context['projets_termines'] = projets.filter(statut='TERMINE').count()

        # Chiffre d'affaires total
        context['ca_total'] = projets.aggregate(
            total=Sum('montant_total')
        )['total'] or 0

        return context


@login_required
@client_permission_required
def client_delete(request, pk):
    """Vue pour supprimer un client"""
    client = get_object_or_404(JRClient, pk=pk)

    # Vérifier si le client a des projets
    if client.projets.exists():
        messages.error(request, 'Impossible de supprimer ce client car il a des projets associés.')
        return redirect('pm:client_detail', pk=pk)

    raison_sociale = client.raison_sociale
    client.delete()
    messages.success(request, f'Client {raison_sociale} supprimé avec succès.')
    return redirect('pm:client_list')


@login_required
@client_permission_required
def client_stats_api(request):
    """API pour les statistiques des clients"""
    stats = {
        'total_clients': JRClient.objects.count(),
        'clients_actifs': JRClient.objects.filter(statut='ACTIF').count(),
        'clients_inactifs': JRClient.objects.filter(statut='INACTIF').count(),
        'clients_suspendus': JRClient.objects.filter(statut='SUSPENDU').count(),
        'par_pays': list(
            JRClient.objects.values('pays')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        ),
        'ca_total': sum(
            client.chiffre_affaires_total or 0
            for client in JRClient.objects.all()
        )
    }

    return JsonResponse(stats)

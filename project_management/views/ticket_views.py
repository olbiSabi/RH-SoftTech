from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.files.storage import default_storage

from ..models import JRTicket, JRProject, JRCommentaire, JRPieceJointe, JRHistorique
from ..forms import TicketForm, TicketSearchForm, CommentaireForm, PieceJointeForm
from ..services import TicketService
from employee.models import ZY00


@method_decorator(login_required, name='dispatch')
class TicketListView(LoginRequiredMixin, ListView):
    """Vue pour la liste des tickets"""
    model = JRTicket
    template_name = 'project_management/ticket/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = JRTicket.objects.select_related('projet', 'assigne', 'projet__client')
        
        # Recherche
        search_form = TicketSearchForm(self.request.GET)
        if search_form.is_valid():
            recherche = search_form.cleaned_data.get('recherche')
            projet = search_form.cleaned_data.get('projet')
            assigne = search_form.cleaned_data.get('assigne')
            statut = search_form.cleaned_data.get('statut')
            priorite = search_form.cleaned_data.get('priorite')
            type_ticket = search_form.cleaned_data.get('type_ticket')
            dans_backlog = search_form.cleaned_data.get('dans_backlog')
            date_creation_min = search_form.cleaned_data.get('date_creation_min')
            date_creation_max = search_form.cleaned_data.get('date_creation_max')
            
            if recherche:
                queryset = queryset.filter(
                    Q(titre__icontains=recherche) |
                    Q(code__icontains=recherche) |
                    Q(description__icontains=recherche)
                )
            
            if projet:
                queryset = queryset.filter(projet=projet)
            
            if assigne:
                queryset = queryset.filter(assigne=assigne)
            
            if statut:
                queryset = queryset.filter(statut=statut)
            
            if priorite:
                queryset = queryset.filter(priorite=priorite)
            
            if type_ticket:
                queryset = queryset.filter(type_ticket=type_ticket)
            
            if dans_backlog:
                queryset = queryset.filter(dans_backlog=True)
            
            if date_creation_min:
                queryset = queryset.filter(created_at__date__gte=date_creation_min)
            
            if date_creation_max:
                queryset = queryset.filter(created_at__date__lte=date_creation_max)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TicketSearchForm(self.request.GET)
        
        # Statistiques
        context['total_tickets'] = JRTicket.objects.count()
        context['tickets_ouverts'] = JRTicket.objects.filter(statut='OUVERT').count()
        context['tickets_en_cours'] = JRTicket.objects.filter(statut='EN_COURS').count()
        context['tickets_en_revue'] = JRTicket.objects.filter(statut='EN_REVUE').count()
        context['tickets_termines'] = JRTicket.objects.filter(statut='TERMINE').count()

        # Permission de gestion des projets
        context['peut_gerer_projets'] = (
            self.request.user.is_superuser or
            self.request.user.is_staff or
            (hasattr(self.request.user, 'employe') and
             self.request.user.employe and
             self.request.user.employe.peut_gerer_projets())
        )

        return context


@method_decorator(login_required, name='dispatch')
class TicketCreateView(LoginRequiredMixin, CreateView):
    """Vue pour la création d'un ticket"""
    model = JRTicket
    form_class = TicketForm
    template_name = 'project_management/ticket/ticket_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('pm:ticket_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)

        # Créer l'historique
        TicketService.creer_historique(
            ticket=self.object,
            utilisateur=self.request.user,
            type_changement='CREATION',
            description=f"Création du ticket {self.object.code}"
        )
        
        messages.success(self.request, f'Ticket {self.object.code} créé avec succès.')
        return response


@method_decorator(login_required, name='dispatch')
class TicketUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour la modification d'un ticket"""
    model = JRTicket
    form_class = TicketForm
    template_name = 'project_management/ticket/ticket_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('pm:ticket_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Sauvegarder les anciennes valeurs pour l'historique
        old_instance = get_object_or_404(JRTicket, pk=self.object.pk)

        response = super().form_valid(form)
        
        # Créer l'historique pour les changements
        TicketService.tracker_changements(
            old_instance=old_instance,
            new_instance=self.object,
            utilisateur=self.request.user
        )
        
        messages.success(self.request, f'Ticket {self.object.code} modifié avec succès.')
        return response


@login_required
def ticket_detail(request, pk):
    """Vue pour le détail d'un ticket"""
    ticket = get_object_or_404(
        JRTicket.objects.select_related(
            'projet', 'assigne', 'projet__client', 'projet__chef_projet'
        ),
        pk=pk
    )
    
    # Commentaires
    commentaires = ticket.commentaires.select_related('auteur').order_by('created_at')
    
    # Pièces jointes
    pieces_jointes = ticket.pieces_jointes.select_related('uploaded_by').order_by('-uploaded_at')
    
    # Historique
    historique = ticket.historique.select_related('utilisateur').order_by('-created_at')
    
    # Imputations
    imputations = ticket.imputations.select_related('employe', 'valide_par').order_by('-date_imputation')
    
    # Formulaires
    commentaire_form = CommentaireForm()
    piece_jointe_form = PieceJointeForm()

    # Permission de gestion des projets
    peut_gerer_projets = (
        request.user.is_superuser or
        request.user.is_staff or
        (hasattr(request.user, 'employe') and
         request.user.employe and
         request.user.employe.peut_gerer_projets())
    )

    context = {
        'ticket': ticket,
        'commentaires': commentaires,
        'pieces_jointes': pieces_jointes,
        'historique': historique,
        'imputations': imputations,
        'commentaire_form': commentaire_form,
        'piece_jointe_form': piece_jointe_form,
        'peut_gerer_projets': peut_gerer_projets,
    }

    return render(request, 'project_management/ticket/ticket_detail.html', context)


@login_required
@require_POST
def ticket_ajouter_commentaire(request, pk):
    """Vue pour ajouter un commentaire à un ticket"""
    ticket = get_object_or_404(JRTicket, pk=pk)
    form = CommentaireForm(request.POST)

    # Récupérer l'employé ZY00 lié à l'utilisateur connecté
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        messages.error(request, 'Vous devez être associé à un employé pour commenter.')
        return redirect('pm:ticket_detail', pk=pk)

    if form.is_valid():
        commentaire = JRCommentaire.objects.create(
            ticket=ticket,
            auteur=employe,
            contenu=form.cleaned_data['contenu']
        )

        # Ajouter les mentions
        if form.cleaned_data['mentions']:
            commentaire.mentions.set(form.cleaned_data['mentions'])

        # Créer l'historique
        TicketService.creer_historique(
            ticket=ticket,
            utilisateur=employe,
            type_changement='COMMENTAIRE',
            description="Ajout d'un commentaire"
        )

        messages.success(request, 'Commentaire ajouté avec succès.')
    else:
        messages.error(request, 'Erreur lors de l\'ajout du commentaire.')

    return redirect('pm:ticket_detail', pk=pk)


@login_required
@require_POST
def ticket_ajouter_piece_jointe(request, pk):
    """Vue pour ajouter une pièce jointe à un ticket"""
    ticket = get_object_or_404(JRTicket, pk=pk)
    form = PieceJointeForm(request.POST, request.FILES)

    # Récupérer l'employé ZY00 lié à l'utilisateur connecté
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        employe = None  # uploaded_by accepte null

    if form.is_valid() and request.FILES.get('fichier'):
        fichier = request.FILES['fichier']

        piece_jointe = JRPieceJointe.objects.create(
            ticket=ticket,
            fichier=fichier,
            nom_original=fichier.name,
            taille=fichier.size,
            type_mime=fichier.content_type,
            uploaded_by=employe
        )

        # Créer l'historique
        TicketService.creer_historique(
            ticket=ticket,
            utilisateur=employe,
            type_changement='PIECE_JOINTE',
            description=f"Ajout de la pièce jointe {fichier.name}"
        )

        messages.success(request, 'Pièce jointe ajoutée avec succès.')
    else:
        messages.error(request, 'Erreur lors de l\'ajout de la pièce jointe.')

    return redirect('pm:ticket_detail', pk=pk)


@login_required
@require_POST
def ticket_changer_statut(request, pk):
    """Vue pour changer le statut d'un ticket"""
    ticket = get_object_or_404(JRTicket, pk=pk)
    nouveau_statut = request.POST.get('statut')
    
    if nouveau_statut in dict(JRTicket.STATUT_CHOICES):
        ancien_statut = ticket.statut
        
        # Validation des transitions
        if not TicketService.valider_transition_statut(ancien_statut, nouveau_statut):
            messages.error(request, 'Transition de statut non autorisée.')
            return redirect('pm:ticket_detail', pk=pk)
        
        ticket.statut = nouveau_statut
        ticket.save()
        
        # Créer l'historique
        TicketService.creer_historique(
            ticket=ticket,
            utilisateur=request.user,
            type_changement='STATUT',
            champ_modifie='statut',
            ancienne_valeur=ancien_statut,
            nouvelle_valeur=nouveau_statut,
            description=f"Changement de statut : {ancien_statut} → {nouveau_statut}"
        )
        
        messages.success(request, f'Statut changé en {nouveau_statut} avec succès.')
    else:
        messages.error(request, 'Statut invalide.')

    return redirect('pm:ticket_detail', pk=pk)


@login_required
@require_POST
def ticket_assigner(request, pk):
    """Vue pour assigner un ticket"""
    ticket = get_object_or_404(JRTicket, pk=pk)
    assigne_id = request.POST.get('assigne')
    
    ancien_assigne = ticket.assigne
    nouveau_assigne = None
    
    if assigne_id:
        nouveau_assigne = get_object_or_404(ZY00, pk=assigne_id)
    
    ticket.assigne = nouveau_assigne
    ticket.save()
    
    # Créer l'historique
    TicketService.creer_historique(
        ticket=ticket,
        utilisateur=request.user,
        type_changement='ASSIGNATION',
        champ_modifie='assigne',
        ancienne_valeur=str(ancien_assigne) if ancien_assigne else 'Non assigné',
        nouvelle_valeur=str(nouveau_assigne) if nouveau_assigne else 'Non assigné',
        description=f"Réassignation du ticket"
    )
    
    messages.success(request, f'Ticket assigné à {nouveau_assigne} avec succès.' if nouveau_assigne else 'Ticket non assigné.')
    return redirect('pm:ticket_detail', pk=pk)


@login_required
def ticket_kanban(request):
    """Vue pour le tableau Kanban des tickets"""
    # Filtres
    projet_id = request.GET.get('projet')
    assigne_id = request.GET.get('assigne')

    tickets = JRTicket.objects.select_related('projet', 'assigne')
    projet = None

    if projet_id:
        try:
            projet = JRProject.objects.get(pk=projet_id)
            tickets = tickets.filter(projet_id=projet_id)
        except JRProject.DoesNotExist:
            pass

    if assigne_id:
        tickets = tickets.filter(assigne_id=assigne_id)

    # Organiser par statut
    tickets_par_statut = {
        'OUVERT': tickets.filter(statut='OUVERT'),
        'EN_COURS': tickets.filter(statut='EN_COURS'),
        'EN_REVUE': tickets.filter(statut='EN_REVUE'),
        'TERMINE': tickets.filter(statut='TERMINE'),
    }

    context = {
        'tickets_par_statut': tickets_par_statut,
        'projet': projet,
        'projets': JRProject.objects.filter(statut__in=['PLANIFIE', 'ACTIF']),
        'employes': ZY00.objects.filter(etat='actif'),
    }

    return render(request, 'project_management/ticket/ticket_kanban.html', context)


@login_required
def ticket_stats_api(request):
    """API pour les statistiques des tickets"""
    stats = {
        'total_tickets': JRTicket.objects.count(),
        'par_statut': list(
            JRTicket.objects.values('statut')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'par_priorite': list(
            JRTicket.objects.values('priorite')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'par_type': list(
            JRTicket.objects.values('type_ticket')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'tickets_non_assignes': JRTicket.objects.filter(assigne__isnull=True).count(),
        'tickets_en_retard': JRTicket.objects.filter(
            date_echeance__lt=timezone.now().date(),
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
        ).count(),
    }

    return JsonResponse(stats)


@login_required
@require_POST
def ticket_delete(request, pk):
    """Vue pour supprimer un ticket"""
    ticket = get_object_or_404(JRTicket, pk=pk)
    code = ticket.code
    titre = ticket.titre

    # Supprimer le ticket (les commentaires, pièces jointes et historique seront supprimés en cascade)
    ticket.delete()

    messages.success(request, f'Ticket {code} "{titre}" supprimé avec succès.')
    return redirect('pm:ticket_list')

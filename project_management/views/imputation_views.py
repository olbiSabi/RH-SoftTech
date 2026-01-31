from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, FloatField, ExpressionWrapper, F, Value
from django.db.models.functions import Cast, Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction

from ..models import JRImputation, JRTicket, JRProject
from ..forms import ImputationForm, ImputationSearchForm, ValidationImputationForm
from ..services import ImputationService
from employee.models import ZY00


@method_decorator(login_required, name='dispatch')
class ImputationListView(LoginRequiredMixin, ListView):
    """Vue pour la liste des imputations"""
    model = JRImputation
    template_name = 'project_management/imputation/imputation_list.html'
    context_object_name = 'imputations'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = JRImputation.objects.select_related(
            'employe', 'ticket', 'ticket__projet', 'valide_par'
        )
        
        # Recherche
        search_form = ImputationSearchForm(self.request.GET)
        if search_form.is_valid():
            recherche = search_form.cleaned_data.get('recherche')
            employe = search_form.cleaned_data.get('employe')
            projet = search_form.cleaned_data.get('projet')
            statut_validation = search_form.cleaned_data.get('statut_validation')
            type_activite = search_form.cleaned_data.get('type_activite')
            date_min = search_form.cleaned_data.get('date_min')
            date_max = search_form.cleaned_data.get('date_max')
            
            if recherche:
                queryset = queryset.filter(
                    Q(ticket__titre__icontains=recherche) |
                    Q(ticket__code__icontains=recherche) |
                    Q(description__icontains=recherche)
                )
            
            if employe:
                queryset = queryset.filter(employe=employe)
            
            if projet:
                queryset = queryset.filter(
                    Q(ticket__projet__code__icontains=projet) |
                    Q(ticket__projet__nom__icontains=projet)
                )
            
            if statut_validation:
                queryset = queryset.filter(statut_validation=statut_validation)
            
            if type_activite:
                queryset = queryset.filter(type_activite=type_activite)
            
            if date_min:
                queryset = queryset.filter(date_imputation__gte=date_min)
            
            if date_max:
                queryset = queryset.filter(date_imputation__lte=date_max)
        
        return queryset.order_by('-date_imputation', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ImputationSearchForm(self.request.GET)

        # Données pour les filtres
        context['employes'] = ZY00.objects.filter(etat='Actif').order_by('nom', 'prenoms')
        context['projets'] = JRProject.objects.all().order_by('nom')

        # Statistiques
        context['total_imputations'] = JRImputation.objects.count()
        context['imputations_en_attente'] = JRImputation.objects.filter(
            statut_validation='EN_ATTENTE'
        ).count()
        context['imputations_validees'] = JRImputation.objects.filter(
            statut_validation='VALIDE'
        ).count()
        context['imputations_rejetees'] = JRImputation.objects.filter(
            statut_validation='REJETE'
        ).count()

        # Fonction pour calculer les heures (même logique que dans le modèle)
        def calculer_heures(queryset):
            total = 0
            for imp in queryset:
                total_minutes = int(float(imp.heures) * 60) + (imp.minutes or 0)
                total += total_minutes / 60.0
            return total

        # Total heures par statut
        all_imputations = JRImputation.objects.all()
        imputations_validees_qs = all_imputations.filter(statut_validation='VALIDE')
        imputations_en_attente_qs = all_imputations.filter(statut_validation='EN_ATTENTE')

        context['total_heures'] = calculer_heures(all_imputations)
        context['heures_validees'] = calculer_heures(imputations_validees_qs)
        context['heures_en_attente'] = calculer_heures(imputations_en_attente_qs)

        return context


@method_decorator(login_required, name='dispatch')
class ImputationCreateView(LoginRequiredMixin, CreateView):
    """Vue pour la création d'une imputation"""
    model = JRImputation
    form_class = ImputationForm
    template_name = 'project_management/imputation/imputation_form.html'
    success_url = reverse_lazy('pm:imputation_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Imputation de {self.object.total_heures}h créée avec succès.'
        )
        return response


@method_decorator(login_required, name='dispatch')
class ImputationUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour la modification d'une imputation"""
    model = JRImputation
    form_class = ImputationForm
    template_name = 'project_management/imputation/imputation_form.html'

    def get_success_url(self):
        return reverse_lazy('pm:mes_imputations')

    def get_queryset(self):
        # L'utilisateur ne peut modifier que ses propres imputations en attente
        try:
            employe = ZY00.objects.get(user=self.request.user)
            return JRImputation.objects.filter(
                employe=employe,
                statut_validation='EN_ATTENTE'
            )
        except ZY00.DoesNotExist:
            return JRImputation.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Imputation modifiée avec succès.'
        )
        return response


@method_decorator(login_required, name='dispatch')
class ImputationDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour la suppression d'une imputation"""
    model = JRImputation
    template_name = 'project_management/imputation/imputation_confirm_delete.html'
    success_url = reverse_lazy('pm:mes_imputations')

    def get_queryset(self):
        # L'utilisateur ne peut supprimer que ses propres imputations en attente
        try:
            employe = ZY00.objects.get(user=self.request.user)
            return JRImputation.objects.filter(
                employe=employe,
                statut_validation='EN_ATTENTE'
            )
        except ZY00.DoesNotExist:
            return JRImputation.objects.none()

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Imputation supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


@login_required
def mes_imputations(request):
    """Vue pour les imputations de l'utilisateur connecté"""
    # Récupérer l'employé associé à l'utilisateur connecté
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        messages.error(request, "Aucun employé associé à votre compte utilisateur.")
        return redirect('pm:dashboard')

    imputations = JRImputation.objects.filter(
        employe=employe
    ).select_related('ticket', 'ticket__projet').order_by('-date_imputation')

    # Pagination
    paginator = Paginator(imputations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fonction pour calculer les heures (même logique que dans le modèle)
    def calculer_heures(queryset):
        total = 0
        for imp in queryset:
            total_minutes = int(float(imp.heures) * 60) + (imp.minutes or 0)
            total += total_minutes / 60.0
        return total

    # Statistiques personnelles
    imputations_validees = imputations.filter(statut_validation='VALIDE')
    stats = {
        'total': imputations.count(),
        'en_attente': imputations.filter(statut_validation='EN_ATTENTE').count(),
        'validees': imputations_validees.count(),
        'rejetees': imputations.filter(statut_validation='REJETE').count(),
        'total_heures': calculer_heures(imputations_validees),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
    }

    return render(request, 'project_management/imputation/mes_imputations.html', context)


@login_required
def validation_imputations(request):
    """Vue pour la validation des imputations (pour les chefs de projet et administrateurs)"""
    # Récupérer l'employé associé à l'utilisateur connecté
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        messages.error(request, "Aucun employé associé à votre compte utilisateur.")
        return redirect('pm:dashboard')

    # Vérifier si l'utilisateur a des droits étendus (DRH, GESTION_APP, DIRECTEUR)
    is_admin = (
        employe.has_role('DRH') or
        employe.has_role('GESTION_APP') or
        employe.has_role('DIRECTEUR')
    )

    # Récupérer les imputations en attente
    if is_admin:
        # Les administrateurs voient toutes les imputations en attente
        imputations = JRImputation.objects.filter(
            statut_validation='EN_ATTENTE'
        )
    else:
        # Les chefs de projet ne voient que les imputations de leurs projets
        projets_utilisateur = JRProject.objects.filter(chef_projet=employe)
        imputations = JRImputation.objects.filter(
            statut_validation='EN_ATTENTE',
            ticket__projet__in=projets_utilisateur
        )

    imputations = imputations.select_related(
        'employe', 'ticket', 'ticket__projet'
    ).order_by('-date_imputation')

    # Filtres
    projet_filter = request.GET.get('projet')
    employe_filter = request.GET.get('employe')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if projet_filter:
        imputations = imputations.filter(ticket__projet__pk=projet_filter)
    if employe_filter:
        imputations = imputations.filter(employe__pk=employe_filter)
    if date_debut:
        imputations = imputations.filter(date_imputation__gte=date_debut)
    if date_fin:
        imputations = imputations.filter(date_imputation__lte=date_fin)

    # Pagination
    paginator = Paginator(imputations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer les projets et employés pour les filtres
    if is_admin:
        projets = JRProject.objects.filter(statut='ACTIF').order_by('code')
        employes = ZY00.objects.filter(etat='Actif').order_by('nom', 'prenoms')
    else:
        projets = JRProject.objects.filter(chef_projet=employe, statut='ACTIF').order_by('code')
        employes = ZY00.objects.filter(
            pm_imputations__ticket__projet__in=projets
        ).distinct().order_by('nom', 'prenoms')

    context = {
        'page_obj': page_obj,
        'total_en_attente': imputations.count(),
        'is_admin': is_admin,
        'projets': projets,
        'employes': employes,
    }

    return render(request, 'project_management/imputation/validation_list.html', context)


@login_required
@require_POST
def valider_imputation(request, pk):
    """Vue pour valider une imputation"""
    imputation = get_object_or_404(JRImputation, pk=pk)

    # Récupérer l'employé correspondant à l'utilisateur
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        messages.error(request, "Aucun employé associé à votre compte utilisateur.")
        return redirect('pm:validation_imputations')

    # Vérifier que l'utilisateur est autorisé à valider
    if not ImputationService.peut_valider_imputation(request.user, imputation):
        messages.error(request, 'Vous n\'êtes pas autorisé à valider cette imputation.')
        return redirect('pm:validation_imputations')

    form = ValidationImputationForm(request.POST)

    if form.is_valid():
        action = form.cleaned_data['action']
        commentaire = form.cleaned_data['commentaire_validation']

        if action == 'valider':
            imputation.valider(employe, commentaire)
            messages.success(
                request,
                f'Imputation de {imputation.employe} validée avec succès.'
            )
        elif action == 'rejeter':
            imputation.rejeter(employe, commentaire)
            messages.warning(
                request,
                f'Imputation de {imputation.employe} rejetée.'
            )
    else:
        messages.error(request, 'Erreur lors de la validation.')

    return redirect('pm:validation_imputations')


@login_required
@require_POST
def valider_multiple_imputations(request):
    """Vue pour valider plusieurs imputations en masse"""
    # Récupérer l'employé correspondant à l'utilisateur
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        messages.error(request, "Aucun employé associé à votre compte utilisateur.")
        return redirect('pm:validation_imputations')

    imputation_ids = request.POST.getlist('imputation_ids')
    action = request.POST.get('action')
    commentaire = request.POST.get('commentaire_validation', '')

    if not imputation_ids:
        messages.error(request, 'Aucune imputation sélectionnée.')
        return redirect('pm:validation_imputations')

    imputations = JRImputation.objects.filter(
        pk__in=imputation_ids,
        statut_validation='EN_ATTENTE'
    )

    # Vérifier les permissions pour chaque imputation
    validees = 0
    rejetees = 0
    erreurs = 0

    with transaction.atomic():
        for imputation in imputations:
            if ImputationService.peut_valider_imputation(request.user, imputation):
                if action == 'valider':
                    imputation.valider(employe, commentaire)
                    validees += 1
                elif action == 'rejeter':
                    imputation.rejeter(employe, commentaire)
                    rejetees += 1
            else:
                erreurs += 1

    if validees > 0:
        messages.success(request, f'{validees} imputation(s) validée(s) avec succès.')
    if rejetees > 0:
        messages.warning(request, f'{rejetees} imputation(s) rejetée(s).')
    if erreurs > 0:
        messages.error(request, f'{erreurs} imputation(s) n\'ont pas pu être traitées (permission refusée).')

    return redirect('pm:validation_imputations')


@login_required
def rapports_temps(request):
    """Vue pour les rapports de temps"""
    # Filtres
    projet_id = request.GET.get('projet')
    employe_id = request.GET.get('employe')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    statut_filter = request.GET.get('statut', '')

    # Par défaut, afficher toutes les imputations traitées (validées et rejetées)
    imputations = JRImputation.objects.exclude(statut_validation='EN_ATTENTE')

    # Filtre par statut si spécifié
    if statut_filter:
        imputations = imputations.filter(statut_validation=statut_filter)

    if projet_id:
        imputations = imputations.filter(ticket__projet_id=projet_id)

    if employe_id:
        imputations = imputations.filter(employe_id=employe_id)

    if date_debut:
        imputations = imputations.filter(date_imputation__gte=date_debut)

    if date_fin:
        imputations = imputations.filter(date_imputation__lte=date_fin)
    
    # Statistiques - Calcul des heures totales
    # On calcule en Python pour avoir le même résultat que heures_affichage/minutes_affichage
    # car les données peuvent avoir heures décimales + minutes (double comptage historique)

    def calculer_stats_heures(queryset):
        """Calcule le total d'heures en utilisant la même logique que heures_affichage"""
        total = 0
        for imp in queryset:
            # Même calcul que dans le modèle
            total_minutes = int(float(imp.heures) * 60) + (imp.minutes or 0)
            total += total_minutes / 60.0
        return total

    stats = {
        'total_heures': calculer_stats_heures(imputations),
        'total_imputations': imputations.count(),
        'par_type_activite': [],
        'par_employe': [],
        'par_projet': [],
    }

    # Calcul par type d'activité
    types_activite = imputations.values('type_activite').distinct()
    for ta in types_activite:
        type_val = ta['type_activite']
        qs = imputations.filter(type_activite=type_val)
        stats['par_type_activite'].append({
            'type_activite': type_val,
            'total_heures': calculer_stats_heures(qs),
            'count': qs.count()
        })
    stats['par_type_activite'].sort(key=lambda x: x['total_heures'], reverse=True)

    # Calcul par employé
    employes = imputations.values('employe__nom', 'employe__prenoms').distinct()
    for emp in employes:
        qs = imputations.filter(employe__nom=emp['employe__nom'], employe__prenoms=emp['employe__prenoms'])
        stats['par_employe'].append({
            'employe__nom': emp['employe__nom'],
            'employe__prenoms': emp['employe__prenoms'],
            'total_heures': calculer_stats_heures(qs),
            'count': qs.count()
        })
    stats['par_employe'].sort(key=lambda x: x['total_heures'], reverse=True)

    # Calcul par projet
    projets = imputations.values('ticket__projet__code', 'ticket__projet__nom').distinct()
    for proj in projets:
        qs = imputations.filter(ticket__projet__code=proj['ticket__projet__code'])
        stats['par_projet'].append({
            'ticket__projet__code': proj['ticket__projet__code'],
            'ticket__projet__nom': proj['ticket__projet__nom'],
            'total_heures': calculer_stats_heures(qs),
            'count': qs.count()
        })
    stats['par_projet'].sort(key=lambda x: x['total_heures'], reverse=True)
    
    # Détail des imputations
    imputations_detail = imputations.select_related(
        'employe', 'ticket', 'ticket__projet'
    ).order_by('-date_imputation')
    
    # Pagination pour le détail
    paginator = Paginator(imputations_detail, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques par statut (toutes imputations traitées, sans filtre statut)
    all_imputations = JRImputation.objects.exclude(statut_validation='EN_ATTENTE')
    imputations_validees = all_imputations.filter(statut_validation='VALIDE')
    stats_par_statut = {
        'validees': imputations_validees.count(),
        'rejetees': all_imputations.filter(statut_validation='REJETE').count(),
        'heures_validees': calculer_stats_heures(imputations_validees),
    }

    context = {
        'stats': stats,
        'stats_par_statut': stats_par_statut,
        'page_obj': page_obj,
        'projets': JRProject.objects.all(),
        'employes': ZY00.objects.filter(etat='Actif').order_by('nom', 'prenoms'),
        'statut_choices': [
            ('', 'Tous les statuts'),
            ('VALIDE', 'Validées'),
            ('REJETE', 'Rejetées'),
        ],
    }

    return render(request, 'project_management/imputation/rapports_temps.html', context)


@login_required
def export_temps_excel(request):
    """Vue pour exporter les temps en Excel"""
    import pandas as pd
    from io import BytesIO
    from django.http import HttpResponse
    
    # Récupérer les données (même logique que rapports_temps)
    imputations = JRImputation.objects.filter(statut_validation='VALIDE').select_related(
        'employe', 'ticket', 'ticket__projet'
    ).order_by('-date_imputation')
    
    # Créer le DataFrame
    data = []
    for imp in imputations:
        # Convertir date_validation en datetime sans timezone pour Excel
        date_validation = None
        if imp.date_validation:
            date_validation = imp.date_validation.replace(tzinfo=None)

        data.append({
            'Date': imp.date_imputation,
            'Employé': f"{imp.employe.nom} {imp.employe.prenoms}",
            'Projet': imp.ticket.projet.code,
            'Ticket': imp.ticket.code,
            'Type activité': imp.get_type_activite_display(),
            'Heures': imp.total_heures,
            'Description': imp.description,
            'Validé par': f"{imp.valide_par.nom} {imp.valide_par.prenoms}" if imp.valide_par else '',
            'Date validation': date_validation,
        })
    
    df = pd.DataFrame(data)
    
    # Créer le fichier Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Imputations', index=False)
        
        # Ajuster la largeur des colonnes
        worksheet = writer.sheets['Imputations']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.set_column(idx, idx, max_len + 2)
    
    output.seek(0)
    
    # Créer la réponse HTTP
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=imputations_{timezone.now().date()}.xlsx'
    
    return response


@login_required
def imputation_stats_api(request):
    """API pour les statistiques des imputations"""
    stats = {
        'total_imputations': JRImputation.objects.count(),
        'par_statut': list(
            JRImputation.objects.values('statut_validation')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'total_heures_validees': JRImputation.objects.filter(
            statut_validation='VALIDE'
        ).aggregate(
            total=ExpressionWrapper(
                Coalesce(Sum('heures'), Value(0)) + Coalesce(Sum('minutes'), Value(0)) / 60.0,
                output_field=FloatField()
            )
        )['total'] or 0,
        'imputations_en_attente': JRImputation.objects.filter(
            statut_validation='EN_ATTENTE'
        ).count(),
        'par_type_activite': list(
            JRImputation.objects.values('type_activite')
            .annotate(
                total_heures=ExpressionWrapper(
                    Coalesce(Sum('heures'), Value(0)) + Coalesce(Sum('minutes'), Value(0)) / 60.0,
                    output_field=FloatField()
                ),
                count=Count('id')
            )
            .order_by('-total_heures')
        ),
    }

    return JsonResponse(stats)

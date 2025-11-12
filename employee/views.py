from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import ZYDO
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import os
from .utils import get_redirect_url_with_tab, get_active_tab_for_ajax
from departement.models import ZDPO
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD
from .forms import (
    ZY00Form, EmbaucheAgentForm, ZYCOForm, ZYTEForm,
    ZYMEForm, ZYAFForm, ZYADForm
)


# ===============================
# VUES POUR L'EMBAUCHE
# ===============================
def validate_date_overlap(queryset, date_debut, date_fin, exclude_pk=None):
    """
    Fonction utilitaire pour valider les chevauchements de dates
    """
    overlap_query = Q()

    if date_fin:
        # Cas avec date de fin
        overlap_query = (
                Q(date_debut__lte=date_debut, date_fin__gte=date_debut) |
                Q(date_debut__lte=date_fin, date_fin__gte=date_fin) |
                Q(date_debut__gte=date_debut, date_fin__lte=date_fin) |
                Q(date_debut__lte=date_fin, date_fin__isnull=True)
        )
    else:
        # Cas sans date de fin (actif)
        overlap_query = (
                Q(date_fin__gte=date_debut) | Q(date_fin__isnull=True)
        )

    queryset = queryset.filter(overlap_query)

    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)

    overlapping = queryset.first()
    return (overlapping is not None, overlapping)



def embauche_agent(request):
    """Vue pour l'embauche d'un nouvel agent (pré-embauche)"""
    if request.method == 'POST':
        form = EmbaucheAgentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Créer l'employé
                    employe = form.save(commit=False)
                    employe.type_dossier = 'PRE'  # Pré-embauche par défaut
                    employe.save()

                    # Date du jour pour les dates de début
                    date_jour = timezone.now().date()

                    # Créer le contrat
                    contrat = ZYCO.objects.create(
                        employe=employe,
                        type_contrat=form.cleaned_data['type_contrat'],
                        date_debut=form.cleaned_data['date_debut_contrat'],
                        date_fin=form.cleaned_data.get('date_fin_contrat')
                    )

                    # Créer le téléphone
                    telephone = ZYTE.objects.create(
                        employe=employe,
                        numero=form.cleaned_data['numero_telephone'],
                        date_debut_validite=date_jour
                    )

                    # Créer l'email
                    email = ZYME.objects.create(
                        employe=employe,
                        email=form.cleaned_data['email'],
                        date_debut_validite=date_jour
                    )

                    # Créer l'affectation
                    affectation = ZYAF.objects.create(
                        employe=employe,
                        poste=form.cleaned_data['poste'],
                        date_debut=date_jour
                    )

                    # Créer l'adresse principale
                    adresse = ZYAD.objects.create(
                        employe=employe,
                        rue=form.cleaned_data['rue'],
                        ville=form.cleaned_data['ville'],
                        pays=form.cleaned_data['pays'],
                        code_postal=form.cleaned_data['code_postal'],
                        type_adresse='PRINCIPALE',
                        date_debut=form.cleaned_data['date_debut_adresse']
                    )

                    messages.success(
                        request,
                        f"✅ Pré-embauche réussie ! L'agent {employe.nom} {employe.prenoms} "
                        f"a été enregistré avec le matricule {employe.matricule}. "
                        f"Vous pouvez maintenant valider son embauche."
                    )
                    # IMPORTANT: Utiliser redirect pour éviter la résoumission
                    return redirect('liste_employes')

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erreur lors de la création de la pré-embauche : {str(e)}"
                )
                # Redirection après erreur pour éviter la résoumission
                return redirect('embauche_agent')
        else:
            # Si le formulaire n'est pas valide, on affiche les erreurs
            # mais on ajoute un message général
            messages.error(
                request,
                "❌ Le formulaire contient des erreurs. Veuillez corriger les champs indiqués ci-dessous."
            )
            # On réaffiche le formulaire avec les erreurs - pas de redirect
    else:
        form = EmbaucheAgentForm()

    return render(request, 'employee/embauche-agent.html', {'form': form})


def valider_embauche(request, uuid):
    """Valider une pré-embauche et passer le type de dossier à SAL"""
    employe = get_object_or_404(ZY00, uuid=uuid)

    if employe.type_dossier == 'PRE':
        employe.type_dossier = 'SAL'
        employe.date_validation_embauche = timezone.now().date()
        employe.save()
        messages.success(request, f"Embauche de {employe.nom} {employe.prenoms} validée avec succès!")
    else:
        messages.warning(request, "Cet employé est déjà validé.")

    # ✅ MODIFICATION : Conservation de l'onglet actif
    base_url = reverse('dossier_detail', kwargs={'uuid': uuid})
    redirect_url = get_redirect_url_with_tab(request, base_url)
    return redirect(redirect_url)


# ===============================
# VUES POUR LES EMPLOYÉS (ZY00)
# ===============================

class EmployeListView(ListView):
    """Liste de tous les employés"""
    model = ZY00
    template_name = 'employee/employees-list.html'
    context_object_name = 'employes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrer par type de dossier
        type_dossier = self.request.GET.get('type_dossier')
        if type_dossier:
            queryset = queryset.filter(type_dossier=type_dossier)

        # Recherche par nom ou matricule
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenoms__icontains=search) |
                Q(matricule__icontains=search)
            )

        return queryset.order_by('-matricule')


class EmployeCreateView(CreateView):
    """Créer un employé"""
    model = ZY00
    form_class = ZY00Form
    template_name = 'employes/employe_form.html'
    success_url = reverse_lazy('liste_employes')

    def form_valid(self, form):
        messages.success(self.request, "Employé créé avec succès!")
        return super().form_valid(form)


class EmployeUpdateView(UpdateView):
    """Modifier un employé"""
    model = ZY00
    form_class = ZY00Form
    template_name = 'employee/employe_form.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    context_object_name = 'employe'

    def get_object(self, queryset=None):
        """Surcharge pour mieux gérer les erreurs"""
        try:
            return super().get_object(queryset)
        except ZY00.DoesNotExist:
            messages.error(self.request, "❌ Employé non trouvé")
            raise Http404("Employé non trouvé")

    def get_success_url(self):
        messages.success(self.request, "✅ Employé modifié avec succès!")
        # ✅ MODIFICATION : Conservation de l'onglet actif
        base_url = reverse('dossier_detail', kwargs={'uuid': self.object.uuid})
        return get_redirect_url_with_tab(self.request, base_url)

class EmployeDeleteView(DeleteView):
    """Supprimer un employé (suppression en cascade)"""
    model = ZY00
    template_name = 'employee/employe_confirm_delete.html'
    success_url = reverse_lazy('liste_dossiers')
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        """Surcharge pour mieux gérer la récupération par UUID"""
        if queryset is None:
            queryset = self.get_queryset()

        uuid = self.kwargs.get('uuid')
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        obj = get_object_or_404(queryset)
        return obj

    def delete(self, request, *args, **kwargs):
        employe = self.get_object()
        messages.success(request, f"Employé {employe.nom} {employe.prenom} supprimé avec succès!")
        return super().delete(request, *args, **kwargs)

    # Optionnel : pour personnaliser le contexte
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employe'] = self.get_object()
        return context

def detail_employe(request, uuid):
    """Détails d'un employé avec toutes ses informations"""
    employe = get_object_or_404(ZY00, uuid=uuid)

    context = {
        'employe': employe,
        'contrats': employe.contrats.all(),
        'telephones': employe.telephones.all(),
        'emails': employe.emails.all(),
        'affectations': employe.affectations.all(),
        'adresses': employe.adresses.all(),
        'documents': employe.documents.all(),
    }

    return render(request, 'employee/detail_employe.html', context)



class DossierIndividuelView(ListView):
    """Affiche la liste des employés + détail d'un employé sélectionné"""
    model = ZY00
    template_name = 'employee/dossier-individuel.html'
    context_object_name = 'employes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-matricule')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ajouter un deuxième jeu de données avec un nom personnalisé
        context['employes_actifs'] = ZY00.objects.filter(
            type_dossier='SAL'
        ).order_by('matricule')

        # Vérifier si un UUID est passé dans l'URL
        uuid = self.kwargs.get('uuid')
        if uuid:
            employe_selectionne = get_object_or_404(ZY00, uuid=uuid)

            # Données de l'employé
            context['employe'] = employe_selectionne

            # Entités liées (optimisées avec select_related)
            context['contrats'] = employe_selectionne.contrats.all().order_by('-date_debut')
            context['affectations'] = employe_selectionne.affectations.select_related(
                'poste__DEPARTEMENT'
            ).order_by('-date_debut')
            context['telephones'] = employe_selectionne.telephones.all().order_by('-date_debut_validite')
            context['emails'] = employe_selectionne.emails.all().order_by('-date_debut_validite')
            context['adresses'] = employe_selectionne.adresses.all().order_by('-date_debut')
            context['documents'] = employe_selectionne.documents.all().order_by('-date_ajout')

            # Postes disponibles pour le modal d'affectation ← AJOUTÉ
            context['postes'] = ZDPO.objects.filter(
                STATUT=True
            ).select_related('DEPARTEMENT').order_by('DEPARTEMENT__LIBELLE', 'CODE')

        return context

    def get(self, request, *args, **kwargs):
        # Cette méthode permet de gérer les deux cas :
        # - Accès à la liste seule
        # - Accès à la liste + détail d'un employé
        return super().get(request, *args, **kwargs)


# ========================================
# CONTRATS (ZYCO)
# ========================================

@require_POST
def contrat_create_ajax(request):
    """Créer un contrat via AJAX"""
    try:
        employe_matricule = request.POST.get('employe_matricule')
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([employe_matricule, type_contrat, date_debut]):
            return JsonResponse({
                'success': False,
                'error': 'Tous les champs obligatoires doivent être remplis'
            })

        # ✅ NOUVEAU CODE
        employe_identifier = request.POST.get('employe_matricule')  # Peut être UUID ou matricule

        # Essayer de trouver par UUID d'abord, puis par matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Vérifier date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({
                'success': False,
                'error': '❌ La date de fin doit être supérieure à la date de début'
            })

        # Vérifier un seul contrat actif
        contrats_actifs = ZYCO.objects.filter(employe=employe, date_fin__isnull=True)
        if contrats_actifs.exists():
            contrat = contrats_actifs.first()
            return JsonResponse({
                'success': False,
                'error': f'❌ Un contrat actif existe depuis le {contrat.date_debut.strftime("%d/%m/%Y")}'
            })

        # Vérifier chevauchement
        base_queryset = ZYCO.objects.filter(employe=employe)
        has_overlap, overlapping = validate_date_overlap(base_queryset, date_debut_obj, date_fin_obj)

        if has_overlap:
            date_fin_str = overlapping.date_fin.strftime("%d/%m/%Y") if overlapping.date_fin else "En cours"
            return JsonResponse({
                'success': False,
                'error': f'❌ Chevauchement avec contrat du {overlapping.date_debut.strftime("%d/%m/%Y")} au {date_fin_str}'
            })

        contrat = ZYCO.objects.create(
            employe=employe,
            type_contrat=type_contrat,
            date_debut=date_debut_obj,
            date_fin=date_fin_obj
        )

        return JsonResponse({'success': True, 'message': '✅ Contrat créé', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def contrat_update_ajax(request, pk):
    """Modifier un contrat via AJAX"""
    try:
        contrat = get_object_or_404(ZYCO, pk=pk)
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([type_contrat, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        # Vérifier contrat actif
        if not date_fin_obj:
            contrats_actifs = ZYCO.objects.filter(
                employe=contrat.employe,
                date_fin__isnull=True
            ).exclude(pk=pk)
            if contrats_actifs.exists():
                return JsonResponse({'success': False, 'error': '❌ Un autre contrat actif existe'})

        # Vérifier chevauchement
        base_queryset = ZYCO.objects.filter(employe=contrat.employe)
        has_overlap, overlapping = validate_date_overlap(base_queryset, date_debut_obj, date_fin_obj, pk)

        if has_overlap:
            return JsonResponse({'success': False, 'error': '❌ Chevauchement détecté'})

        contrat.type_contrat = type_contrat
        contrat.date_debut = date_debut_obj
        contrat.date_fin = date_fin_obj
        contrat.save()

        return JsonResponse({'success': True, 'message': '✅ Contrat modifié', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def contrat_delete_ajax(request, pk):
    """Supprimer un contrat via AJAX"""
    try:
        contrat = get_object_or_404(ZYCO, pk=pk)
        contrat.delete()
        return JsonResponse({'success': True, 'message': '✅ Contrat supprimé', **get_active_tab_for_ajax(request)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========================================
# AFFECTATIONS (ZYAF)
# ========================================

@require_POST
def affectation_create_ajax(request):
    """Créer une affectation via AJAX"""
    try:
        employe_matricule = request.POST.get('employe_matricule')
        poste_id = request.POST.get('poste_id')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([employe_matricule, poste_id, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        # ✅ NOUVEAU CODE
        employe_identifier = request.POST.get('employe_matricule')  # Peut être UUID ou matricule

        # Essayer de trouver par UUID d'abord, puis par matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        poste = get_object_or_404(ZDPO, pk=poste_id)
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        # Vérifier une seule affectation active
        affectations_actives = ZYAF.objects.filter(employe=employe, date_fin__isnull=True)
        if affectations_actives.exists():
            aff = affectations_actives.first()
            return JsonResponse({
                'success': False,
                'error': f'❌ Une affectation active existe depuis le {aff.date_debut.strftime("%d/%m/%Y")}'
            })

        # Vérifier chevauchement
        base_queryset = ZYAF.objects.filter(employe=employe)
        has_overlap, overlapping = validate_date_overlap(base_queryset, date_debut_obj, date_fin_obj)

        if has_overlap:
            return JsonResponse({'success': False, 'error': '❌ Chevauchement détecté'})

        ZYAF.objects.create(
            employe=employe,
            poste=poste,
            date_debut=date_debut_obj,
            date_fin=date_fin_obj
        )

        return JsonResponse({'success': True, 'message': '✅ Affectation créée', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def affectation_update_ajax(request, pk):
    """Modifier une affectation via AJAX"""
    try:
        affectation = get_object_or_404(ZYAF, pk=pk)
        poste_id = request.POST.get('poste_id')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([poste_id, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        poste = get_object_or_404(ZDPO, pk=poste_id)
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        if not date_fin_obj:
            affectations_actives = ZYAF.objects.filter(
                employe=affectation.employe,
                date_fin__isnull=True
            ).exclude(pk=pk)
            if affectations_actives.exists():
                return JsonResponse({'success': False, 'error': '❌ Une autre affectation active existe'})

        base_queryset = ZYAF.objects.filter(employe=affectation.employe)
        has_overlap, overlapping = validate_date_overlap(base_queryset, date_debut_obj, date_fin_obj, pk)

        if has_overlap:
            return JsonResponse({'success': False, 'error': '❌ Chevauchement détecté'})

        affectation.poste = poste
        affectation.date_debut = date_debut_obj
        affectation.date_fin = date_fin_obj
        affectation.save()

        return JsonResponse({'success': True, 'message': '✅ Affectation modifiée', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def affectation_delete_ajax(request, pk):
    """Supprimer une affectation via AJAX"""
    try:
        affectation = get_object_or_404(ZYAF, pk=pk)
        affectation.delete()
        return JsonResponse({'success': True, 'message': '✅ Affectation supprimée', **get_active_tab_for_ajax(request)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========================================
# TÉLÉPHONES (ZYTE)
# ========================================

@require_POST
def telephone_create_ajax(request):
    """Créer un téléphone via AJAX"""
    try:
        employe_matricule = request.POST.get('employe_matricule')
        numero = request.POST.get('numero')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([employe_matricule, numero, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        # ✅ NOUVEAU CODE
        employe_identifier = request.POST.get('employe_matricule')  # Peut être UUID ou matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        ZYTE.objects.create(
            employe=employe,
            numero=numero,
            date_debut_validite=date_debut_obj,
            date_fin_validite=date_fin_obj
        )

        return JsonResponse({'success': True, 'message': '✅ Téléphone ajouté', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def telephone_update_ajax(request, pk):
    """Modifier un téléphone via AJAX"""
    try:
        telephone = get_object_or_404(ZYTE, pk=pk)
        numero = request.POST.get('numero')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([numero, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        telephone.numero = numero
        telephone.date_debut_validite = date_debut_obj
        telephone.date_fin_validite = date_fin_obj
        telephone.save()

        return JsonResponse({'success': True, 'message': '✅ Téléphone modifié', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def telephone_delete_ajax(request, pk):
    """Supprimer un téléphone via AJAX"""
    try:
        telephone = get_object_or_404(ZYTE, pk=pk)
        telephone.delete()
        return JsonResponse({'success': True, 'message': '✅ Téléphone supprimé', **get_active_tab_for_ajax(request)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========================================
# EMAILS (ZYME)
# ========================================

@require_POST
def email_create_ajax(request):
    """Créer un email via AJAX"""
    try:
        employe_matricule = request.POST.get('employe_matricule')
        email = request.POST.get('email')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([employe_matricule, email, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        # ✅ NOUVEAU CODE
        employe_identifier = request.POST.get('employe_matricule')  # Peut être UUID ou matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        ZYME.objects.create(
            employe=employe,
            email=email,
            date_debut_validite=date_debut_obj,
            date_fin_validite=date_fin_obj
        )

        return JsonResponse({'success': True, 'message': '✅ Email ajouté', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def email_update_ajax(request, pk):
    """Modifier un email via AJAX"""
    try:
        email_obj = get_object_or_404(ZYME, pk=pk)
        email = request.POST.get('email')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([email, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        email_obj.email = email
        email_obj.date_debut_validite = date_debut_obj
        email_obj.date_fin_validite = date_fin_obj
        email_obj.save()

        return JsonResponse({'success': True, 'message': '✅ Email modifié', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def email_delete_ajax(request, pk):
    """Supprimer un email via AJAX"""
    try:
        email = get_object_or_404(ZYME, pk=pk)
        email.delete()
        return JsonResponse({'success': True, 'message': '✅ Email supprimé', **get_active_tab_for_ajax(request)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========================================
# ADRESSES (ZYAD)
# ========================================

@require_POST
def adresse_create_ajax(request):
    """Créer une adresse via AJAX"""
    try:
        employe_matricule = request.POST.get('employe_matricule')
        rue = request.POST.get('rue')
        ville = request.POST.get('ville')
        pays = request.POST.get('pays')
        code_postal = request.POST.get('code_postal')
        type_adresse = request.POST.get('type_adresse')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([employe_matricule, rue, ville, pays, code_postal, type_adresse, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        employe_identifier = request.POST.get('employe_matricule')  # Peut être UUID ou matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        # Vérifier une seule adresse principale active
        if type_adresse == 'PRINCIPALE' and not date_fin_obj:
            adresses_principales = ZYAD.objects.filter(
                employe=employe,
                type_adresse='PRINCIPALE',
                date_fin__isnull=True
            )
            if adresses_principales.exists():
                return JsonResponse({
                    'success': False,
                    'error': '❌ Une adresse principale active existe déjà'
                })

        ZYAD.objects.create(
            employe=employe,
            rue=rue,
            ville=ville,
            pays=pays,
            code_postal=code_postal,
            type_adresse=type_adresse,
            date_debut=date_debut_obj,
            date_fin=date_fin_obj
        )

        return JsonResponse({'success': True, 'message': '✅ Adresse ajoutée', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def adresse_update_ajax(request, pk):
    """Modifier une adresse via AJAX"""
    try:
        adresse = get_object_or_404(ZYAD, pk=pk)
        rue = request.POST.get('rue')
        ville = request.POST.get('ville')
        pays = request.POST.get('pays')
        code_postal = request.POST.get('code_postal')
        type_adresse = request.POST.get('type_adresse')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not all([rue, ville, pays, code_postal, type_adresse, date_debut]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            return JsonResponse({'success': False, 'error': '❌ Date fin > date début'})

        if type_adresse == 'PRINCIPALE' and not date_fin_obj:
            adresses_principales = ZYAD.objects.filter(
                employe=adresse.employe,
                type_adresse='PRINCIPALE',
                date_fin__isnull=True
            ).exclude(pk=pk)
            if adresses_principales.exists():
                return JsonResponse({'success': False, 'error': '❌ Une autre adresse principale active existe'})

        adresse.rue = rue
        adresse.ville = ville
        adresse.pays = pays
        adresse.code_postal = code_postal
        adresse.type_adresse = type_adresse
        adresse.date_debut = date_debut_obj
        adresse.date_fin = date_fin_obj
        adresse.save()

        return JsonResponse({'success': True, 'message': '✅ Adresse modifiée', **get_active_tab_for_ajax(request)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@require_POST
def adresse_delete_ajax(request, pk):
    """Supprimer une adresse via AJAX"""
    try:
        adresse = get_object_or_404(ZYAD, pk=pk)
        adresse.delete()
        return JsonResponse({'success': True, 'message': '✅ Adresse supprimée', **get_active_tab_for_ajax(request)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def document_create_ajax(request):
    """Créer un document via AJAX"""
    try:
        employe_identifier = request.POST.get('employe_matricule')
        type_document = request.POST.get('type_document')
        description = request.POST.get('description', '')
        fichier = request.FILES.get('fichier')

        # Validation des champs obligatoires
        if not all([employe_identifier, type_document, fichier]):
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants'})

        # Récupérer l'employé par UUID ou matricule
        try:
            employe = get_object_or_404(ZY00, uuid=employe_identifier)
        except:
            employe = get_object_or_404(ZY00, matricule=employe_identifier)

        # Vérifier la taille du fichier (max 10 Mo)
        if fichier.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Le fichier ne doit pas dépasser 10 Mo.'})

        # Vérifier l'extension
        ext = os.path.splitext(fichier.name)[1].lower()
        extensions_autorisees = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
        if ext not in extensions_autorisees:
            return JsonResponse({
                'success': False,
                'error': f'Extension non autorisée. Extensions autorisées : {", ".join(extensions_autorisees)}'
            })

        # Créer le document
        document = ZYDO.objects.create(
            employe=employe,
            type_document=type_document,
            description=description,
            fichier=fichier
        )

        return JsonResponse({
            'success': True,
            'message': f'✅ Document "{document.get_type_document_display()}" ajouté avec succès',
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def document_delete_ajax(request, pk):
    """Supprimer un document via AJAX"""
    try:
        document = get_object_or_404(ZYDO, pk=pk, actif=True)
        document.delete()

        return JsonResponse({
            'success': True,
            'message': f'✅ Document ✅ supprimé avec succès',
            **get_active_tab_for_ajax(request)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def gerer_documents_employe(request, matricule):
    """Page pour joindre et gérer les documents d'un employé"""
    employe = get_object_or_404(ZY00, matricule=matricule)
    documents = ZYDO.objects.filter(employe=employe, actif=True)

    # Récupérer les choix directement depuis le modèle
    type_documents = ZYDO.TYPE_DOCUMENT_CHOICES

    context = {
        'employe': employe,
        'documents': documents,
        'type_documents': type_documents,
    }
    return render(request, 'employee/modal/modal_employee.html', context)


@login_required
def telecharger_document(request, pk):
    """Télécharger un document"""
    document = get_object_or_404(ZYDO, pk=pk, actif=True)

    try:
        response = FileResponse(document.fichier.open('rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{document.get_nom_fichier()}"'
        return response
    except FileNotFoundError:
        raise Http404("Fichier introuvable")



@require_POST
@login_required
def modifier_photo_ajax(request):
    """Vue AJAX pour modifier la photo de profil d'un employé"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        photo = request.FILES.get('photo')

        if not employe_uuid or not photo:
            return JsonResponse({
                'success': False,
                'error': 'UUID de l\'employé ou photo manquant'
            })

        # Récupérer l'employé
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Vérifier la taille du fichier (max 5MB)
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'La taille de la photo ne doit pas dépasser 5 MB'
            })

        # Vérifier l'extension du fichier
        ext = os.path.splitext(photo.name)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        if ext not in valid_extensions:
            return JsonResponse({
                'success': False,
                'error': f'Format non autorisé. Formats acceptés: {", ".join(valid_extensions)}'
            })

        # Supprimer l'ancienne photo si elle existe
        if employe.photo:
            try:
                if os.path.isfile(employe.photo.path):
                    os.remove(employe.photo.path)
            except Exception:
                pass  # Ignorer les erreurs de suppression

        # Enregistrer la nouvelle photo
        employe.photo = photo
        employe.save()

        return JsonResponse({
            'success': True,
            'photo_url': employe.get_photo_url(),
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Alternative: Vue pour supprimer la photo
@require_POST
@login_required
def supprimer_photo_ajax(request, uuid):
    """Vue AJAX pour supprimer la photo de profil d'un employé"""
    try:
        employe = get_object_or_404(ZY00, uuid=uuid)

        # Supprimer le fichier photo
        if employe.photo:
            try:
                if os.path.isfile(employe.photo.path):
                    os.remove(employe.photo.path)
            except Exception:
                pass

            # Supprimer la référence dans la base de données
            employe.photo = None
            employe.save()

        return JsonResponse({
            'success': True,
            'photo_url': employe.get_photo_url(), # Retourne l'URL de la photo par défaut
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def dossierSortie(request):
    return render(request, "employee/dossier-sortie.html")


def profilEmployee(request):
    return render(request, "employee/profil-employee.html")


def conges(request):
    return render(request, "employee/conges-employee.html")


def validerConges(request):
    return render(request, "employee/valider-conges.html")


def feuilleDeTemps(request):
    return render(request, "employee/feuille-de-temps.html")


def planification(request):
    return render(request, "employee/planification.html")


def presence(request):
    return render(request, "employee/presence.html")
# Create your views here.

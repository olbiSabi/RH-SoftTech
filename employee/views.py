from datetime import datetime
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import  Http404, JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from absence.decorators import drh_or_admin_required, gestion_app_required
from .decorators import custom_permission_required, DRHOrAssistantRHRequiredMixin, DRHOrAdminRequiredMixin
from .utils import get_redirect_url_with_tab, get_active_tab_for_ajax
from departement.models import ZDPO, ZDDE
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYNP, ZYPP, ZYIB, ZYRO, ZYRE
from .forms import (
    ZY00Form, EmbaucheAgentForm, ZYCOForm, ZYTEForm,
    ZYMEForm, ZYAFForm, ZYADForm, ZYFAForm
)
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from absence.models import AcquisitionConges, Absence
from datetime import date
from django.db.models import Q, Count
from datetime import timedelta

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

#@custom_permission_required('peut_embaucher')
@drh_or_admin_required
@login_required
def embauche_agent(request):
    """Vue pour l'embauche d'un nouvel agent (pré-embauche)"""
    if request.method == 'POST':
        form = EmbaucheAgentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Créer l'employé avec tous les champs
                    employe = form.save(commit=False)
                    employe.type_dossier = 'PRE'  # Pré-embauche par défaut
                    employe.etat = 'actif'  # Actif par défaut

                    # INITIALISER username ET prenomuser
                    employe.username = employe.nom
                    employe.prenomuser = employe.prenoms

                    # Sauvegarder l'employé (génération automatique du matricule)
                    employe.save()

                    # ✅ CRÉATION AUTOMATIQUE DU COMPTE USER AVEC MOT DE PASSE FIXE
                    username, password = create_user_account(employe)

                    # CRÉATION AUTOMATIQUE DANS ZYNP (Historique nom/prénom)
                    znp = ZYNP.objects.create(
                        employe=employe,
                        nom=employe.nom,
                        prenoms=employe.prenoms,
                        date_debut_validite=timezone.now().date(),
                        actif=True
                    )

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
                        complement=form.cleaned_data['complement'],
                        pays=form.cleaned_data['pays'],
                        code_postal=form.cleaned_data['code_postal'],
                        type_adresse='PRINCIPALE',
                        date_debut=form.cleaned_data['date_debut_adresse']
                    )

                    messages.success(
                        request,
                        f"✅ Pré-embauche de {employe.nom} {employe.prenoms} créée avec succès ! "
                        f"Matricule : {employe.matricule}"
                    )

                    # Rediriger vers la liste des employés
                    return redirect('employee:liste_employes')

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erreur lors de la création de la pré-embauche : {str(e)}"
                )
                return render(request, 'employee/embauche-agent.html', {'form': form})
        else:
            messages.error(
                request,
                "❌ Le formulaire contient des erreurs. Veuillez corriger les champs indiqués ci-dessous."
            )
    else:
        form = EmbaucheAgentForm()
        # Pré-remplir les dates avec aujourd'hui
        from datetime import date
        form.fields['date_entree_entreprise'].initial = date.today()
        form.fields['date_debut_adresse'].initial = date.today()
        form.fields['date_debut_contrat'].initial = date.today()

    return render(request, 'employee/embauche-agent.html', {'form': form})

@drh_or_admin_required
@login_required
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
    base_url = reverse('employee:detail_employe', kwargs={'uuid': uuid})
    redirect_url = get_redirect_url_with_tab(request, base_url)
    return redirect(redirect_url)


def create_user_account(employe):
    """
    Crée un compte utilisateur pour un employé
    Retourne (username, password)
    """
    # Générer un username unique basé sur le nom et prénom
    base_username = f"{employe.nom.lower()}.{employe.prenoms.split()[0].lower()}"
    username = base_username

    # Vérifier si le username existe déjà et ajouter un suffixe si nécessaire
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    # ✅ MOT DE PASSE FIXE
    password = "Hronian2024!"

    # Créer l'utilisateur
    user = User.objects.create_user(
        username=username,
        password=password,  # ← Mot de passe fixe
        first_name=employe.prenomuser or employe.prenoms.split()[0],
        last_name=employe.username or employe.nom,
        email=getattr(employe, 'email', f"{username}@onian-easym.com")
    )

    # Lier l'utilisateur à l'employé
    employe.user = user
    employe.save()

    return username, password
# ===============================
# VUES POUR LES EMPLOYÉS (ZY00)
# ===============================

class EmployeListView(LoginRequiredMixin, DRHOrAdminRequiredMixin, ListView):
    """Liste de tous les employés"""
    login_url = 'login'  # Optionnel : spécifier l'URL de connexion
    redirect_field_name = 'next'  # Optionnel : redirection après connexion
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

class EmployeCreateView(LoginRequiredMixin, DRHOrAdminRequiredMixin, CreateView):
    """Créer un employé"""
    login_url = 'login'
    model = ZY00
    form_class = ZY00Form
    template_name = 'employes/employe_form.html'
    success_url = reverse_lazy('employee:liste_employes')

    def form_valid(self, form):
        messages.success(self.request, "Employé créé avec succès!")
        return super().form_valid(form)

class EmployeUpdateView(LoginRequiredMixin, DRHOrAdminRequiredMixin, UpdateView):
    """Modifier un employé"""
    login_url = 'login'
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
        base_url = reverse('employee:detail_employe', kwargs={'uuid': self.object.uuid})
        return get_redirect_url_with_tab(self.request, base_url)

class EmployeDeleteView(LoginRequiredMixin, DRHOrAdminRequiredMixin, DeleteView):
    """Supprimer un employé (suppression en cascade)"""
    login_url = 'login'
    model = ZY00
    template_name = 'employee/employe_confirm_delete.html'
    success_url = reverse_lazy('employee:liste_employes')
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        uuid = self.kwargs.get('uuid')
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        return get_object_or_404(queryset)

    def form_valid(self, form):
        """Surcharge de form_valid pour gérer la suppression du user"""
        employe = self.object
        print(f"🚀 DEBUG - Début suppression dans form_valid")
        print(f"   Employé: {employe.matricule} - {employe.nom} {employe.prenoms}")
        print(f"   User ID: {employe.user_id}")

        try:
            # Sauvegarder les infos pour les messages
            employe_nom = f"{employe.nom} {employe.prenoms}"
            employe_matricule = employe.matricule

            # Gestion de la suppression du user
            if employe.user:
                user = employe.user
                username = user.username

                print(f"🔍 DEBUG - Suppression du user {username}")

                # Dissocier d'abord
                employe.user = None
                employe.save(update_fields=['user'])

                # Supprimer le user
                user.delete()
                print(f"✅ DEBUG - User {username} supprimé")
                messages.info(self.request, f"Compte utilisateur '{username}' supprimé.")

            # Maintenant supprimer l'employé via la méthode parent
            print(f"🗑️ DEBUG - Suppression de l'employé {employe_matricule}")
            response = super().form_valid(form)

            print(f"✅ DEBUG - Suppression terminée avec succès")
            messages.success(self.request, f"Employé {employe_nom} supprimé avec succès!")

            return response

        except Exception as e:
            print(f"❌ DEBUG - Erreur: {str(e)}")
            import traceback
            traceback.print_exc()

            messages.error(self.request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('employee:detail_employe', uuid=employe.uuid)

class DossierIndividuelView(LoginRequiredMixin, DRHOrAssistantRHRequiredMixin, ListView):
    login_url = 'login'
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

        # ✅ AJOUT : Liste des départements pour le modal d'affectation
        context['departements'] = ZDDE.objects.all().order_by('LIBELLE')

        # Vérifier si un UUID est passé dans l'URL
        uuid = self.kwargs.get('uuid')
        if uuid:
            employe_selectionne = get_object_or_404(ZY00, uuid=uuid)

            # Données de l'employé
            context['employe'] = employe_selectionne
            # Historique des noms/prénoms
            historique_actif = get_historique_actif(employe_selectionne)
            context['historique_actif'] = historique_actif
            context['historique_noms_prenoms'] = employe_selectionne.historique_noms_prenoms.all().order_by('-date_debut_validite')
            # Personnes à prévenir
            context['personnes_prevenir'] = employe_selectionne.personnes_prevenir.all().order_by('ordre_priorite','-date_debut_validite')
            # Entités liées (optimisées avec select_related)
            context['contrats'] = employe_selectionne.contrats.all().order_by('-date_debut')
            context['affectations'] = employe_selectionne.affectations.select_related('poste__DEPARTEMENT').order_by('-date_debut')
            context['telephones'] = employe_selectionne.telephones.all().order_by('-date_debut_validite')
            context['emails'] = employe_selectionne.emails.all().order_by('-date_debut_validite')
            context['adresses'] = employe_selectionne.adresses.all().order_by('-date_debut')
            context['documents'] = employe_selectionne.documents.all().order_by('-date_ajout')

            # AJOUT CRITIQUE : Personnes à charge et statistiques
            personnes_charge = employe_selectionne.personnes_charge.all()
            context['personnes_charge'] = personnes_charge

            # Personnes à prévenir
            context['nb_personnes_prevenir'] = employe_selectionne.personnes_prevenir.filter(actif=True,date_fin_validite__isnull=True).count()
            # Calcul des statistiques famille
            context['nb_total'] = personnes_charge.count()
            context['nb_enfants'] = personnes_charge.filter(personne_charge='ENFANT').count()
            context['nb_conjoints'] = personnes_charge.filter(personne_charge='CONJOINT').count()
            context['nb_actifs'] = personnes_charge.filter(actif=True).count()
            # AJOUT : Identité bancaire (RIB)
            try:
                context['identite_bancaire'] = employe_selectionne.identite_bancaire
                context['has_identite_bancaire'] = True
            except ZYIB.DoesNotExist:
                context['identite_bancaire'] = None
                context['has_identite_bancaire'] = False
            # Postes disponibles pour le modal d'affectation
            context['postes'] = ZDPO.objects.filter(STATUT=True).select_related('DEPARTEMENT').order_by('DEPARTEMENT__LIBELLE', 'CODE')

        # Variables de test
        context['test_variable'] = "Hello World"
        context['test_number'] = 42

        return context

    def get(self, request, *args, **kwargs):
        # Cette méthode permet de gérer les deux cas :
        # - Accès à la liste seule
        # - Accès à la liste + détail d'un employé
        return super().get(request, *args, **kwargs)


@login_required
@drh_or_admin_required
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


# ===== API GESTION DE ROLE EMPLOYE (ZYRE) =====
@login_required
@gestion_app_required
def gestion_roles_employes(request):
    """
    Page principale de gestion des rôles employés
    """
    # Filtres
    filtre_employe = request.GET.get('employe', '')
    filtre_role = request.GET.get('role', '')
    filtre_statut = request.GET.get('statut', 'actif')  # actif, inactif, tous

    # Base query
    attributions_base = ZYRE.objects.select_related(
        'employe', 'role', 'created_by'
    )

    # Appliquer les filtres
    attributions = attributions_base

    if filtre_employe:
        attributions = attributions.filter(
            Q(employe__matricule__icontains=filtre_employe) |
            Q(employe__nom__icontains=filtre_employe) |
            Q(employe__prenoms__icontains=filtre_employe)
        )

    if filtre_role:
        attributions = attributions.filter(role_id=filtre_role)

    if filtre_statut == 'actif':
        attributions = attributions.filter(actif=True, date_fin__isnull=True)
    elif filtre_statut == 'inactif':
        attributions = attributions.filter(
            Q(actif=False) | Q(date_fin__isnull=False)
        )

    attributions = attributions.order_by('-created_at')

    # Statistiques
    stats = {
        'total': ZYRE.objects.count(),
        'actifs': ZYRE.objects.filter(actif=True, date_fin__isnull=True).count(),
        'inactifs': ZYRE.objects.filter(
            Q(actif=False) | Q(date_fin__isnull=False)
        ).count(),
        'roles_distincts': ZYRO.objects.filter(
            attributions__actif=True
        ).distinct().count(),
    }

    # Données pour les filtres
    roles = ZYRO.objects.filter(actif=True).order_by('LIBELLE')
    employes = ZY00.objects.filter(
        type_dossier='SAL',
        etat='actif'
    ).order_by('nom', 'prenoms')

    context = {
        'attributions': attributions,
        'stats': stats,
        'roles': roles,
        'employes': employes,
        'filtre_employe': filtre_employe,
        'filtre_role': filtre_role,
        'filtre_statut': filtre_statut,
    }

    return render(request, 'employee/gestion_roles.html', context)


@login_required
@require_http_methods(["POST"])
@gestion_app_required
def attribuer_role(request):
    """
    Attribuer un rôle à un employé (AJAX)
    """
    try:
        employe_id = request.POST.get('employe_id')
        role_id = request.POST.get('role_id')
        date_debut = request.POST.get('date_debut')
        commentaire = request.POST.get('commentaire', '').strip()

        # Validation
        if not all([employe_id, role_id, date_debut]):
            return JsonResponse({
                'success': False,
                'error': 'Tous les champs obligatoires doivent être remplis'
            }, status=400)

        employe = get_object_or_404(ZY00, uuid=employe_id)
        role = get_object_or_404(ZYRO, pk=role_id)

        # ✅ Vérification améliorée
        existing = ZYRE.objects.filter(
            employe=employe,
            role=role,
            actif=True,
            date_fin__isnull=True
        )

        if existing.exists():
            return JsonResponse({
                'success': False,
                'error': f'Le rôle "{role.LIBELLE}" est déjà actif pour {employe.nom} {employe.prenoms}'
            }, status=400)

        with transaction.atomic():
            # Créer l'attribution
            attribution = ZYRE.objects.create(
                employe=employe,
                role=role,
                date_debut=date_debut,
                actif=True,
                commentaire=commentaire,
                created_by=request.user.employe if hasattr(request.user, 'employe') else None
            )

            return JsonResponse({
                'success': True,
                'message': f'✅ Rôle "{role.LIBELLE}" attribué à {employe.nom} {employe.prenoms} avec succès',
                'attribution_id': str(attribution.pk)
            })

    except ValidationError as ve:
        # ✅ Capturer les erreurs de validation
        return JsonResponse({
            'success': False,
            'error': str(ve)
        }, status=400)

    except Exception as e:
        # ✅ Logger l'erreur pour debug
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'attribution : {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@gestion_app_required
def retirer_role(request, attribution_id):
    """
    Retirer un rôle (désactiver l'attribution)
    """
    try:
        attribution = get_object_or_404(ZYRE, pk=attribution_id)

        if not attribution.actif or attribution.date_fin:
            return JsonResponse({
                'success': False,
                'error': 'Cette attribution est déjà inactive'
            }, status=400)

        with transaction.atomic():
            attribution.actif = False
            attribution.date_fin = date.today()
            attribution.save()

            return JsonResponse({
                'success': True,
                'message': f'✅ Rôle "{attribution.role.LIBELLE}" retiré de {attribution.employe.nom}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@gestion_app_required
def reactiver_role(request, attribution_id):
    """
    Réactiver un rôle
    """
    try:
        attribution = get_object_or_404(ZYRE, pk=attribution_id)

        if attribution.actif and not attribution.date_fin:
            return JsonResponse({
                'success': False,
                'error': 'Cette attribution est déjà active'
            }, status=400)

        # Vérifier qu'il n'y a pas déjà une attribution active pour ce rôle
        existing = ZYRE.objects.filter(
            employe=attribution.employe,
            role=attribution.role,
            actif=True,
            date_fin__isnull=True
        ).exclude(pk=attribution.pk).exists()

        if existing:
            return JsonResponse({
                'success': False,
                'error': f'Le rôle "{attribution.role.LIBELLE}" est déjà actif pour cet employé'
            }, status=400)

        with transaction.atomic():
            attribution.actif = True
            attribution.date_fin = None
            attribution.save()

            return JsonResponse({
                'success': True,
                'message': f'✅ Rôle "{attribution.role.LIBELLE}" réactivé pour {attribution.employe.nom}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@gestion_app_required
def modifier_role(request, attribution_id):
    """
    Modifier une attribution de rôle
    """
    try:
        attribution = get_object_or_404(ZYRE, pk=attribution_id)

        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        with transaction.atomic():
            if date_debut:
                attribution.date_debut = date_debut

            if date_fin:
                attribution.date_fin = date_fin
                attribution.actif = False
            else:
                attribution.date_fin = None
                attribution.actif = True

            attribution.commentaire = commentaire
            attribution.save()

            return JsonResponse({
                'success': True,
                'message': f'✅ Attribution modifiée avec succès'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def roles_employe(request, employe_uuid):
    """
    API pour récupérer tous les rôles d'un employé
    """
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        attributions = ZYRE.objects.filter(
            employe=employe
        ).select_related('role').order_by('-date_debut')

        roles_data = []
        for attr in attributions:
            roles_data.append({
                'id': attr.pk,
                'role_code': attr.role.CODE,
                'role_libelle': attr.role.LIBELLE,
                'date_debut': attr.date_debut.strftime('%d/%m/%Y'),
                'date_fin': attr.date_fin.strftime('%d/%m/%Y') if attr.date_fin else None,
                'actif': attr.actif,
                'commentaire': attr.commentaire or '',
            })

        return JsonResponse({
            'success': True,
            'roles': roles_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@gestion_app_required
def supprimer_role(request, attribution_id):
    """
    Supprimer définitivement une attribution de rôle
    """
    try:
        attribution = get_object_or_404(ZYRE, pk=attribution_id)

        employe_nom = f"{attribution.employe.nom} {attribution.employe.prenoms}"
        role_libelle = attribution.role.LIBELLE

        with transaction.atomic():
            # Retirer le rôle du groupe Django si l'employé a un user
            if hasattr(attribution.employe, 'user') and attribution.employe.user:
                if attribution.role.django_group:
                    attribution.employe.user.groups.remove(attribution.role.django_group)

            # Supprimer l'attribution
            attribution.delete()

            return JsonResponse({
                'success': True,
                'message': f'✅ Rôle "{role_libelle}" supprimé définitivement pour {employe_nom}'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def profil_employe(request, matricule):
    """Vue du profil employé"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    # Contacts d'urgence
    contacts_urgence = employe.personnes_prevenir.filter(
        actif=True,
        date_fin_validite__isnull=True
    ).order_by('ordre_priorite')

    # ✅ CORRECTION : Acquisition de congés de l'année N-1 (pour consommation en année N)
    annee_actuelle = date.today().year
    annee_acquisition = annee_actuelle - 1  # Année précédente

    try:
        acquisition_conges = AcquisitionConges.objects.get(
            employe=employe,
            annee_reference=annee_acquisition  # ✅ N-1
        )
    except AcquisitionConges.DoesNotExist:
        acquisition_conges = None

    # ✅ Absences de l'année en cours (qui consomment les congés de N-1)
    absences = Absence.objects.filter(
        employe=employe,
        date_debut__year=annee_actuelle  # ✅ Absences de l'année N
    ).select_related('type_absence').order_by('-date_debut')[:10]

    # Documents
    documents = employe.documents.filter(actif=True).order_by('-date_ajout')

    context = {
        'employe': employe,
        'contacts_urgence': contacts_urgence,
        'acquisition_conges': acquisition_conges,
        'annee_acquisition': annee_acquisition,  # ✅ Pour affichage
        'annee_consommation': annee_actuelle,  # ✅ Pour affichage
        'absences': absences,
        'documents': documents,
    }

    return render(request, 'employee/profil.html', context)


@login_required
@require_POST
def upload_photo(request, matricule):
    """Upload de la photo de profil"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    if 'photo' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucune photo fournie'})

    try:
        employe.photo = request.FILES['photo']
        employe.save()

        return JsonResponse({
            'success': True,
            'photo_url': employe.get_photo_url()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_contact_urgence(request, matricule):
    """Créer un contact d'urgence"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    try:
        contact = ZYPP.objects.create(
            employe=employe,
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            lien_parente=request.POST.get('lien_parente'),
            telephone_principal=request.POST.get('telephone_principal'),
            telephone_secondaire=request.POST.get('telephone_secondaire') or None,
            email=request.POST.get('email') or None,
            adresse=request.POST.get('adresse') or None,
            ordre_priorite=request.POST.get('ordre_priorite'),
            remarques=request.POST.get('remarques') or None,
            actif=True
        )

        return JsonResponse({'success': True, 'id': contact.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def contact_urgence_detail(request, contact_id):
    """Détails d'un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    return JsonResponse({
        'id': contact.id,
        'nom': contact.nom,
        'prenom': contact.prenom,
        'lien_parente': contact.lien_parente,
        'telephone_principal': contact.telephone_principal,
        'telephone_secondaire': contact.telephone_secondaire,
        'email': contact.email,
        'adresse': contact.adresse,
        'ordre_priorite': contact.ordre_priorite,
        'remarques': contact.remarques,
    })


@login_required
@require_POST
def update_contact_urgence(request, contact_id):
    """Modifier un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    try:
        contact.nom = request.POST.get('nom')
        contact.prenom = request.POST.get('prenom')
        contact.lien_parente = request.POST.get('lien_parente')
        contact.telephone_principal = request.POST.get('telephone_principal')
        contact.telephone_secondaire = request.POST.get('telephone_secondaire') or None
        contact.email = request.POST.get('email') or None
        contact.adresse = request.POST.get('adresse') or None
        contact.ordre_priorite = request.POST.get('ordre_priorite')
        contact.remarques = request.POST.get('remarques') or None
        contact.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def delete_contact_urgence(request, contact_id):
    """Supprimer un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    try:
        contact.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def upload_document(request, matricule):
    """Upload d'un document pour l'employé"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    if 'fichier' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'})

    try:
        # Vérifier la taille du fichier (max 10 MB)
        fichier = request.FILES['fichier']
        if fichier.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Le fichier est trop volumineux (max 10 MB)'})

        # Vérifier l'extension
        ext = os.path.splitext(fichier.name)[1].lower()
        extensions_autorisees = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
        if ext not in extensions_autorisees:
            return JsonResponse({
                'success': False,
                'error': f'Format de fichier non autorisé. Formats acceptés : {", ".join(extensions_autorisees)}'
            })

        # Créer le document
        document = ZYDO.objects.create(
            employe=employe,
            type_document=request.POST.get('type_document'),
            description=request.POST.get('description', ''),
            fichier=fichier,
            actif=True
        )

        return JsonResponse({
            'success': True,
            'id': document.id,
            'message': 'Document ajouté avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def delete_document(request, document_id):
    """Supprimer un document"""
    document = get_object_or_404(ZYDO, id=document_id)

    try:
        # Supprimer le fichier physique
        if document.fichier and os.path.isfile(document.fichier.path):
            os.remove(document.fichier.path)

        # Supprimer l'enregistrement en base
        document.delete()

        return JsonResponse({'success': True, 'message': 'Document supprimé avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def dashboard(request):
    """
    Dashboard principal avec statistiques RH
    """
    # ========================================
    # STATISTIQUES EMPLOYÉS
    # ========================================

    # Total employés
    total_employes = ZY00.objects.count()

    # Employés actifs
    employes_actifs = ZY00.objects.filter(etat='actif').count()

    # Employés en attente (nouveau statut ou à valider)
    employes_attente = ZY00.objects.filter(
        Q(etat='en_attente') | Q(etat='nouveau')
    ).count()

    # Contrats actifs (contrats non expirés)
    date_actuelle = timezone.now().date()
    contrats_actifs = ZYCO.objects.filter(
        Q(date_fin__gte=date_actuelle) | Q(date_fin__isnull=True),
        actif=True
    ).count()

    # ========================================
    # NOUVEAUX EMPLOYÉS (30 derniers jours)
    # ========================================

    date_limite = date_actuelle - timedelta(days=30)

    # Employés en attente de validation
    embauches_attente = ZY00.objects.filter(
        etat='en_attente',
        date_entree_entreprise__gte=date_limite
    ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

    # Dernières embauches validées
    dernieres_embauches = ZY00.objects.filter(
        etat='actif',
        date_entree_entreprise__gte=date_limite
    ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

    # ========================================
    # STATISTIQUES ABSENCES
    # ========================================

    # Absences en attente de validation
    absences_attente_manager = Absence.objects.filter(
        statut='EN_ATTENTE_MANAGER'
    ).count()

    absences_attente_rh = Absence.objects.filter(
        statut='EN_ATTENTE_RH'
    ).count()

    absences_total_attente = absences_attente_manager + absences_attente_rh

    # Absences du mois en cours
    premier_jour_mois = date_actuelle.replace(day=1)
    absences_mois = Absence.objects.filter(
        date_debut__gte=premier_jour_mois,
        statut='VALIDE'
    ).count()

    # ========================================
    # DÉPARTEMENTS
    # ========================================

    # Total départements
    total_departements = ZDDE.objects.filter(actif=True).count()

    # Départements avec leur effectif
    departements_effectifs = ZDDE.objects.filter(actif=True).annotate(
        effectif=Count('postes__affectations', filter=Q(
            postes__affectations__date_fin__isnull=True,
            postes__affectations__employe__etat='actif'
        ))
    ).order_by('-effectif')[:5]

    # ========================================
    # ANNIVERSAIRES DE TRAVAIL (ce mois)
    # ========================================

    mois_actuel = date_actuelle.month
    anniversaires = ZY00.objects.filter(
        etat='actif',
        date_entree_entreprise__month=mois_actuel
    ).exclude(
        date_entree_entreprise__year=date_actuelle.year
    ).select_related('entreprise').order_by('date_entree_entreprise')[:10]

    # ========================================
    # CONTRATS ARRIVANT À ÉCHÉANCE (60 jours)
    # ========================================

    date_limite_contrat = date_actuelle + timedelta(days=60)
    contrats_echeance = ZYCO.objects.filter(
        date_fin__gte=date_actuelle,
        date_fin__lte=date_limite_contrat,
        actif=True
    ).select_related('employe', 'employe__entreprise').order_by('date_fin')[:5]

    # ========================================
    # SOLDES DE CONGÉS À SURVEILLER
    # ========================================

    annee_acquisition = date_actuelle.year - 1
    soldes_faibles = AcquisitionConges.objects.filter(
        annee_reference=annee_acquisition,
        jours_restants__lte=5,
        jours_restants__gt=0,
        employe__etat='actif'
    ).select_related('employe').order_by('jours_restants')[:5]

    # ========================================
    # CONTEXT
    # ========================================

    context = {
        # Statistiques principales
        'total_employes': total_employes,
        'employes_actifs': employes_actifs,
        'employes_attente': employes_attente,
        'contrats_actifs': contrats_actifs,

        # Embauches
        'embauches_attente': embauches_attente,
        'dernieres_embauches': dernieres_embauches,

        # Absences
        'absences_total_attente': absences_total_attente,
        'absences_attente_manager': absences_attente_manager,
        'absences_attente_rh': absences_attente_rh,
        'absences_mois': absences_mois,

        # Départements
        'total_departements': total_departements,
        'departements_effectifs': departements_effectifs,

        # Alertes
        'anniversaires': anniversaires,
        'contrats_echeance': contrats_echeance,
        'soldes_faibles': soldes_faibles,
    }

    return render(request, 'home.html', context)
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from .utils import get_redirect_url_with_tab, get_active_tab_for_ajax
from departement.models import ZDPO, ZDDE
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYNP, ZYPP, ZYIB
from .forms import (
    ZY00Form, EmbaucheAgentForm, ZYCOForm, ZYTEForm,
    ZYMEForm, ZYAFForm, ZYADForm, ZYFAForm
)
from django.contrib.auth.models import User
from django.db import transaction

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


@login_required
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

                    # INITIALISER username ET prenomuser
                    employe.username = employe.nom
                    employe.prenomuser = employe.prenoms
                    employe.save()

                    # ✅ CRÉATION AUTOMATIQUE DU COMPTE USER AVEC MOT DE PASSE FIXE
                    username, password = create_user_account(employe)

                    # CRÉATION AUTOMATIQUE DANS ZYNP
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

                    return redirect('liste_employes')

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erreur lors de la création de la pré-embauche : {str(e)}"
                )
                return redirect('embauche_agent')
        else:
            messages.error(
                request,
                "❌ Le formulaire contient des erreurs. Veuillez corriger les champs indiqués ci-dessous."
            )
    else:
        form = EmbaucheAgentForm()

    return render(request, 'employee/embauche-agent.html', {'form': form})

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
    base_url = reverse('detail_employe', kwargs={'uuid': uuid})
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

class EmployeListView(LoginRequiredMixin, ListView):
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

class EmployeCreateView(LoginRequiredMixin, CreateView):
    """Créer un employé"""
    login_url = 'login'
    model = ZY00
    form_class = ZY00Form
    template_name = 'employes/employe_form.html'
    success_url = reverse_lazy('liste_employes')

    def form_valid(self, form):
        messages.success(self.request, "Employé créé avec succès!")
        return super().form_valid(form)

class EmployeUpdateView(LoginRequiredMixin, UpdateView):
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
        base_url = reverse('detail_employe', kwargs={'uuid': self.object.uuid})
        return get_redirect_url_with_tab(self.request, base_url)

class EmployeDeleteView(LoginRequiredMixin, DeleteView):
    """Supprimer un employé (suppression en cascade)"""
    login_url = 'login'
    model = ZY00
    template_name = 'employee/employe_confirm_delete.html'
    success_url = reverse_lazy('liste_employes')
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


@login_required
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

class DossierIndividuelView(LoginRequiredMixin, ListView):
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


# ========================================
# ✅ NOUVELLES API POUR LES MODALES
# ========================================

# ===== API ADRESSES (pour modales) =====

@require_http_methods(["GET"])
@login_required
def api_adresse_detail(request, id):
    """Récupérer les détails d'une adresse (pour édition)"""
    try:
        adresse = get_object_or_404(ZYAD, id=id)
        data = {
            'id': adresse.id,
            'type_adresse': adresse.type_adresse,
            'rue': adresse.rue,
            'complement': adresse.complement or '',
            'code_postal': adresse.code_postal,
            'ville': adresse.ville,
            'pays': adresse.pays,
            'date_debut': adresse.date_debut.strftime('%Y-%m-%d') if adresse.date_debut else '',
            'date_fin': adresse.date_fin.strftime('%Y-%m-%d') if adresse.date_fin else '',
            'actif': adresse.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_adresse_create_modal(request):
    """Créer une adresse via modal (retourne JSON)"""
    try:
        print("=" * 50)
        print("📝 DÉBUT api_adresse_create_modal - ADRESSE SECONDAIRE")
        print("=" * 50)

        # Log toutes les données POST reçues
        print("📦 DONNÉES POST REÇUES:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")

        employe_uuid = request.POST.get('employe_uuid')
        print(f"🔍 Employe UUID: {employe_uuid}")

        employe = get_object_or_404(ZY00, uuid=employe_uuid)
        print(f"✅ Employé trouvé: {employe.matricule}")

        # Validation de base
        errors = {}
        required_fields = ['type_adresse', 'rue', 'code_postal', 'ville', 'pays', 'date_debut']
        for field in required_fields:
            value = request.POST.get(field)
            print(f"🔍 Validation {field}: '{value}'")
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            print(f"❌ ERREURS DE VALIDATION: {errors}")
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        type_adresse = request.POST.get('type_adresse')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        print(f"📦 Type adresse: {type_adresse}")
        print(f"📦 Date début: {date_debut}")
        print(f"📦 Date fin: {date_fin}")

        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            print(f"✅ Date début convertie: {date_debut_obj}")
        except Exception as e:
            errors['date_debut'] = ['Format de date invalide']
            print(f"❌ Erreur conversion date_debut: {e}")

        date_fin_obj = None
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                print(f"✅ Date fin convertie: {date_fin_obj}")
            except Exception as e:
                errors['date_fin'] = ['Format de date invalide']
                print(f"❌ Erreur conversion date_fin: {e}")

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            print("❌ Erreur: date_fin <= date_debut")

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Créer l'adresse avec validation
        print("💾 TENTATIVE CRÉATION ADRESSE...")
        with transaction.atomic():
            adresse = ZYAD(
                employe=employe,
                type_adresse=type_adresse,
                rue=request.POST.get('rue'),
                complement=request.POST.get('complement', ''),
                code_postal=request.POST.get('code_postal'),
                ville=request.POST.get('ville'),
                pays=request.POST.get('pays'),
                date_debut=date_debut_obj,
                date_fin=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

            # Valider le modèle
            try:
                print("🔍 Validation full_clean()...")
                adresse.full_clean()
                print("✅ Validation full_clean() réussie")
            except ValidationError as e:
                print(f"❌ ERREUR ValidationError: {e.message_dict}")
                return JsonResponse({'errors': e.message_dict}, status=400)

            adresse.save()
            print(f"✅ ADRESSE CRÉÉE AVEC SUCCÈS - ID: {adresse.id}")

        return JsonResponse({
            'success': True,
            'message': '✅ Adresse créée avec succès',
            'id': adresse.id
        })

    except Exception as e:
        print(f"💥 ERREUR NON GÉRÉE: {str(e)}")
        import traceback
        print(f"🔍 TRACEBACK COMPLET:")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def api_adresse_update_modal(request, id):
    """Mettre à jour une adresse via modal"""
    try:
        adresse = get_object_or_404(ZYAD, id=id)

        # Validation
        errors = {}
        if not request.POST.get('type_adresse'):
            errors['type_adresse'] = ['Ce champ est requis']
        if not request.POST.get('rue'):
            errors['rue'] = ['Ce champ est requis']
        if not request.POST.get('code_postal'):
            errors['code_postal'] = ['Ce champ est requis']
        if not request.POST.get('ville'):
            errors['ville'] = ['Ce champ est requis']
        if not request.POST.get('pays'):
            errors['pays'] = ['Ce champ est requis']
        if not request.POST.get('date_debut'):
            errors['date_debut'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # Mettre à jour l'adresse
        with transaction.atomic():
            adresse.type_adresse = request.POST.get('type_adresse')
            adresse.rue = request.POST.get('rue')
            adresse.complement = request.POST.get('complement', '')
            adresse.code_postal = request.POST.get('code_postal')
            adresse.ville = request.POST.get('ville')
            adresse.pays = request.POST.get('pays')
            adresse.date_debut = date_debut_obj
            adresse.date_fin = date_fin_obj
            adresse.actif = request.POST.get('actif') == 'on'
            adresse.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Adresse modifiée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_adresse_delete_modal(request, id):
    """Supprimer une adresse via modal"""
    try:
        adresse = get_object_or_404(ZYAD, id=id)
        with transaction.atomic():
            adresse.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Adresse supprimée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API TÉLÉPHONES (pour modales) =====

@require_http_methods(["GET"])
@login_required
def api_telephone_detail(request, id):
    """Récupérer les détails d'un téléphone"""
    try:
        telephone = get_object_or_404(ZYTE, id=id)
        data = {
            'id': telephone.id,
            'numero': telephone.numero,
            'date_debut_validite': telephone.date_debut_validite.strftime(
                '%Y-%m-%d') if telephone.date_debut_validite else '',
            'date_fin_validite': telephone.date_fin_validite.strftime(
                '%Y-%m-%d') if telephone.date_fin_validite else '',
            'actif': telephone.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def api_telephone_create_modal(request):
    """Créer un téléphone via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        errors = {}
        if not request.POST.get('numero'):
            errors['numero'] = ['Ce champ est requis']
        if not request.POST.get('date_debut_validite'):
            errors['date_debut_validite'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut_validite'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_validite')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        with transaction.atomic():
            telephone = ZYTE.objects.create(
                employe=employe,
                numero=request.POST.get('numero'),
                date_debut_validite=date_debut_obj,
                date_fin_validite=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Téléphone créé avec succès',
            'id': telephone.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_telephone_update_modal(request, id):
    """Mettre à jour un téléphone via modal"""
    try:
        telephone = get_object_or_404(ZYTE, id=id)

        errors = {}
        if not request.POST.get('numero'):
            errors['numero'] = ['Ce champ est requis']
        if not request.POST.get('date_debut_validite'):
            errors['date_debut_validite'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut_validite'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_validite')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        with transaction.atomic():
            telephone.numero = request.POST.get('numero')
            telephone.date_debut_validite = date_debut_obj
            telephone.date_fin_validite = date_fin_obj
            telephone.actif = request.POST.get('actif') == 'on'
            telephone.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Téléphone modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_telephone_delete_modal(request, id):
    """Supprimer un téléphone via modal"""
    try:
        telephone = get_object_or_404(ZYTE, id=id)
        with transaction.atomic():
            telephone.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Téléphone supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API EMAILS (pour modales) =====

@require_http_methods(["GET"])
@login_required
def api_email_detail(request, id):
    """Récupérer les détails d'un email"""
    try:
        email = get_object_or_404(ZYME, id=id)
        data = {
            'id': email.id,
            'email': email.email,
            'date_debut_validite': email.date_debut_validite.strftime('%Y-%m-%d') if email.date_debut_validite else '',
            'date_fin_validite': email.date_fin_validite.strftime('%Y-%m-%d') if email.date_fin_validite else '',
            'actif': email.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_email_create_modal(request):
    """Créer un email via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        errors = {}
        if not request.POST.get('email'):
            errors['email'] = ['Ce champ est requis']
        if not request.POST.get('date_debut_validite'):
            errors['date_debut_validite'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut_validite'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_validite')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        with transaction.atomic():
            email = ZYME.objects.create(
                employe=employe,
                email=request.POST.get('email'),
                date_debut_validite=date_debut_obj,
                date_fin_validite=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Email créé avec succès',
            'id': email.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_email_update_modal(request, id):
    """Mettre à jour un email via modal"""
    try:
        email = get_object_or_404(ZYME, id=id)

        errors = {}
        if not request.POST.get('email'):
            errors['email'] = ['Ce champ est requis']
        if not request.POST.get('date_debut_validite'):
            errors['date_debut_validite'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut_validite'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_validite')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        with transaction.atomic():
            email.email = request.POST.get('email')
            email.date_debut_validite = date_debut_obj
            email.date_fin_validite = date_fin_obj
            email.actif = request.POST.get('actif') == 'on'
            email.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Email modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_email_delete_modal(request, id):
    """Supprimer un email via modal"""
    try:
        email = get_object_or_404(ZYME, id=id)
        with transaction.atomic():
            email.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Email supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API DOCUMENTS (pour modales) =====

@require_http_methods(["POST"])
@login_required
def api_document_create_modal(request):
    """Créer un document via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        errors = {}
        if not request.POST.get('type_document'):
            errors['type_document'] = ['Ce champ est requis']
        if not request.FILES.get('fichier'):
            errors['fichier'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        fichier = request.FILES.get('fichier')

        # Vérifier la taille du fichier (max 10 Mo)
        if fichier.size > 10 * 1024 * 1024:
            return JsonResponse({'errors': {'fichier': ['Le fichier ne doit pas dépasser 10 Mo']}}, status=400)

        # Vérifier l'extension
        ext = os.path.splitext(fichier.name)[1].lower()
        extensions_autorisees = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
        if ext not in extensions_autorisees:
            return JsonResponse({
                'errors': {
                    'fichier': [f'Extension non autorisée. Extensions autorisées : {", ".join(extensions_autorisees)}']}
            }, status=400)

        with transaction.atomic():
            document = ZYDO.objects.create(
                employe=employe,
                type_document=request.POST.get('type_document'),
                fichier=fichier,
                description=request.POST.get('description', ''),
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Document ajouté avec succès',
            'id': document.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_document_delete_modal(request, id):
    """Supprimer un document via modal"""
    try:
        document = get_object_or_404(ZYDO, id=id)
        with transaction.atomic():
            # Supprimer le fichier physique
            if document.fichier:
                document.fichier.delete()
            document.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Document supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API CONTRATS (pour modales) =====

@require_http_methods(["GET"])
@login_required
def api_contrat_detail(request, id):
    """Récupérer les détails d'un contrat"""
    try:
        contrat = get_object_or_404(ZYCO, id=id)
        data = {
            'id': contrat.id,
            'type_contrat': contrat.type_contrat,
            'date_debut': contrat.date_debut.strftime('%Y-%m-%d') if contrat.date_debut else '',
            'date_fin': contrat.date_fin.strftime('%Y-%m-%d') if contrat.date_fin else '',
            'actif': contrat.actif if hasattr(contrat, 'actif') else True,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_contrat_create_modal(request):
    """Créer un contrat via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        errors = {}
        if not request.POST.get('type_contrat'):
            errors['type_contrat'] = ['Ce champ est requis']
        if not request.POST.get('date_debut'):
            errors['date_debut'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # 1. Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # 2. Validation: un seul contrat actif
        if not date_fin_obj:  # Contrat actif (sans date fin)
            contrats_actifs = ZYCO.objects.filter(
                employe=employe,
                date_fin__isnull=True
            )
            if contrats_actifs.exists():
                contrat_actif = contrats_actifs.first()
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Un contrat actif existe déjà depuis le {contrat_actif.date_debut.strftime('%d/%m/%Y')}. "
                            "Veuillez clôturer le contrat existant avant d'en créer un nouveau."
                        ]
                    }
                }, status=400)

        # 3. Validation: éviter les chevauchements de dates
        contrats_existants = ZYCO.objects.filter(employe=employe)
        for contrat in contrats_existants:
            # Vérifier chevauchement
            chevauchement = (
                    (contrat.date_debut <= date_debut_obj and (
                                contrat.date_fin is None or contrat.date_fin >= date_debut_obj)) or
                    (date_fin_obj and contrat.date_debut <= date_fin_obj and (
                                contrat.date_fin is None or contrat.date_fin >= date_fin_obj)) or
                    (date_debut_obj <= contrat.date_debut and (
                                date_fin_obj is None or date_fin_obj >= contrat.date_debut))
            )

            if chevauchement:
                date_fin_contrat = contrat.date_fin.strftime("%d/%m/%Y") if contrat.date_fin else "En cours"
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Chevauchement détecté avec le contrat du {contrat.date_debut.strftime('%d/%m/%Y')} au {date_fin_contrat}. "
                            "Ajustez les dates pour éviter les chevauchements."
                        ]
                    }
                }, status=400)

        with transaction.atomic():
            contrat = ZYCO.objects.create(
                employe=employe,
                type_contrat=request.POST.get('type_contrat'),
                date_debut=date_debut_obj,
                date_fin=date_fin_obj,
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Contrat créé avec succès',
            'id': contrat.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_contrat_update_modal(request, id):
    """Mettre à jour un contrat via modal"""
    try:
        contrat = get_object_or_404(ZYCO, id=id)

        errors = {}
        if not request.POST.get('type_contrat'):
            errors['type_contrat'] = ['Ce champ est requis']
        if not request.POST.get('date_debut'):
            errors['date_debut'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # 1. Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # 2. Validation: un seul contrat actif
        if not date_fin_obj:  # Devient actif
            contrats_actifs = ZYCO.objects.filter(
                employe=contrat.employe,
                date_fin__isnull=True
            ).exclude(id=id)
            if contrats_actifs.exists():
                contrat_actif = contrats_actifs.first()
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Un autre contrat actif existe depuis le {contrat_actif.date_debut.strftime('%d/%m/%Y')}. "
                            "Un seul contrat peut être actif à la fois."
                        ]
                    }
                }, status=400)

        # 3. Validation: éviter les chevauchements de dates
        contrats_existants = ZYCO.objects.filter(employe=contrat.employe).exclude(id=id)
        for contrat_existant in contrats_existants:
            chevauchement = (
                    (contrat_existant.date_debut <= date_debut_obj and (
                                contrat_existant.date_fin is None or contrat_existant.date_fin >= date_debut_obj)) or
                    (date_fin_obj and contrat_existant.date_debut <= date_fin_obj and (
                                contrat_existant.date_fin is None or contrat_existant.date_fin >= date_fin_obj)) or
                    (date_debut_obj <= contrat_existant.date_debut and (
                                date_fin_obj is None or date_fin_obj >= contrat_existant.date_debut))
            )

            if chevauchement:
                date_fin_contrat = contrat_existant.date_fin.strftime(
                    "%d/%m/%Y") if contrat_existant.date_fin else "En cours"
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Chevauchement détecté avec le contrat du {contrat_existant.date_debut.strftime('%d/%m/%Y')} au {date_fin_contrat}. "
                            "Ajustez les dates pour éviter les chevauchements."
                        ]
                    }
                }, status=400)

        with transaction.atomic():
            contrat.type_contrat = request.POST.get('type_contrat')
            contrat.date_debut = date_debut_obj
            contrat.date_fin = date_fin_obj
            contrat.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Contrat modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_contrat_delete_modal(request, id):
    """Supprimer un contrat via modal"""
    try:
        contrat = get_object_or_404(ZYCO, id=id)
        with transaction.atomic():
            contrat.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Contrat supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API AFFECTATIONS (pour modales) =====

@require_http_methods(["GET"])
@login_required
def api_affectation_detail(request, id):
    """Récupérer les détails d'une affectation"""
    try:
        affectation = get_object_or_404(ZYAF, id=id)
        data = {
            'id': affectation.id,
            'poste': {
                'id': affectation.poste.id,
                'LIBELLE': affectation.poste.LIBELLE,
                'departement_id': affectation.poste.DEPARTEMENT.id,
            },
            'date_debut': affectation.date_debut.strftime('%Y-%m-%d') if affectation.date_debut else '',
            'date_fin': affectation.date_fin.strftime('%Y-%m-%d') if affectation.date_fin else '',
            'actif': affectation.actif if hasattr(affectation, 'actif') else True,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_affectation_create_modal(request):
    """Créer une affectation via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        errors = {}
        if not request.POST.get('poste'):
            errors['poste'] = ['Ce champ est requis']
        if not request.POST.get('date_debut'):
            errors['date_debut'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        poste = get_object_or_404(ZDPO, id=request.POST.get('poste'))
        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # 1. Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # 2. Validation: une seule affectation active
        if not date_fin_obj:  # Affectation active (sans date fin)
            affectations_actives = ZYAF.objects.filter(
                employe=employe,
                date_fin__isnull=True
            )
            if affectations_actives.exists():
                affectation_active = affectations_actives.first()
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Une affectation active existe déjà depuis le {affectation_active.date_debut.strftime('%d/%m/%Y')}. "
                            "Veuillez clôturer l'affectation existante avant d'en créer une nouvelle."
                        ]
                    }
                }, status=400)

        # 3. Validation: éviter les chevauchements de dates
        affectations_existantes = ZYAF.objects.filter(employe=employe)
        for affectation in affectations_existantes:
            chevauchement = (
                    (affectation.date_debut <= date_debut_obj and (
                                affectation.date_fin is None or affectation.date_fin >= date_debut_obj)) or
                    (date_fin_obj and affectation.date_debut <= date_fin_obj and (
                                affectation.date_fin is None or affectation.date_fin >= date_fin_obj)) or
                    (date_debut_obj <= affectation.date_debut and (
                                date_fin_obj is None or date_fin_obj >= affectation.date_debut))
            )

            if chevauchement:
                date_fin_affectation = affectation.date_fin.strftime("%d/%m/%Y") if affectation.date_fin else "En cours"
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Chevauchement détecté avec l'affectation du {affectation.date_debut.strftime('%d/%m/%Y')} au {date_fin_affectation}. "
                            "Ajustez les dates pour éviter les chevauchements."
                        ]
                    }
                }, status=400)

        with transaction.atomic():
            affectation = ZYAF.objects.create(
                employe=employe,
                poste=poste,
                date_debut=date_debut_obj,
                date_fin=date_fin_obj,
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Affectation créée avec succès',
            'id': affectation.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_affectation_update_modal(request, id):
    """Mettre à jour une affectation via modal"""
    try:
        affectation = get_object_or_404(ZYAF, id=id)

        errors = {}
        if not request.POST.get('poste'):
            errors['poste'] = ['Ce champ est requis']
        if not request.POST.get('date_debut'):
            errors['date_debut'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        poste = get_object_or_404(ZDPO, id=request.POST.get('poste'))
        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # 1. Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # 2. Validation: une seule affectation active
        if not date_fin_obj:  # Devient active
            affectations_actives = ZYAF.objects.filter(
                employe=affectation.employe,
                date_fin__isnull=True
            ).exclude(id=id)
            if affectations_actives.exists():
                affectation_active = affectations_actives.first()
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Une autre affectation active existe depuis le {affectation_active.date_debut.strftime('%d/%m/%Y')}. "
                            "Une seule affectation peut être active à la fois."
                        ]
                    }
                }, status=400)

        # 3. Validation: éviter les chevauchements de dates
        affectations_existantes = ZYAF.objects.filter(employe=affectation.employe).exclude(id=id)
        for affectation_existante in affectations_existantes:
            chevauchement = (
                    (affectation_existante.date_debut <= date_debut_obj and (
                                affectation_existante.date_fin is None or affectation_existante.date_fin >= date_debut_obj)) or
                    (date_fin_obj and affectation_existante.date_debut <= date_fin_obj and (
                                affectation_existante.date_fin is None or affectation_existante.date_fin >= date_fin_obj)) or
                    (date_debut_obj <= affectation_existante.date_debut and (
                                date_fin_obj is None or date_fin_obj >= affectation_existante.date_debut))
            )

            if chevauchement:
                date_fin_affectation = affectation_existante.date_fin.strftime(
                    "%d/%m/%Y") if affectation_existante.date_fin else "En cours"
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Chevauchement détecté avec l'affectation du {affectation_existante.date_debut.strftime('%d/%m/%Y')} au {date_fin_affectation}. "
                            "Ajustez les dates pour éviter les chevauchements."
                        ]
                    }
                }, status=400)

        with transaction.atomic():
            affectation.poste = poste
            affectation.date_debut = date_debut_obj
            affectation.date_fin = date_fin_obj
            affectation.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Affectation modifiée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_affectation_delete_modal(request, id):
    """Supprimer une affectation via modal"""
    try:
        affectation = get_object_or_404(ZYAF, id=id)
        with transaction.atomic():
            affectation.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Affectation supprimée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API HELPER =====

@require_http_methods(["GET"])
@login_required
def api_postes_by_departement(request):
    """Récupérer la liste des postes d'un département"""
    try:
        departement_id = request.GET.get('departement')
        if not departement_id:
            return JsonResponse({'error': 'Le paramètre departement est requis'}, status=400)

        postes = ZDPO.objects.filter(DEPARTEMENT_id=departement_id, STATUT=True).order_by('LIBELLE')

        data = [
            {
                'id': poste.id,
                'LIBELLE': poste.LIBELLE,
            }
            for poste in postes
        ]

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
@login_required
def modifier_photo_ajax(request):
    """Vue AJAX pour modifier la photo de profil d'un employé"""
    try:
        print("=" * 50)
        print("📸 DÉBUT modifier_photo_ajax")

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

        # ✅ CORRECTION CRITIQUE : Ajouter timestamp à l'URL
        import time
        timestamp = int(time.time())
        photo_url_with_timestamp = f"{employe.photo.url}?t={timestamp}"

        print(f"✅ URL photo avec timestamp: {photo_url_with_timestamp}")

        return JsonResponse({
            'success': True,
            'photo_url': photo_url_with_timestamp,  # ← AVEC TIMESTAMP
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        print(f"💥 ERREUR: {str(e)}")
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
            'photo_url': employe.get_photo_url(),
            **get_active_tab_for_ajax(request)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



# ===== API FAMILLE (ZYFA) =====

@require_http_methods(["GET"])
@login_required
def api_famille_detail(request, id):
    """Récupérer les détails d'une personne à charge"""
    try:
        famille = get_object_or_404(ZYFA, id=id)
        data = {
            'id': famille.id,
            'personne_charge': famille.personne_charge,
            'nom': famille.nom,
            'prenom': famille.prenom,
            'sexe': famille.sexe,
            'date_naissance': famille.date_naissance.strftime('%Y-%m-%d') if famille.date_naissance else '',
            'date_debut_prise_charge': famille.date_debut_prise_charge.strftime('%Y-%m-%d') if famille.date_debut_prise_charge else '',
            'date_fin_prise_charge': famille.date_fin_prise_charge.strftime('%Y-%m-%d') if famille.date_fin_prise_charge else '',
            'actif': famille.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_famille_create_modal(request):
    """Créer une personne à charge via modal"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Validation
        errors = {}
        required_fields = ['personne_charge', 'nom', 'prenom', 'sexe', 'date_naissance', 'date_debut_prise_charge']
        for field in required_fields:
            if not request.POST.get(field):
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        personne_charge = request.POST.get('personne_charge')
        date_naissance_obj = datetime.strptime(request.POST.get('date_naissance'), '%Y-%m-%d').date()
        date_debut_obj = datetime.strptime(request.POST.get('date_debut_prise_charge'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_prise_charge')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Validations
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_prise_charge'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        if date_naissance_obj > timezone.now().date():
            errors['date_naissance'] = ['La date de naissance doit être dans le passé']
            return JsonResponse({'errors': errors}, status=400)

        # Créer la personne à charge
        with transaction.atomic():
            famille = ZYFA.objects.create(
                employe=employe,
                personne_charge=personne_charge,
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                sexe=request.POST.get('sexe'),
                date_naissance=date_naissance_obj,
                date_debut_prise_charge=date_debut_obj,
                date_fin_prise_charge=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Personne à charge ajoutée avec succès',
            'id': famille.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_famille_update_modal(request, id):
    """Mettre à jour une personne à charge via modal"""
    try:
        famille = get_object_or_404(ZYFA, id=id)

        # Validation
        errors = {}
        required_fields = ['personne_charge', 'nom', 'prenom', 'sexe', 'date_naissance', 'date_debut_prise_charge']
        for field in required_fields:
            if not request.POST.get(field):
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        personne_charge = request.POST.get('personne_charge')
        date_naissance_obj = datetime.strptime(request.POST.get('date_naissance'), '%Y-%m-%d').date()
        date_debut_obj = datetime.strptime(request.POST.get('date_debut_prise_charge'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_prise_charge')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Validations
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_prise_charge'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        if date_naissance_obj > timezone.now().date():
            errors['date_naissance'] = ['La date de naissance doit être dans le passé']
            return JsonResponse({'errors': errors}, status=400)

        # Mettre à jour
        with transaction.atomic():
            famille.personne_charge = personne_charge
            famille.nom = request.POST.get('nom')
            famille.prenom = request.POST.get('prenom')
            famille.sexe = request.POST.get('sexe')
            famille.date_naissance = date_naissance_obj
            famille.date_debut_prise_charge = date_debut_obj
            famille.date_fin_prise_charge = date_fin_obj
            famille.actif = request.POST.get('actif') == 'on'
            famille.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Personne à charge modifiée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_famille_delete_modal(request, id):
    """Supprimer une personne à charge via modal"""
    try:
        famille = get_object_or_404(ZYFA, id=id)
        with transaction.atomic():
            famille.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Personne à charge supprimée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ===== API HISTORIQUE NOMS/PRENOMS (ZYNP) =====

@require_http_methods(["GET"])
@login_required
def api_znp_detail(request, id):
    """Récupérer les détails d'un historique nom/prénom"""
    try:
        znp = get_object_or_404(ZYNP, id=id)
        data = {
            'id': znp.id,
            'nom': znp.nom,
            'prenoms': znp.prenoms,
            'date_debut_validite': znp.date_debut_validite.strftime('%Y-%m-%d') if znp.date_debut_validite else '',
            'date_fin_validite': znp.date_fin_validite.strftime('%Y-%m-%d') if znp.date_fin_validite else '',
            'actif': znp.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_znp_create_modal(request):
    """Créer un historique nom/prénom via modal avec validation des chevauchements"""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Validation de base
        errors = {}
        required_fields = ['nom', 'prenoms', 'date_debut_validite']
        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        nom = request.POST.get('nom')
        prenoms = request.POST.get('prenoms')
        date_debut = request.POST.get('date_debut_validite')
        date_fin = request.POST.get('date_fin_validite')

        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        except Exception:
            errors['date_debut_validite'] = ['Format de date invalide']

        date_fin_obj = None
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            except Exception:
                errors['date_fin_validite'] = ['Format de date invalide']

        # Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Validation des chevauchements de dates
        historiques_existants = ZYNP.objects.filter(employe=employe)

        for historique in historiques_existants:
            # Cas 1: L'historique existant n'a pas de date de fin (est actif)
            if not historique.date_fin_validite:
                if not date_fin_obj or date_fin_obj >= historique.date_debut_validite:
                    erreur_msg = (
                        f"Impossible de créer un nouvel historique. L'historique actuel (du {historique.date_debut_validite.strftime('%d/%m/%Y')} à aujourd'hui) "
                        f"n'est pas clôturé. Veuillez d'abord ajouter une date de fin à l'historique actuel."
                    )
                    return JsonResponse({
                        'errors': {
                            '__all__': [erreur_msg]
                        }
                    }, status=400)

            # Cas 2: Vérifier les chevauchements entre périodes
            chevauchement = (
                # Nouvelle période commence pendant une période existante
                (date_debut_obj >= historique.date_debut_validite and
                 (historique.date_fin_validite is None or date_debut_obj <= historique.date_fin_validite)) or

                # Nouvelle période se termine pendant une période existante
                (date_fin_obj and
                 date_fin_obj >= historique.date_debut_validite and
                 (historique.date_fin_validite is None or date_fin_obj <= historique.date_fin_validite)) or

                # Nouvelle période englobe une période existante
                (date_debut_obj <= historique.date_debut_validite and
                 (date_fin_obj is None or date_fin_obj >= historique.date_debut_validite))
            )

            if chevauchement:
                date_fin_existant = historique.date_fin_validite.strftime(
                    "%d/%m/%Y") if historique.date_fin_validite else "aujourd'hui"
                erreur_msg = (
                    f"Chevauchement détecté avec l'historique existant du {historique.date_debut_validite.strftime('%d/%m/%Y')} "
                    f"au {date_fin_existant}. Ajustez les dates pour éviter les chevauchements."
                )
                return JsonResponse({
                    'errors': {
                        '__all__': [erreur_msg]
                    }
                }, status=400)

        # Créer l'historique avec validation
        with transaction.atomic():
            znp = ZYNP(
                employe=employe,
                nom=nom,
                prenoms=prenoms,
                date_debut_validite=date_debut_obj,
                date_fin_validite=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

            # Valider le modèle
            try:
                znp.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            znp.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Historique nom/prénom créé avec succès',
            'id': znp.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_znp_update_modal(request, id):
    """Mettre à jour un historique nom/prénom via modal avec validation des chevauchements"""
    try:
        znp = get_object_or_404(ZYNP, id=id)

        # Validation
        errors = {}
        if not request.POST.get('nom'):
            errors['nom'] = ['Ce champ est requis']
        if not request.POST.get('prenoms'):
            errors['prenoms'] = ['Ce champ est requis']
        if not request.POST.get('date_debut_validite'):
            errors['date_debut_validite'] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        date_debut_obj = datetime.strptime(request.POST.get('date_debut_validite'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin_validite')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # 🆕 VALIDATION AVANCÉE: Vérifier les chevauchements de dates (en excluant l'instance courante)
        historiques_existants = ZYNP.objects.filter(employe=znp.employe).exclude(id=id)

        for historique in historiques_existants:
            chevauchement = (
                # Nouvelle période commence pendant une période existante
                    (date_debut_obj >= historique.date_debut_validite and
                     (historique.date_fin_validite is None or date_debut_obj <= historique.date_fin_validite)) or

                    # Nouvelle période se termine pendant une période existante
                    (date_fin_obj and
                     date_fin_obj >= historique.date_debut_validite and
                     (historique.date_fin_validite is None or date_fin_obj <= historique.date_fin_validite)) or

                    # Nouvelle période englobe une période existante
                    (date_debut_obj <= historique.date_debut_validite and
                     (date_fin_obj is None or date_fin_obj >= historique.date_debut_validite))
            )

            if chevauchement:
                date_fin_existant = historique.date_fin_validite.strftime(
                    "%d/%m/%Y") if historique.date_fin_validite else "aujourd'hui"
                return JsonResponse({
                    'errors': {
                        '__all__': [
                            f"Chevauchement détecté avec l'historique existant du {historique.date_debut_validite.strftime('%d/%m/%Y')} "
                            f"au {date_fin_existant}. Ajustez les dates pour éviter les chevauchements."
                        ]
                    }
                }, status=400)

        # Mettre à jour l'historique
        with transaction.atomic():
            znp.nom = request.POST.get('nom')
            znp.prenoms = request.POST.get('prenoms')
            znp.date_debut_validite = date_debut_obj
            znp.date_fin_validite = date_fin_obj
            znp.actif = request.POST.get('actif') == 'on'
            znp.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Historique nom/prénom modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_znp_delete_modal(request, id):
    """Supprimer un historique nom/prénom via modal"""
    try:
        znp = get_object_or_404(ZYNP, id=id)
        with transaction.atomic():
            znp.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Historique nom/prénom supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_historique_actif(employe):
    """Récupérer l'historique nom/prénom actif (sans date de fin)"""
    return ZYNP.objects.filter(
        employe=employe,
        date_fin_validite__isnull=True
    ).first()

@login_required
def peut_creer_nouvel_historique(employe, nouvelle_date_debut):
    """Vérifier si on peut créer un nouvel historique"""
    historique_actif = get_historique_actif(employe)

    if historique_actif:
        # Il y a un historique actif non clôturé
        return False, f"L'historique actuel (du {historique_actif.date_debut_validite.strftime('%d/%m/%Y')}) n'est pas clôturé. Ajoutez une date de fin avant de créer un nouvel historique."

    # Vérifier les chevauchements avec les historiques clôturés
    historiques = ZYNP.objects.filter(employe=employe)

    for historique in historiques:
        if (nouvelle_date_debut >= historique.date_debut_validite and
                (historique.date_fin_validite is None or nouvelle_date_debut <= historique.date_fin_validite)):
            return False, f"La nouvelle date chevauche avec l'historique du {historique.date_debut_validite.strftime('%d/%m/%Y')} au {historique.date_fin_validite.strftime('%d/%m/%Y') if historique.date_fin_validite else 'présent'}"

    return True, None


# ===== API PERSONNES À PRÉVENIR (ZYPP) =====

@require_http_methods(["GET"])
@login_required
def api_personne_prevenir_detail(request, id):
    """Récupérer les détails d'une personne à prévenir"""
    try:
        personne = get_object_or_404(ZYPP, id=id)
        data = {
            'id': personne.id,
            'nom': personne.nom,
            'prenom': personne.prenom,
            'lien_parente': personne.lien_parente,
            'telephone_principal': personne.telephone_principal,
            'telephone_secondaire': personne.telephone_secondaire or '',
            'email': personne.email or '',
            'adresse': personne.adresse or '',
            'ordre_priorite': personne.ordre_priorite,
            'remarques': personne.remarques or '',
            'date_debut_validite': personne.date_debut_validite.strftime(
                '%Y-%m-%d') if personne.date_debut_validite else '',
            'date_fin_validite': personne.date_fin_validite.strftime('%Y-%m-%d') if personne.date_fin_validite else '',
            'actif': personne.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_personne_prevenir_create_modal(request):
    """Créer une personne à prévenir via modal"""
    try:
        print("=" * 50)
        print("📝 DÉBUT api_personne_prevenir_create_modal")
        print("=" * 50)

        # Log toutes les données POST reçues
        print("📦 DONNÉES POST REÇUES:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")

        employe_uuid = request.POST.get('employe_uuid')
        print(f"🔍 Employe UUID: {employe_uuid}")

        employe = get_object_or_404(ZY00, uuid=employe_uuid)
        print(f"✅ Employé trouvé: {employe.matricule}")

        # Validation de base
        errors = {}
        required_fields = ['nom', 'prenom', 'lien_parente', 'telephone_principal', 'ordre_priorite',
                           'date_debut_validite']
        for field in required_fields:
            value = request.POST.get(field)
            print(f"🔍 Validation {field}: '{value}'")
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            print(f"❌ ERREURS DE VALIDATION: {errors}")
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        lien_parente = request.POST.get('lien_parente')
        telephone_principal = request.POST.get('telephone_principal')
        telephone_secondaire = request.POST.get('telephone_secondaire', '')
        email = request.POST.get('email', '')
        adresse = request.POST.get('adresse', '')
        ordre_priorite = request.POST.get('ordre_priorite')
        remarques = request.POST.get('remarques', '')
        date_debut = request.POST.get('date_debut_validite')
        date_fin = request.POST.get('date_fin_validite')

        print(f"📦 Ordre priorité: {ordre_priorite}")
        print(f"📦 Date début: {date_debut}")
        print(f"📦 Date fin: {date_fin}")

        # Conversion des dates
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            print(f"✅ Date début convertie: {date_debut_obj}")
        except Exception as e:
            errors['date_debut_validite'] = ['Format de date invalide']
            print(f"❌ Erreur conversion date_debut: {e}")

        date_fin_obj = None
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                print(f"✅ Date fin convertie: {date_fin_obj}")
            except Exception as e:
                errors['date_fin_validite'] = ['Format de date invalide']
                print(f"❌ Erreur conversion date_fin: {e}")

        # Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']
            print("❌ Erreur: date_fin <= date_debut")

        # Validation: les deux téléphones ne doivent pas être identiques
        if telephone_secondaire and telephone_principal == telephone_secondaire:
            errors['telephone_secondaire'] = ['Le téléphone secondaire doit être différent du téléphone principal']
            print("❌ Erreur: téléphones identiques")

        # Validation: vérifier le format du téléphone principal
        telephone_nettoye = ''.join(filter(str.isdigit, telephone_principal.replace('+', '')))
        if len(telephone_nettoye) < 8:
            errors['telephone_principal'] = ['Le numéro de téléphone doit contenir au moins 8 chiffres']
            print("❌ Erreur: téléphone trop court")

        # Validation: vérifier le format du téléphone secondaire si fourni
        if telephone_secondaire:
            telephone_sec_nettoye = ''.join(filter(str.isdigit, telephone_secondaire.replace('+', '')))
            if len(telephone_sec_nettoye) < 8:
                errors['telephone_secondaire'] = ['Le numéro de téléphone doit contenir au moins 8 chiffres']
                print("❌ Erreur: téléphone secondaire trop court")

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Validation: pas de doublon de priorité actif pour le même employé
        if not date_fin_obj:  # Contact actif
            contacts_meme_priorite = ZYPP.objects.filter(
                employe=employe,
                ordre_priorite=ordre_priorite,
                date_fin_validite__isnull=True
            )

            if contacts_meme_priorite.exists():
                contact_existant = contacts_meme_priorite.first()
                priorite_label = dict(ZYPP.ORDRE_PRIORITE_CHOICES).get(int(ordre_priorite), ordre_priorite)
                erreur_msg = (
                    f"Un contact avec la priorité '{priorite_label}' existe déjà "
                    f"({contact_existant.prenom} {contact_existant.nom}). "
                    f"Veuillez d'abord clôturer ce contact ou choisir une autre priorité."
                )
                return JsonResponse({
                    'errors': {
                        'ordre_priorite': [erreur_msg]
                    }
                }, status=400)

        # Validation des chevauchements de dates pour la même priorité
        contacts_existants = ZYPP.objects.filter(
            employe=employe,
            ordre_priorite=ordre_priorite
        )

        for contact in contacts_existants:
            chevauchement = (
                # Nouvelle période commence pendant une période existante
                    (date_debut_obj >= contact.date_debut_validite and
                     (contact.date_fin_validite is None or date_debut_obj <= contact.date_fin_validite)) or

                    # Nouvelle période se termine pendant une période existante
                    (date_fin_obj and
                     date_fin_obj >= contact.date_debut_validite and
                     (contact.date_fin_validite is None or date_fin_obj <= contact.date_fin_validite)) or

                    # Nouvelle période englobe une période existante
                    (date_debut_obj <= contact.date_debut_validite and
                     (date_fin_obj is None or date_fin_obj >= contact.date_debut_validite))
            )

            if chevauchement:
                priorite_label = dict(ZYPP.ORDRE_PRIORITE_CHOICES).get(int(ordre_priorite), ordre_priorite)
                date_fin_contact = contact.date_fin_validite.strftime(
                    "%d/%m/%Y") if contact.date_fin_validite else "aujourd'hui"
                erreur_msg = (
                    f"Chevauchement de dates détecté pour la priorité '{priorite_label}' "
                    f"avec le contact existant du {contact.date_debut_validite.strftime('%d/%m/%Y')} "
                    f"au {date_fin_contact}. Ajustez les dates pour éviter les chevauchements."
                )
                return JsonResponse({
                    'errors': {
                        '__all__': [erreur_msg]
                    }
                }, status=400)

        # Créer la personne à prévenir avec validation
        print("💾 TENTATIVE CRÉATION PERSONNE À PRÉVENIR...")
        with transaction.atomic():
            personne = ZYPP(
                employe=employe,
                nom=nom,
                prenom=prenom,
                lien_parente=lien_parente,
                telephone_principal=telephone_principal,
                telephone_secondaire=telephone_secondaire if telephone_secondaire else None,
                email=email if email else None,
                adresse=adresse if adresse else None,
                ordre_priorite=ordre_priorite,
                remarques=remarques if remarques else None,
                date_debut_validite=date_debut_obj,
                date_fin_validite=date_fin_obj,
                actif=request.POST.get('actif') == 'on',
            )

            # Valider le modèle
            try:
                print("🔍 Validation full_clean()...")
                personne.full_clean()
                print("✅ Validation full_clean() réussie")
            except ValidationError as e:
                print(f"❌ ERREUR ValidationError: {e.message_dict}")
                return JsonResponse({'errors': e.message_dict}, status=400)

            personne.save()
            print(f"✅ PERSONNE À PRÉVENIR CRÉÉE AVEC SUCCÈS - ID: {personne.id}")

        return JsonResponse({
            'success': True,
            'message': '✅ Personne à prévenir créée avec succès',
            'id': personne.id
        })

    except Exception as e:
        print(f"💥 ERREUR NON GÉRÉE: {str(e)}")
        import traceback
        print(f"🔍 TRACEBACK COMPLET:")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_personne_prevenir_update_modal(request, id):
    """Mettre à jour une personne à prévenir via modal"""
    try:
        print("=" * 50)
        print(f"📝 DÉBUT api_personne_prevenir_update_modal - ID: {id}")
        print("=" * 50)

        personne = get_object_or_404(ZYPP, id=id)
        print(f"✅ Personne trouvée: {personne.prenom} {personne.nom}")

        # Validation de base
        errors = {}
        required_fields = ['nom', 'prenom', 'lien_parente', 'telephone_principal', 'ordre_priorite',
                           'date_debut_validite']
        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            print(f"❌ ERREURS DE VALIDATION: {errors}")
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        lien_parente = request.POST.get('lien_parente')
        telephone_principal = request.POST.get('telephone_principal')
        telephone_secondaire = request.POST.get('telephone_secondaire', '')
        email = request.POST.get('email', '')
        adresse = request.POST.get('adresse', '')
        ordre_priorite = request.POST.get('ordre_priorite')
        remarques = request.POST.get('remarques', '')
        date_debut = request.POST.get('date_debut_validite')
        date_fin = request.POST.get('date_fin_validite')

        # Conversion des dates
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        except Exception:
            errors['date_debut_validite'] = ['Format de date invalide']

        date_fin_obj = None
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            except Exception:
                errors['date_fin_validite'] = ['Format de date invalide']

        # Validation: date fin > date début
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin_validite'] = ['La date de fin doit être supérieure à la date de début']

        # Validation: les deux téléphones ne doivent pas être identiques
        if telephone_secondaire and telephone_principal == telephone_secondaire:
            errors['telephone_secondaire'] = ['Le téléphone secondaire doit être différent du téléphone principal']

        # Validation: vérifier le format du téléphone principal
        telephone_nettoye = ''.join(filter(str.isdigit, telephone_principal.replace('+', '')))
        if len(telephone_nettoye) < 8:
            errors['telephone_principal'] = ['Le numéro de téléphone doit contenir au moins 8 chiffres']

        # Validation: vérifier le format du téléphone secondaire si fourni
        if telephone_secondaire:
            telephone_sec_nettoye = ''.join(filter(str.isdigit, telephone_secondaire.replace('+', '')))
            if len(telephone_sec_nettoye) < 8:
                errors['telephone_secondaire'] = ['Le numéro de téléphone doit contenir au moins 8 chiffres']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Validation: pas de doublon de priorité actif (en excluant l'instance courante)
        if not date_fin_obj:  # Contact actif
            contacts_meme_priorite = ZYPP.objects.filter(
                employe=personne.employe,
                ordre_priorite=ordre_priorite,
                date_fin_validite__isnull=True
            ).exclude(id=id)

            if contacts_meme_priorite.exists():
                contact_existant = contacts_meme_priorite.first()
                priorite_label = dict(ZYPP.ORDRE_PRIORITE_CHOICES).get(int(ordre_priorite), ordre_priorite)
                erreur_msg = (
                    f"Un autre contact avec la priorité '{priorite_label}' existe déjà "
                    f"({contact_existant.prenom} {contact_existant.nom}). "
                    f"Une seule personne peut avoir cette priorité à la fois."
                )
                return JsonResponse({
                    'errors': {
                        'ordre_priorite': [erreur_msg]
                    }
                }, status=400)

        # Validation des chevauchements de dates (en excluant l'instance courante)
        contacts_existants = ZYPP.objects.filter(
            employe=personne.employe,
            ordre_priorite=ordre_priorite
        ).exclude(id=id)

        for contact in contacts_existants:
            chevauchement = (
                    (date_debut_obj >= contact.date_debut_validite and
                     (contact.date_fin_validite is None or date_debut_obj <= contact.date_fin_validite)) or

                    (date_fin_obj and
                     date_fin_obj >= contact.date_debut_validite and
                     (contact.date_fin_validite is None or date_fin_obj <= contact.date_fin_validite)) or

                    (date_debut_obj <= contact.date_debut_validite and
                     (date_fin_obj is None or date_fin_obj >= contact.date_debut_validite))
            )

            if chevauchement:
                priorite_label = dict(ZYPP.ORDRE_PRIORITE_CHOICES).get(int(ordre_priorite), ordre_priorite)
                date_fin_contact = contact.date_fin_validite.strftime(
                    "%d/%m/%Y") if contact.date_fin_validite else "aujourd'hui"
                erreur_msg = (
                    f"Chevauchement de dates détecté pour la priorité '{priorite_label}' "
                    f"avec le contact existant du {contact.date_debut_validite.strftime('%d/%m/%Y')} "
                    f"au {date_fin_contact}."
                )
                return JsonResponse({
                    'errors': {
                        '__all__': [erreur_msg]
                    }
                }, status=400)

        # Mettre à jour la personne à prévenir
        print("💾 TENTATIVE MISE À JOUR...")
        with transaction.atomic():
            personne.nom = nom
            personne.prenom = prenom
            personne.lien_parente = lien_parente
            personne.telephone_principal = telephone_principal
            personne.telephone_secondaire = telephone_secondaire if telephone_secondaire else None
            personne.email = email if email else None
            personne.adresse = adresse if adresse else None
            personne.ordre_priorite = ordre_priorite
            personne.remarques = remarques if remarques else None
            personne.date_debut_validite = date_debut_obj
            personne.date_fin_validite = date_fin_obj
            personne.actif = request.POST.get('actif') == 'on'

            # Valider le modèle
            try:
                personne.full_clean()
            except ValidationError as e:
                print(f"❌ ERREUR ValidationError: {e.message_dict}")
                return JsonResponse({'errors': e.message_dict}, status=400)

            personne.save()
            print(f"✅ PERSONNE À PRÉVENIR MODIFIÉE AVEC SUCCÈS")

        return JsonResponse({
            'success': True,
            'message': '✅ Personne à prévenir modifiée avec succès'
        })

    except Exception as e:
        print(f"💥 ERREUR NON GÉRÉE: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_personne_prevenir_delete_modal(request, id):
    """Supprimer une personne à prévenir via modal"""
    try:
        print(f"🗑️ Suppression de la personne à prévenir ID: {id}")
        personne = get_object_or_404(ZYPP, id=id)
        nom_complet = f"{personne.prenom} {personne.nom}"

        with transaction.atomic():
            personne.delete()

        print(f"✅ Personne à prévenir supprimée: {nom_complet}")

        return JsonResponse({
            'success': True,
            'message': f'✅ Personne à prévenir ({nom_complet}) supprimée avec succès'
        })
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


# ===== API IDENTITÉ BANCAIRE (ZYIB) =====
@require_http_methods(["GET"])
@login_required
def api_identite_bancaire_detail(request, employe_uuid):
    """Récupérer les détails de l'identité bancaire d'un employé"""
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        try:
            ib = employe.identite_bancaire
            data = {
                'id': ib.id,
                'titulaire_compte': ib.titulaire_compte,
                'nom_banque': ib.nom_banque,
                'code_banque': ib.code_banque,
                'code_guichet': ib.code_guichet,
                'numero_compte': ib.numero_compte,
                'cle_rib': ib.cle_rib,
                'iban': ib.iban or '',
                'bic': ib.bic or '',
                'type_compte': ib.type_compte,
                'domiciliation': ib.domiciliation or '',
                'date_ouverture': ib.date_ouverture.strftime('%Y-%m-%d') if ib.date_ouverture else '',
                'remarques': ib.remarques or '',
                'actif': ib.actif,
                'rib_complet': ib.get_rib(),
                'iban_formate': ib.get_iban_formate(),
            }
            return JsonResponse(data)
        except ZYIB.DoesNotExist:
            return JsonResponse({'error': 'Aucune identité bancaire enregistrée'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_identite_bancaire_create_or_update(request, employe_uuid):
    """Créer ou mettre à jour l'identité bancaire d'un employé"""
    try:
        print("=" * 50)
        print("📝 DÉBUT api_identite_bancaire_create_or_update")
        print("=" * 50)

        employe = get_object_or_404(ZY00, uuid=employe_uuid)
        print(f"✅ Employé trouvé: {employe.matricule}")

        # Validation de base
        errors = {}
        required_fields = ['titulaire_compte', 'nom_banque', 'code_banque', 'code_guichet',
                           'numero_compte', 'cle_rib']

        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
            print(f"❌ ERREURS DE VALIDATION: {errors}")
            return JsonResponse({'errors': errors}, status=400)

        # Récupération des données
        data = {
            'titulaire_compte': request.POST.get('titulaire_compte'),
            'nom_banque': request.POST.get('nom_banque'),
            'code_banque': request.POST.get('code_banque'),
            'code_guichet': request.POST.get('code_guichet'),
            'numero_compte': request.POST.get('numero_compte'),
            'cle_rib': request.POST.get('cle_rib'),
            'iban': request.POST.get('iban', ''),
            'bic': request.POST.get('bic', ''),
            'type_compte': request.POST.get('type_compte', 'COURANT'),
            'domiciliation': request.POST.get('domiciliation', ''),
            'remarques': request.POST.get('remarques', ''),
            'actif': request.POST.get('actif') == 'on',
        }

        # Date d'ouverture
        date_ouverture = request.POST.get('date_ouverture')
        if date_ouverture:
            try:
                data['date_ouverture'] = datetime.strptime(date_ouverture, '%Y-%m-%d').date()
            except ValueError:
                errors['date_ouverture'] = ['Format de date invalide']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Créer ou mettre à jour
        with transaction.atomic():
            ib, created = ZYIB.objects.update_or_create(
                employe=employe,
                defaults=data
            )

            # Valider le modèle
            try:
                ib.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            ib.save()
            print(f"✅ IDENTITÉ BANCAIRE {'CRÉÉE' if created else 'MODIFIÉE'} AVEC SUCCÈS - ID: {ib.id}")

        return JsonResponse({
            'success': True,
            'message': f'✅ Identité bancaire {"créée" if created else "modifiée"} avec succès',
            'id': ib.id
        })

    except Exception as e:
        print(f"💥 ERREUR NON GÉRÉE: {str(e)}")
        import traceback
        print(f"🔍 TRACEBACK COMPLET:")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_identite_bancaire_delete(request, employe_uuid):
    """Supprimer l'identité bancaire d'un employé"""
    try:
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        try:
            ib = employe.identite_bancaire
            with transaction.atomic():
                ib.delete()

            return JsonResponse({
                'success': True,
                'message': '✅ Identité bancaire supprimée avec succès'
            })
        except ZYIB.DoesNotExist:
            return JsonResponse({'error': 'Aucune identité bancaire à supprimer'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def handler404(request, exception):
    """Vue personnalisée pour les erreurs 404"""
    return render(request, '404.html', status=404)

def handler500(request):
    """Vue personnalisée pour les erreurs 500"""
    return render(request, '500.html', status=500)

def handler403(request, exception):
    """Vue personnalisée pour les erreurs 403"""
    return render(request, '403.html', status=403)

def handler400(request, exception):
    """Vue personnalisée pour les erreurs 400"""
    return render(request, '400.html', status=400)


def profilEmployee(request):
    return render(request, "employee/profil-employee.html")


# Create your views here.
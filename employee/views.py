from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from .models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD
from .forms import (
    ZY00Form, EmbaucheAgentForm, ZYCOForm, ZYTEForm,
    ZYMEForm, ZYAFForm, ZYADForm
)


# ===============================
# VUES POUR L'EMBAUCHE
# ===============================

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

    return redirect('detail_employe', uuid=uuid)


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
        # Rediriger vers le détail du dossier individuel
        return reverse_lazy('dossier_detail', kwargs={'uuid': self.object.uuid})


from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404


class EmployeDeleteView(DeleteView):
    """Supprimer un employé (suppression en cascade)"""
    model = ZY00
    template_name = 'employee/employe_confirm_delete.html'
    success_url = reverse_lazy('liste_dossiers')  # Corriger le nom de l'URL

    # CORRECTION : Utiliser slug_field et slug_url_kwarg pour UUID
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

        # Vérifier si un UUID est passé dans l'URL
        uuid = self.kwargs.get('uuid')
        if uuid:
            employe_selectionne = get_object_or_404(ZY00, uuid=uuid)
            context['employe'] = employe_selectionne
            context['contrats'] = employe_selectionne.contrats.all()
            context['telephones'] = employe_selectionne.telephones.all()
            context['emails'] = employe_selectionne.emails.all()
            context['affectations'] = employe_selectionne.affectations.all()
            context['adresses'] = employe_selectionne.adresses.all()

        return context

    def get(self, request, *args, **kwargs):
        # Cette méthode permet de gérer les deux cas :
        # - Accès à la liste seule
        # - Accès à la liste + détail d'un employé
        return super().get(request, *args, **kwargs)

# ===============================
# VUES POUR LES CONTRATS (ZYCO)
# ===============================

class ContratListView(ListView):
    """Liste de tous les contrats"""
    model = ZYCO
    template_name = 'contrats/liste_contrats.html'
    context_object_name = 'contrats'
    paginate_by = 20


class ContratCreateView(CreateView):
    """Créer un contrat"""
    model = ZYCO
    form_class = ZYCOForm
    template_name = 'contrats/contrat_form.html'
    success_url = reverse_lazy('liste_contrats')

    def form_valid(self, form):
        messages.success(self.request, "Contrat créé avec succès!")
        return super().form_valid(form)


class ContratUpdateView(UpdateView):
    """Modifier un contrat"""
    model = ZYCO
    form_class = ZYCOForm
    template_name = 'contrats/contrat_form.html'
    success_url = reverse_lazy('liste_contrats')

    def form_valid(self, form):
        messages.success(self.request, "Contrat modifié avec succès!")
        return super().form_valid(form)


class ContratDeleteView(DeleteView):
    """Supprimer un contrat"""
    model = ZYCO
    template_name = 'contrats/contrat_confirm_delete.html'
    success_url = reverse_lazy('liste_contrats')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Contrat supprimé avec succès!")
        return super().delete(request, *args, **kwargs)


# ===============================
# VUES POUR LES TÉLÉPHONES (ZYTE)
# ===============================

class TelephoneListView(ListView):
    """Liste de tous les téléphones"""
    model = ZYTE
    template_name = 'telephones/liste_telephones.html'
    context_object_name = 'telephones'
    paginate_by = 20


class TelephoneCreateView(CreateView):
    """Créer un téléphone"""
    model = ZYTE
    form_class = ZYTEForm
    template_name = 'telephones/telephone_form.html'
    success_url = reverse_lazy('liste_telephones')

    def form_valid(self, form):
        messages.success(self.request, "Téléphone créé avec succès!")
        return super().form_valid(form)


class TelephoneUpdateView(UpdateView):
    """Modifier un téléphone"""
    model = ZYTE
    form_class = ZYTEForm
    template_name = 'telephones/telephone_form.html'
    success_url = reverse_lazy('liste_telephones')

    def form_valid(self, form):
        messages.success(self.request, "Téléphone modifié avec succès!")
        return super().form_valid(form)


class TelephoneDeleteView(DeleteView):
    """Supprimer un téléphone"""
    model = ZYTE
    template_name = 'telephones/telephone_confirm_delete.html'
    success_url = reverse_lazy('liste_telephones')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Téléphone supprimé avec succès!")
        return super().delete(request, *args, **kwargs)


# ===============================
# VUES POUR LES EMAILS (ZYME)
# ===============================

class EmailListView(ListView):
    """Liste de tous les emails"""
    model = ZYME
    template_name = 'emails/liste_emails.html'
    context_object_name = 'emails'
    paginate_by = 20


class EmailCreateView(CreateView):
    """Créer un email"""
    model = ZYME
    form_class = ZYMEForm
    template_name = 'emails/email_form.html'
    success_url = reverse_lazy('liste_emails')

    def form_valid(self, form):
        messages.success(self.request, "Email créé avec succès!")
        return super().form_valid(form)


class EmailUpdateView(UpdateView):
    """Modifier un email"""
    model = ZYME
    form_class = ZYMEForm
    template_name = 'emails/email_form.html'
    success_url = reverse_lazy('liste_emails')

    def form_valid(self, form):
        messages.success(self.request, "Email modifié avec succès!")
        return super().form_valid(form)


class EmailDeleteView(DeleteView):
    """Supprimer un email"""
    model = ZYME
    template_name = 'emails/email_confirm_delete.html'
    success_url = reverse_lazy('liste_emails')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Email supprimé avec succès!")
        return super().delete(request, *args, **kwargs)


# ===============================
# VUES POUR LES AFFECTATIONS (ZYAF)
# ===============================

class AffectationListView(ListView):
    """Liste de toutes les affectations"""
    model = ZYAF
    template_name = 'affectations/liste_affectations.html'
    context_object_name = 'affectations'
    paginate_by = 20


class AffectationCreateView(CreateView):
    """Créer une affectation"""
    model = ZYAF
    form_class = ZYAFForm
    template_name = 'affectations/affectation_form.html'
    success_url = reverse_lazy('liste_affectations')

    def form_valid(self, form):
        messages.success(self.request, "Affectation créée avec succès!")
        return super().form_valid(form)


class AffectationUpdateView(UpdateView):
    """Modifier une affectation"""
    model = ZYAF
    form_class = ZYAFForm
    template_name = 'affectations/affectation_form.html'
    success_url = reverse_lazy('liste_affectations')

    def form_valid(self, form):
        messages.success(self.request, "Affectation modifiée avec succès!")
        return super().form_valid(form)


class AffectationDeleteView(DeleteView):
    """Supprimer une affectation"""
    model = ZYAF
    template_name = 'affectations/affectation_confirm_delete.html'
    success_url = reverse_lazy('liste_affectations')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Affectation supprimée avec succès!")
        return super().delete(request, *args, **kwargs)


# ===============================
# VUES POUR LES ADRESSES (ZYAD)
# ===============================

class AdresseListView(ListView):
    """Liste de toutes les adresses"""
    model = ZYAD
    template_name = 'adresses/liste_adresses.html'
    context_object_name = 'adresses'
    paginate_by = 20


class AdresseCreateView(CreateView):
    """Créer une adresse"""
    model = ZYAD
    form_class = ZYADForm
    template_name = 'adresses/adresse_form.html'
    success_url = reverse_lazy('liste_adresses')

    def form_valid(self, form):
        messages.success(self.request, "Adresse créée avec succès!")
        return super().form_valid(form)


class AdresseUpdateView(UpdateView):
    """Modifier une adresse"""
    model = ZYAD
    form_class = ZYADForm
    template_name = 'adresses/adresse_form.html'
    success_url = reverse_lazy('liste_adresses')

    def form_valid(self, form):
        messages.success(self.request, "Adresse modifiée avec succès!")
        return super().form_valid(form)


class AdresseDeleteView(DeleteView):
    """Supprimer une adresse"""
    model = ZYAD
    template_name = 'adresses/adresse_confirm_delete.html'
    success_url = reverse_lazy('liste_adresses')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Adresse supprimée avec succès!")
        return super().delete(request, *args, **kwargs)




def listeEmployee(request):
    return render(request, "employee/employees-list.html")

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

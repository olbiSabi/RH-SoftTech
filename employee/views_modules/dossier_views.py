# employee/views_modules/dossier_views.py
"""
Vues pour le dossier individuel des employés.
"""
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

from absence.decorators import drh_or_admin_required
from employee.decorators import DRHOrAssistantRHRequiredMixin
from employee.models import ZY00, ZYIB
from departement.models import ZDPO, ZDDE


def get_historique_actif(employe):
    """Retourne l'historique de nom/prénom actif de l'employé."""
    return employe.historique_noms_prenoms.filter(
        actif=True,
        date_fin_validite__isnull=True
    ).first()


class DossierIndividuelView(LoginRequiredMixin, DRHOrAssistantRHRequiredMixin, ListView):
    """Affiche la liste des employés + détail d'un employé sélectionné"""
    login_url = 'login'
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

        # Liste des départements pour le modal d'affectation
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
            context['personnes_prevenir'] = employe_selectionne.personnes_prevenir.all().order_by('ordre_priorite', '-date_debut_validite')

            # Entités liées (optimisées avec select_related)
            context['contrats'] = employe_selectionne.contrats.all().order_by('-date_debut')
            context['affectations'] = employe_selectionne.affectations.select_related('poste__DEPARTEMENT').order_by('-date_debut')
            context['telephones'] = employe_selectionne.telephones.all().order_by('-date_debut_validite')
            context['emails'] = employe_selectionne.emails.all().order_by('-date_debut_validite')
            context['adresses'] = employe_selectionne.adresses.all().order_by('-date_debut')
            context['documents'] = employe_selectionne.documents.all().order_by('-date_ajout')

            # Personnes à charge et statistiques
            personnes_charge = employe_selectionne.personnes_charge.all()
            context['personnes_charge'] = personnes_charge

            # Personnes à prévenir count
            context['nb_personnes_prevenir'] = employe_selectionne.personnes_prevenir.filter(
                actif=True,
                date_fin_validite__isnull=True
            ).count()

            # Calcul des statistiques famille
            context['nb_total'] = personnes_charge.count()
            context['nb_enfants'] = personnes_charge.filter(personne_charge='ENFANT').count()
            context['nb_conjoints'] = personnes_charge.filter(personne_charge='CONJOINT').count()
            context['nb_actifs'] = personnes_charge.filter(actif=True).count()

            # Identité bancaire (RIB)
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

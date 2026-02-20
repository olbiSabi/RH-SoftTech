# employee/views_modules/embauche_views.py
"""
Vues pour le processus d'embauche.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from absence.decorators import drh_or_admin_required
from employee.models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYNP
from employee.forms import EmbaucheAgentForm
from employee.utils import get_redirect_url_with_tab
from employee.services.embauche_service import EmbaucheService


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

                    # Date du jour pour les dates de début
                    date_jour = timezone.now().date()

                    # Création automatique dans ZYNP (Historique nom/prénom)
                    ZYNP.objects.create(
                        employe=employe,
                        nom=employe.nom,
                        prenoms=employe.prenoms,
                        date_debut_validite=date_jour,
                        actif=True
                    )

                    # Créer le contrat
                    ZYCO.objects.create(
                        employe=employe,
                        type_contrat=form.cleaned_data['type_contrat'],
                        date_debut=form.cleaned_data['date_debut_contrat'],
                        date_fin=form.cleaned_data.get('date_fin_contrat')
                    )

                    # Créer le téléphone
                    ZYTE.objects.create(
                        employe=employe,
                        numero=form.cleaned_data['numero_telephone'],
                        date_debut_validite=date_jour
                    )

                    # Créer l'email (AVANT le compte utilisateur)
                    ZYME.objects.create(
                        employe=employe,
                        email=form.cleaned_data['email'],
                        date_debut_validite=date_jour
                    )

                    # Création du compte utilisateur (utilise l'email ZYME ci-dessus)
                    username, password = EmbaucheService.create_user_account(employe)

                    # Créer l'affectation
                    ZYAF.objects.create(
                        employe=employe,
                        poste=form.cleaned_data['poste'],
                        date_debut=date_jour
                    )

                    # Créer l'adresse principale
                    ZYAD.objects.create(
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
                        f"Pré-embauche de {employe.nom} {employe.prenoms} créée avec succès ! "
                        f"Matricule : {employe.matricule}"
                    )

                    # Rediriger vers la liste des employés
                    return redirect('employee:liste_employes')

            except Exception as e:
                messages.error(
                    request,
                    f"Erreur lors de la création de la pré-embauche : {str(e)}"
                )
                return render(request, 'employee/embauche-agent.html', {'form': form})
        else:
            messages.error(
                request,
                "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués ci-dessous."
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
        success, message = EmbaucheService.validate_embauche(employe)
        if success:
            messages.success(request, message)
        else:
            messages.warning(request, message)
    else:
        messages.warning(request, "Cet employé est déjà validé.")

    # Conservation de l'onglet actif
    base_url = reverse('employee:detail_employe', kwargs={'uuid': uuid})
    redirect_url = get_redirect_url_with_tab(request, base_url)
    return redirect(redirect_url)

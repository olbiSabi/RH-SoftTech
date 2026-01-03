# gestionnaire/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction

from absence.decorators import drh_or_admin_required
from .models import Entreprise
from .forms import EntrepriseForm
from absence.models import ConfigurationConventionnelle

@drh_or_admin_required
@login_required
def profil_entreprise(request):
    """
    Affiche ou crée le profil de l'entreprise unique
    """
    try:
        # Récupérer l'entreprise (il ne devrait y en avoir qu'une)
        entreprise = Entreprise.objects.first()
    except Entreprise.DoesNotExist:
        entreprise = None

    context = {
        'entreprise': entreprise,
    }

    # Si l'entreprise existe, récupérer aussi la convention
    if entreprise and entreprise.configuration_conventionnelle:
        context['convention'] = entreprise.configuration_conventionnelle

    # Conventions disponibles pour le select
    context['conventions'] = ConfigurationConventionnelle.objects.filter(actif=True).order_by('nom')

    return render(request, 'entreprise/profil_entreprise.html', context)


@drh_or_admin_required
@login_required
@require_POST
def api_entreprise_create(request):
    """
    Crée l'entreprise unique via AJAX
    """
    try:
        # Vérifier qu'il n'existe pas déjà une entreprise
        if Entreprise.objects.exists():
            return JsonResponse({
                'success': False,
                'error': 'Une entreprise existe déjà. Veuillez la modifier au lieu d\'en créer une nouvelle.'
            }, status=400)

        form = EntrepriseForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                entreprise = form.save()

            messages.success(request, f"Entreprise '{entreprise.nom}' créée avec succès")

            return JsonResponse({
                'success': True,
                'message': 'Entreprise créée avec succès',
                'uuid': str(entreprise.uuid)
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = str(error_list[0])

            return JsonResponse({'success': False, 'errors': errors}, status=400)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@drh_or_admin_required
@login_required
@require_POST
def api_entreprise_update(request, uuid):
    """
    Met à jour l'entreprise unique via AJAX
    """
    try:
        entreprise = get_object_or_404(Entreprise, uuid=uuid)
        form = EntrepriseForm(request.POST, request.FILES, instance=entreprise)

        if form.is_valid():
            with transaction.atomic():
                entreprise = form.save()

            messages.success(request, f"Entreprise '{entreprise.nom}' modifiée avec succès")

            return JsonResponse({
                'success': True,
                'message': 'Entreprise modifiée avec succès'
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = str(error_list[0])

            return JsonResponse({'success': False, 'errors': errors}, status=400)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@drh_or_admin_required
@login_required
@require_POST
def api_entreprise_delete(request, uuid):
    """
    Supprime l'entreprise via AJAX
    """
    try:
        entreprise = get_object_or_404(Entreprise, uuid=uuid)

        # Vérifier s'il y a des employés
        if entreprise.effectif_total > 0:
            return JsonResponse({
                'success': False,
                'error': f"Impossible de supprimer l'entreprise '{entreprise.nom}'. "
                         f"Elle possède {entreprise.effectif_total} employé(s) actif(s)."
            }, status=400)

        nom = entreprise.nom
        entreprise.delete()

        messages.success(request, f"Entreprise '{nom}' supprimée avec succès")

        return JsonResponse({
            'success': True,
            'message': 'Entreprise supprimée avec succès'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@drh_or_admin_required
@login_required
@require_http_methods(["GET"])
def api_entreprise_detail(request, uuid):
    """
    Retourne les détails d'une entreprise en JSON
    """
    try:
        entreprise = get_object_or_404(Entreprise, uuid=uuid)

        data = {
            'id': entreprise.id,
            'uuid': str(entreprise.uuid),
            'code': entreprise.code,
            'nom': entreprise.nom,
            'raison_sociale': entreprise.raison_sociale or '',
            'sigle': entreprise.sigle or '',
            'adresse': entreprise.adresse,
            'ville': entreprise.ville,
            'pays': entreprise.pays,
            'telephone': entreprise.telephone or '',
            'email': entreprise.email or '',
            'site_web': entreprise.site_web or '',
            'rccm': entreprise.rccm or '',
            'numero_impot': entreprise.numero_impot or '',
            'numero_cnss': entreprise.numero_cnss or '',
            'configuration_conventionnelle': entreprise.configuration_conventionnelle_id,
            'date_creation': entreprise.date_creation.strftime('%Y-%m-%d') if entreprise.date_creation else '',
            'date_application_convention': entreprise.date_application_convention.strftime(
                '%Y-%m-%d') if entreprise.date_application_convention else '',
            'actif': entreprise.actif,
            'description': entreprise.description or '',
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# employee/views_api/api/famille_api.py
"""
API pour la gestion des personnes à charge (ZYFA).
"""
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone

from employee.models import ZY00, ZYFA


@require_http_methods(["GET"])
@login_required
def api_famille_detail(request, id):
    """Récupérer les détails d'une personne à charge."""
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
    """Créer une personne à charge via modal."""
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
            'message': 'Personne à charge ajoutée avec succès',
            'id': famille.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_famille_update_modal(request, id):
    """Mettre à jour une personne à charge via modal."""
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
            'message': 'Personne à charge modifiée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_famille_delete_modal(request, id):
    """Supprimer une personne à charge via modal."""
    try:
        famille = get_object_or_404(ZYFA, id=id)
        with transaction.atomic():
            famille.delete()

        return JsonResponse({
            'success': True,
            'message': 'Personne à charge supprimée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

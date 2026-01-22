# employee/views_api/api/znp_api.py
"""
API pour la gestion de l'historique noms/prénoms (ZYNP).
"""
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError

from employee.models import ZY00, ZYNP


@require_http_methods(["GET"])
@login_required
def api_znp_detail(request, id):
    """Récupérer les détails d'un historique nom/prénom."""
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
    """Créer un historique nom/prénom via modal avec validation des chevauchements."""
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
            'message': 'Historique nom/prénom créé avec succès',
            'id': znp.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_znp_update_modal(request, id):
    """Mettre à jour un historique nom/prénom via modal avec validation des chevauchements."""
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

        # Validation des chevauchements (en excluant l'instance courante)
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
            'message': 'Historique nom/prénom modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_znp_delete_modal(request, id):
    """Supprimer un historique nom/prénom via modal."""
    try:
        znp = get_object_or_404(ZYNP, id=id)
        with transaction.atomic():
            znp.delete()

        return JsonResponse({
            'success': True,
            'message': 'Historique nom/prénom supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

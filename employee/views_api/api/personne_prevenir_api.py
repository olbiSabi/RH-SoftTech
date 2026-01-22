# employee/views_api/api/personne_prevenir_api.py
"""
API pour la gestion des personnes à prévenir (ZYPP).
"""
from datetime import datetime
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError

from employee.models import ZY00, ZYPP

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
def api_personne_prevenir_detail(request, id):
    """Récupérer les détails d'une personne à prévenir."""
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
    """Créer une personne à prévenir via modal."""
    try:
        employe_uuid = request.POST.get('employe_uuid')
        employe = get_object_or_404(ZY00, uuid=employe_uuid)

        # Validation de base
        errors = {}
        required_fields = ['nom', 'prenom', 'lien_parente', 'telephone_principal', 'ordre_priorite',
                           'date_debut_validite']
        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
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
                personne.full_clean()
            except ValidationError as e:
                return JsonResponse({'errors': e.message_dict}, status=400)

            personne.save()
            logger.info(f"Personne à prévenir créée: {personne.id}")

        return JsonResponse({
            'success': True,
            'message': 'Personne à prévenir créée avec succès',
            'id': personne.id
        })

    except Exception as e:
        logger.error(f"Erreur création personne à prévenir: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_personne_prevenir_update_modal(request, id):
    """Mettre à jour une personne à prévenir via modal."""
    try:
        personne = get_object_or_404(ZYPP, id=id)

        # Validation de base
        errors = {}
        required_fields = ['nom', 'prenom', 'lien_parente', 'telephone_principal', 'ordre_priorite',
                           'date_debut_validite']
        for field in required_fields:
            value = request.POST.get(field)
            if not value:
                errors[field] = ['Ce champ est requis']

        if errors:
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
                return JsonResponse({'errors': e.message_dict}, status=400)

            personne.save()
            logger.info(f"Personne à prévenir modifiée: {personne.id}")

        return JsonResponse({
            'success': True,
            'message': 'Personne à prévenir modifiée avec succès'
        })

    except Exception as e:
        logger.error(f"Erreur modification personne à prévenir: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_personne_prevenir_delete_modal(request, id):
    """Supprimer une personne à prévenir via modal."""
    try:
        personne = get_object_or_404(ZYPP, id=id)
        nom_complet = f"{personne.prenom} {personne.nom}"

        with transaction.atomic():
            personne.delete()

        logger.info(f"Personne à prévenir supprimée: {nom_complet}")

        return JsonResponse({
            'success': True,
            'message': f'Personne à prévenir ({nom_complet}) supprimée avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur suppression personne à prévenir: {e}")
        return JsonResponse({'error': str(e)}, status=400)

# employee/views_modules/roles_views.py
"""
Vues pour la gestion des rôles des employés.
"""
from datetime import date

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction

from absence.decorators import gestion_app_required
from employee.models import ZY00, ZYRO, ZYRE


@login_required
@gestion_app_required
def gestion_roles_employes(request):
    """
    Page principale de gestion des rôles employés
    """
    # Filtres
    filtre_employe = request.GET.get('employe', '')
    filtre_role = request.GET.get('role', '')
    filtre_statut = request.GET.get('statut', 'actif')

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

        # Vérification existante
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
                'message': f'Rôle "{role.LIBELLE}" attribué à {employe.nom} {employe.prenoms} avec succès',
                'attribution_id': str(attribution.pk)
            })

    except ValidationError as ve:
        return JsonResponse({
            'success': False,
            'error': str(ve)
        }, status=400)

    except Exception as e:
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
                'message': f'Rôle "{attribution.role.LIBELLE}" retiré de {attribution.employe.nom}'
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
                'message': f'Rôle "{attribution.role.LIBELLE}" réactivé pour {attribution.employe.nom}'
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
    Modifier une attribution de rôle (dates, commentaire, et rôle)
    """
    try:
        attribution = get_object_or_404(ZYRE, pk=attribution_id)

        role_id = request.POST.get('role_id')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        with transaction.atomic():
            # Modification du rôle si fourni
            if role_id and str(attribution.role.pk) != str(role_id):
                nouveau_role = get_object_or_404(ZYRO, pk=role_id)

                # Vérifier qu'il n'y a pas déjà une attribution active pour ce nouveau rôle
                existing = ZYRE.objects.filter(
                    employe=attribution.employe,
                    role=nouveau_role,
                    actif=True,
                    date_fin__isnull=True
                ).exclude(pk=attribution.pk).exists()

                if existing:
                    return JsonResponse({
                        'success': False,
                        'error': f'Le rôle "{nouveau_role.LIBELLE}" est déjà actif pour cet employé'
                    }, status=400)

                attribution.role = nouveau_role

            # Modification des dates
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
                'message': 'Attribution modifiée avec succès'
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
            attribution.delete()

            return JsonResponse({
                'success': True,
                'message': f'Attribution du rôle "{role_libelle}" supprimée pour {employe_nom}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
@gestion_app_required
def get_attribution_details(request, attribution_id):
    """
    API pour récupérer les détails d'une attribution (pour le formulaire de modification)
    """
    try:
        attribution = get_object_or_404(ZYRE.objects.select_related('employe', 'role'), pk=attribution_id)

        return JsonResponse({
            'success': True,
            'attribution': {
                'id': str(attribution.pk),
                'employe_nom': f"{attribution.employe.nom} {attribution.employe.prenoms}",
                'employe_matricule': attribution.employe.matricule,
                'role_id': attribution.role.pk,
                'role_libelle': attribution.role.LIBELLE,
                'role_code': attribution.role.CODE,
                'date_debut': attribution.date_debut.strftime('%Y-%m-%d'),
                'date_fin': attribution.date_fin.strftime('%Y-%m-%d') if attribution.date_fin else '',
                'actif': attribution.actif,
                'commentaire': attribution.commentaire or '',
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

"""API views pour le module Planning."""
import logging
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction

from .models import Affectation, Evenement, PosteTravail, Planning
from .permissions import get_planning_role, get_visible_employees, get_visible_plannings, can_edit_planning
from employee.models import ZY00

logger = logging.getLogger(__name__)

# Couleurs par statut/type pour FullCalendar
COULEURS_AFFECTATION = {
    'PLANIFIE': '#17a2b8',
    'CONFIRME': '#1c5d5f',
    'EN_COURS': '#28a745',
    'TERMINE': '#6c757d',
    'ANNULE': '#e74a3b',
}

COULEURS_EVENEMENT = {
    'REUNION': '#6f42c1',
    'FORMATION': '#fd7e14',
    'TACHE': '#20c997',
    'AUTRE': '#858796',
}


# ===== AFFECTATIONS =====

@require_http_methods(["GET"])
@login_required
def api_affectations(request):
    """Liste des affectations au format FullCalendar."""
    try:
        start = request.GET.get('start', '')
        end = request.GET.get('end', '')

        visible = get_visible_employees(request.user)
        qs = Affectation.objects.filter(
            employe__in=visible
        ).select_related('employe', 'poste', 'poste__site', 'planning')

        if start:
            qs = qs.filter(date__gte=start[:10])
        if end:
            qs = qs.filter(date__lte=end[:10])

        events = []
        for a in qs:
            events.append({
                'id': f'aff-{a.id}',
                'title': f'{a.employe.nom} {a.employe.prenoms} - {a.poste.nom}',
                'start': f'{a.date}T{a.heure_debut}',
                'end': f'{a.date}T{a.heure_fin}',
                'backgroundColor': COULEURS_AFFECTATION.get(a.statut, '#17a2b8'),
                'borderColor': COULEURS_AFFECTATION.get(a.statut, '#17a2b8'),
                'extendedProps': {
                    'type': 'affectation',
                    'pk': a.id,
                    'employe_matricule': a.employe.matricule,
                    'employe_nom': f'{a.employe.nom} {a.employe.prenoms}',
                    'poste_id': a.poste.id,
                    'poste_nom': a.poste.nom,
                    'site_nom': a.poste.site.nom,
                    'planning_id': a.planning.id,
                    'planning_titre': a.planning.titre,
                    'statut': a.statut,
                    'notes': a.notes,
                }
            })

        return JsonResponse(events, safe=False)

    except Exception as e:
        logger.exception("Erreur api_affectations")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
def api_affectation_create(request):
    """Creer une affectation."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        visible = get_visible_employees(request.user)
        employe_matricule = request.POST.get('employe')

        if not visible.filter(matricule=employe_matricule).exists():
            return JsonResponse({'success': False, 'error': 'Employe non autorise'}, status=403)

        employe = ZY00.objects.get(matricule=employe_matricule)

        planning_id = request.POST.get('planning')
        if not get_visible_plannings(request.user).filter(id=planning_id).exists():
            return JsonResponse({'success': False, 'error': 'Planning non autorise'}, status=403)
        planning = get_object_or_404(Planning, id=planning_id)
        poste = get_object_or_404(PosteTravail, id=request.POST.get('poste'))

        # Detection de chevauchement
        date_aff = request.POST.get('date')
        heure_debut = request.POST.get('heure_debut')
        heure_fin = request.POST.get('heure_fin')
        chevauchement = Affectation.objects.filter(
            employe=employe,
            date=date_aff,
            heure_debut__lt=heure_fin,
            heure_fin__gt=heure_debut,
        )
        if chevauchement.exists():
            aff_existante = chevauchement.first()
            return JsonResponse({
                'success': False,
                'error': f'Chevauchement : {employe.nom} est deja affecte de '
                         f'{aff_existante.heure_debut:%H:%M} a {aff_existante.heure_fin:%H:%M} '
                         f'le {aff_existante.date:%d/%m/%Y} sur le poste "{aff_existante.poste.nom}".'
            }, status=409)

        with transaction.atomic():
            affectation = Affectation.objects.create(
                planning=planning,
                employe=employe,
                poste=poste,
                date=date_aff,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                statut=request.POST.get('statut', 'PLANIFIE'),
                notes=request.POST.get('notes', ''),
                created_by=request.user,
            )

        return JsonResponse({
            'success': True,
            'message': 'Affectation creee avec succes',
            'id': affectation.id,
        })

    except ZY00.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employe non trouve'}, status=404)
    except Exception as e:
        logger.exception("Erreur api_affectation_create")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_affectation_detail(request, pk):
    """Detail d'une affectation."""
    try:
        affectation = get_object_or_404(
            Affectation.objects.select_related('employe', 'poste', 'poste__site', 'planning'),
            pk=pk
        )

        visible = get_visible_employees(request.user)
        if not visible.filter(matricule=affectation.employe.matricule).exists():
            return JsonResponse({'success': False, 'error': 'Acces refuse'}, status=403)

        data = {
            'id': affectation.id,
            'planning_id': affectation.planning.id,
            'planning_titre': affectation.planning.titre,
            'employe_matricule': affectation.employe.matricule,
            'employe_nom': f'{affectation.employe.nom} {affectation.employe.prenoms}',
            'poste_id': affectation.poste.id,
            'poste_nom': affectation.poste.nom,
            'site_nom': affectation.poste.site.nom,
            'date': str(affectation.date),
            'heure_debut': str(affectation.heure_debut)[:5],
            'heure_fin': str(affectation.heure_fin)[:5],
            'statut': affectation.statut,
            'notes': affectation.notes,
        }
        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def api_affectation_update(request, pk):
    """Modifier une affectation."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        affectation = get_object_or_404(Affectation, pk=pk)
        visible = get_visible_employees(request.user)

        if not visible.filter(matricule=affectation.employe.matricule).exists():
            return JsonResponse({'success': False, 'error': 'Acces refuse'}, status=403)

        with transaction.atomic():
            employe_matricule = request.POST.get('employe')
            if employe_matricule:
                if not visible.filter(matricule=employe_matricule).exists():
                    return JsonResponse({'success': False, 'error': 'Employe non autorise'}, status=403)
                affectation.employe = ZY00.objects.get(matricule=employe_matricule)

            planning_id = request.POST.get('planning')
            if planning_id:
                if not get_visible_plannings(request.user).filter(id=planning_id).exists():
                    return JsonResponse({'success': False, 'error': 'Planning non autorise'}, status=403)
                affectation.planning = get_object_or_404(Planning, id=planning_id)

            poste_id = request.POST.get('poste')
            if poste_id:
                affectation.poste = get_object_or_404(PosteTravail, id=poste_id)

            for field in ('date', 'heure_debut', 'heure_fin', 'statut', 'notes'):
                value = request.POST.get(field)
                if value is not None:
                    setattr(affectation, field, value)

            # Detection de chevauchement (exclure l'affectation courante)
            chevauchement = Affectation.objects.filter(
                employe=affectation.employe,
                date=affectation.date,
                heure_debut__lt=affectation.heure_fin,
                heure_fin__gt=affectation.heure_debut,
            ).exclude(pk=pk)
            if chevauchement.exists():
                aff_existante = chevauchement.first()
                return JsonResponse({
                    'success': False,
                    'error': f'Chevauchement : {affectation.employe.nom} est deja affecte de '
                             f'{aff_existante.heure_debut:%H:%M} a {aff_existante.heure_fin:%H:%M} '
                             f'le {aff_existante.date:%d/%m/%Y} sur le poste "{aff_existante.poste.nom}".'
                }, status=409)

            affectation.save()

        return JsonResponse({'success': True, 'message': 'Affectation mise a jour'})

    except Exception as e:
        logger.exception("Erreur api_affectation_update")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def api_affectation_delete(request, pk):
    """Supprimer une affectation."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        affectation = get_object_or_404(Affectation, pk=pk)
        visible = get_visible_employees(request.user)

        if not visible.filter(matricule=affectation.employe.matricule).exists():
            return JsonResponse({'success': False, 'error': 'Acces refuse'}, status=403)

        with transaction.atomic():
            affectation.delete()

        return JsonResponse({'success': True, 'message': 'Affectation supprimee'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== EVENEMENTS =====

@require_http_methods(["GET"])
@login_required
def api_evenements(request):
    """Liste des evenements au format FullCalendar."""
    try:
        start = request.GET.get('start', '')
        end = request.GET.get('end', '')

        visible = get_visible_employees(request.user)
        qs = Evenement.objects.filter(
            employes__in=visible
        ).distinct().prefetch_related('employes')

        if start:
            qs = qs.filter(date_fin__gte=start[:10])
        if end:
            qs = qs.filter(date_debut__lte=end[:10])

        events = []
        for ev in qs:
            participants = list(ev.employes.values_list('matricule', flat=True))
            participants_noms = [
                f'{e.nom} {e.prenoms}' for e in ev.employes.all()
            ]

            events.append({
                'id': f'evt-{ev.id}',
                'title': ev.titre,
                'start': ev.date_debut.isoformat(),
                'end': ev.date_fin.isoformat(),
                'backgroundColor': COULEURS_EVENEMENT.get(ev.type_evenement, '#858796'),
                'borderColor': COULEURS_EVENEMENT.get(ev.type_evenement, '#858796'),
                'extendedProps': {
                    'type': 'evenement',
                    'pk': ev.id,
                    'type_evenement': ev.type_evenement,
                    'description': ev.description,
                    'lieu': ev.lieu,
                    'participants': participants,
                    'participants_noms': participants_noms,
                }
            })

        return JsonResponse(events, safe=False)

    except Exception as e:
        logger.exception("Erreur api_evenements")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
def api_evenement_create(request):
    """Creer un evenement."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        with transaction.atomic():
            evenement = Evenement.objects.create(
                titre=request.POST.get('titre'),
                description=request.POST.get('description', ''),
                date_debut=request.POST.get('date_debut'),
                date_fin=request.POST.get('date_fin'),
                type_evenement=request.POST.get('type_evenement', 'REUNION'),
                lieu=request.POST.get('lieu', ''),
                created_by=request.user,
            )

            # Ajouter les participants
            employes_ids = request.POST.getlist('employes')
            if employes_ids:
                visible = get_visible_employees(request.user)
                employes = visible.filter(matricule__in=employes_ids)
                evenement.employes.set(employes)

        return JsonResponse({
            'success': True,
            'message': 'Evenement cree avec succes',
            'id': evenement.id,
        })

    except Exception as e:
        logger.exception("Erreur api_evenement_create")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_evenement_detail(request, pk):
    """Detail d'un evenement."""
    try:
        evenement = get_object_or_404(Evenement.objects.prefetch_related('employes'), pk=pk)

        participants = list(
            evenement.employes.values('matricule', 'nom', 'prenoms')
        )

        data = {
            'id': evenement.id,
            'titre': evenement.titre,
            'description': evenement.description,
            'date_debut': evenement.date_debut.strftime('%Y-%m-%dT%H:%M'),
            'date_fin': evenement.date_fin.strftime('%Y-%m-%dT%H:%M'),
            'type_evenement': evenement.type_evenement,
            'type_evenement_display': evenement.get_type_evenement_display(),
            'lieu': evenement.lieu,
            'participants': participants,
        }
        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def api_evenement_update(request, pk):
    """Modifier un evenement."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        evenement = get_object_or_404(Evenement, pk=pk)

        with transaction.atomic():
            for field in ('titre', 'description', 'type_evenement', 'lieu'):
                value = request.POST.get(field)
                if value is not None:
                    setattr(evenement, field, value)

            date_debut = request.POST.get('date_debut')
            if date_debut:
                evenement.date_debut = date_debut

            date_fin = request.POST.get('date_fin')
            if date_fin:
                evenement.date_fin = date_fin

            evenement.save()

            # Mettre a jour les participants (vide = supprimer tous)
            employes_ids = request.POST.getlist('employes')
            if 'employes' in request.POST:
                visible = get_visible_employees(request.user)
                valid_ids = [m for m in employes_ids if m]
                if valid_ids:
                    employes = visible.filter(matricule__in=valid_ids)
                    evenement.employes.set(employes)
                else:
                    evenement.employes.clear()

        return JsonResponse({'success': True, 'message': 'Evenement mis a jour'})

    except Exception as e:
        logger.exception("Erreur api_evenement_update")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def api_evenement_delete(request, pk):
    """Supprimer un evenement."""
    if not can_edit_planning(request.user):
        return JsonResponse({'success': False, 'error': 'Permission refusee'}, status=403)

    try:
        evenement = get_object_or_404(Evenement, pk=pk)

        with transaction.atomic():
            evenement.delete()

        return JsonResponse({'success': True, 'message': 'Evenement supprime'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== UTILITAIRES =====

@require_http_methods(["GET"])
@login_required
def api_postes_par_site(request, site_id):
    """Retourne les postes actifs d'un site."""
    try:
        postes = PosteTravail.objects.filter(
            site_id=site_id, is_active=True
        ).values('id', 'nom', 'type_poste', 'heure_debut', 'heure_fin')

        return JsonResponse({'success': True, 'postes': list(postes)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

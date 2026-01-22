# gestion_temps_activite/views/api_views.py
"""Endpoints API/AJAX pour le module GTA."""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from gestion_temps_activite.models import ZDPJ, ZDTA, ZDAC


@login_required
def api_taches_par_projet(request, projet_id):
    """
    API pour récupérer les tâches d'un projet.
    Utilisé pour les formulaires dynamiques (ex: sélection de tâche après choix du projet).
    """
    try:
        projet = ZDPJ.objects.get(pk=projet_id)

        taches = projet.taches.all().values(
            'id', 'code_tache', 'titre', 'statut'
        ).order_by('code_tache')

        taches_list = [
            {
                'id': str(t['id']),
                'code': t['code_tache'],
                'titre': t['titre'],
                'statut': t['statut'],
                'display': f"{t['code_tache']} - {t['titre']}"
            }
            for t in taches
        ]

        return JsonResponse({
            'success': True,
            'taches': taches_list
        })

    except ZDPJ.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Projet non trouvé'
        }, status=404)


@login_required
def api_activites_en_vigueur(request):
    """
    API pour récupérer les types d'activités en vigueur.
    Filtre sur les activités actives et dans la plage de dates valide.
    """
    date_actuelle = timezone.now().date()

    activites = ZDAC.objects.filter(
        actif=True,
        date_debut__lte=date_actuelle
    ).filter(
        Q(date_fin__isnull=True) | Q(date_fin__gte=date_actuelle)
    ).values(
        'id', 'code_activite', 'libelle', 'facturable', 'taux_horaire_defaut'
    ).order_by('libelle')

    activites_list = [
        {
            'id': str(a['id']),
            'code': a['code_activite'],
            'libelle': a['libelle'],
            'facturable': a['facturable'],
            'taux_horaire': float(a['taux_horaire_defaut']) if a['taux_horaire_defaut'] else None,
            'display': f"{a['code_activite']} - {a['libelle']}"
        }
        for a in activites
    ]

    return JsonResponse({
        'success': True,
        'activites': activites_list
    })

# gestion_temps_activite/views/dashboard_views.py
"""Vue du dashboard GTA."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from gestion_temps_activite.services import StatistiqueService


@login_required
def dashboard(request):
    """Dashboard principal du module Gestion Temps et Activités."""
    # Statistiques globales
    stats = StatistiqueService.get_stats_dashboard()

    # Projets récents
    projets_recents = StatistiqueService.get_projets_recents(5)

    # Tâches urgentes
    taches_urgentes = StatistiqueService.get_taches_urgentes(10)

    # Statistiques personnelles si employé connecté
    stats_employe = None
    if hasattr(request.user, 'employe'):
        stats_employe = StatistiqueService.get_stats_employe(request.user.employe)

    context = {
        'total_clients': stats['total_clients'],
        'total_projets': stats['total_projets'],
        'projets_en_cours': stats['projets_en_cours'],
        'total_taches': stats['total_taches'],
        'projets_recents': projets_recents,
        'taches_urgentes': taches_urgentes,
        'stats_employe': stats_employe,
    }

    return render(request, 'gestion_temps_activite/dashboard.html', context)

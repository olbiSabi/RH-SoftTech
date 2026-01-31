from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, FloatField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from ..models import JRClient, JRProject, JRTicket, JRImputation, JRSprint
from employee.models import ZY00


@login_required
def dashboard(request):
    """Vue principale du tableau de bord avec données pré-chargées"""

    # Récupérer l'employé associé à l'utilisateur
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        employe = None

    # Statistiques globales
    projets_actifs = JRProject.objects.filter(
        statut__in=['PLANIFIE', 'ACTIF']
    ).select_related('client', 'chef_projet').order_by('-created_at')[:5]

    total_projets = projets_actifs.count()

    tickets_en_cours = JRTicket.objects.filter(statut='EN_COURS').count()
    tickets_ouverts = JRTicket.objects.filter(statut='OUVERT').count()
    tickets_termines = JRTicket.objects.filter(statut='TERMINE').count()

    # Tickets récents
    tickets_recents = JRTicket.objects.select_related(
        'projet', 'assigne'
    ).order_by('-created_at')[:5]

    # Temps cette semaine (employé connecté)
    debut_semaine = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    heures_semaine = 0
    mes_tickets = []

    if employe:
        heures_semaine = JRImputation.objects.filter(
            date_imputation__gte=debut_semaine,
            statut_validation='VALIDE',
            employe=employe
        ).aggregate(
            total=ExpressionWrapper(
                Coalesce(Sum('heures'), Value(0)) + Coalesce(Sum('minutes'), Value(0)) / 60.0,
                output_field=FloatField()
            )
        )['total'] or 0

        # Mes tickets assignés
        mes_tickets = JRTicket.objects.filter(
            assigne=employe,
            statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
        ).select_related('projet').order_by('-priorite', '-created_at')[:5]

    # Alertes (tickets en retard)
    tickets_retard = JRTicket.objects.filter(
        date_echeance__lt=timezone.now().date(),
        statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
    ).select_related('projet', 'assigne').count()

    # Imputations en attente de validation
    imputations_en_attente = 0
    if employe:
        projets_chef = JRProject.objects.filter(chef_projet=employe)
        imputations_en_attente = JRImputation.objects.filter(
            statut_validation='EN_ATTENTE',
            ticket__projet__in=projets_chef
        ).count()

    context = {
        'employe': employe,
        # Stats principales
        'total_projets': total_projets,
        'tickets_en_cours': tickets_en_cours,
        'tickets_ouverts': tickets_ouverts,
        'tickets_termines': tickets_termines,
        'heures_semaine': round(heures_semaine, 1),
        # Listes
        'projets_actifs': projets_actifs,
        'tickets_recents': tickets_recents,
        'mes_tickets': mes_tickets,
        # Alertes
        'tickets_retard': tickets_retard,
        'imputations_en_attente': imputations_en_attente,
    }

    return render(request, 'project_management/dashboard.html', context)


@login_required
def dashboard_stats_api(request):
    """API pour les statistiques du dashboard"""
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        employe = None

    # Projets actifs
    total_projets = JRProject.objects.filter(
        statut__in=['PLANIFIE', 'ACTIF']
    ).count()

    # Tickets en cours
    tickets_en_cours = JRTicket.objects.filter(
        statut='EN_COURS'
    ).count()

    # Tickets terminés
    tickets_termines = JRTicket.objects.filter(
        statut='TERMINE'
    ).count()

    # Temps cette semaine
    debut_semaine = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    heures_semaine = 0

    if employe:
        heures_semaine = JRImputation.objects.filter(
            date_imputation__gte=debut_semaine,
            statut_validation='VALIDE',
            employe=employe
        ).aggregate(
            total=ExpressionWrapper(
                Coalesce(Sum('heures'), Value(0)) + Coalesce(Sum('minutes'), Value(0)) / 60.0,
                output_field=FloatField()
            )
        )['total'] or 0

    stats = {
        'total_projets': total_projets,
        'tickets_en_cours': tickets_en_cours,
        'tickets_termines': tickets_termines,
        'heures_semaine': round(heures_semaine, 1),
    }

    return JsonResponse(stats)


@login_required
def tickets_recents_api(request):
    """API pour les tickets récents"""
    tickets = JRTicket.objects.select_related(
        'projet', 'projet__client', 'assigne'
    ).order_by('-created_at')[:10]

    tickets_data = []
    for ticket in tickets:
        en_retard = (
            ticket.date_echeance and
            ticket.date_echeance < timezone.now().date() and
            ticket.statut in ['OUVERT', 'EN_COURS', 'EN_REVUE']
        )

        assigne_str = 'Non assigné'
        if ticket.assigne:
            prenoms = ticket.assigne.prenoms or ''
            assigne_str = f"{ticket.assigne.nom} {prenoms[0]}." if prenoms else ticket.assigne.nom

        tickets_data.append({
            'id': ticket.id,
            'code': ticket.code,
            'titre': ticket.titre,
            'projet': ticket.projet.nom,
            'priorite': ticket.priorite,
            'priorite_display': ticket.get_priorite_display(),
            'statut': ticket.statut,
            'statut_display': ticket.get_statut_display(),
            'assigne': assigne_str,
            'created_at': ticket.created_at.strftime('%d/%m/%Y %H:%M'),
            'en_retard': en_retard,
            'date_echeance': ticket.date_echeance.strftime('%d/%m/%Y') if ticket.date_echeance else None,
        })

    return JsonResponse(tickets_data, safe=False)


@login_required
def projets_actifs_api(request):
    """API pour les projets actifs"""
    projets = JRProject.objects.select_related('client').filter(
        statut__in=['PLANIFIE', 'ACTIF']
    ).annotate(
        tickets_count=Count('tickets')
    ).order_by('-created_at')[:10]

    projets_data = []
    for projet in projets:
        progression = projet.progression

        projets_data.append({
            'id': projet.id,
            'code': projet.code,
            'nom': projet.nom,
            'client': projet.client.raison_sociale if projet.client else 'N/A',
            'statut': projet.statut,
            'statut_display': projet.get_statut_display(),
            'tickets_count': projet.tickets_count,
            'progression': round(progression, 1),
        })

    return JsonResponse(projets_data, safe=False)


@login_required
def alertes_api(request):
    """API pour les alertes"""
    alertes = []

    # Tickets en retard
    tickets_retard = JRTicket.objects.filter(
        date_echeance__lt=timezone.now().date(),
        statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
    ).select_related('assigne', 'projet')

    for ticket in tickets_retard:
        alertes.append({
            'type': 'ticket_en_retard',
            'titre': f"Ticket en retard : {ticket.code}",
            'message': f"Le ticket '{ticket.titre}' aurait dû être terminé le {ticket.date_echeance.strftime('%d/%m/%Y')}",
            'priorite': 'haute' if ticket.priorite == 'CRITIQUE' else 'moyenne',
            'date': timezone.now().strftime('%d/%m/%Y %H:%M'),
        })

    # Imputations en attente depuis plus de 3 jours
    delai_alerte = timezone.now() - timedelta(days=3)
    imputations_anciennes = JRImputation.objects.filter(
        statut_validation='EN_ATTENTE',
        created_at__lt=delai_alerte
    ).select_related('employe', 'ticket')

    for imp in imputations_anciennes:
        alertes.append({
            'type': 'imputation_en_attente',
            'titre': f"Imputation en attente : {imp.ticket.code}",
            'message': f"L'imputation de {imp.employe} est en attente depuis le {imp.created_at.date().strftime('%d/%m/%Y')}",
            'priorite': 'moyenne',
            'date': timezone.now().strftime('%d/%m/%Y %H:%M'),
        })

    return JsonResponse(alertes, safe=False)


@login_required
def stats_personnelles_api(request):
    """API pour les statistiques personnelles"""
    try:
        employe = ZY00.objects.get(user=request.user)
    except ZY00.DoesNotExist:
        return JsonResponse({
            'tickets_assignes': 0,
            'tickets_termines': 0,
            'temps_mois': 0,
            'taux_completion': 0,
        })

    # Tickets assignés à l'utilisateur
    tickets_assignes = JRTicket.objects.filter(assigne=employe)
    tickets_termines = tickets_assignes.filter(statut='TERMINE')

    # Temps ce mois
    debut_mois = timezone.now().date().replace(day=1)
    temps_mois = JRImputation.objects.filter(
        employe=employe,
        date_imputation__gte=debut_mois,
        statut_validation='VALIDE'
    ).aggregate(
        total=ExpressionWrapper(
            Coalesce(Sum('heures'), Value(0)) + Coalesce(Sum('minutes'), Value(0)) / 60.0,
            output_field=FloatField()
        )
    )['total'] or 0

    # Taux de complétion
    taux_completion = 0
    if tickets_assignes.exists():
        taux_completion = (tickets_termines.count() / tickets_assignes.count()) * 100

    stats = {
        'tickets_assignes': tickets_assignes.count(),
        'tickets_termines': tickets_termines.count(),
        'temps_mois': round(temps_mois, 1),
        'taux_completion': round(taux_completion, 1),
    }

    return JsonResponse(stats)

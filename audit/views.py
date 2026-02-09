# audit/views.py
"""
Vues pour le module Conformité & Audit.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import AUAL, AURA, AURC
from .forms import (
    AURCForm, FiltresLogsForm, FiltresAlertesForm,
    GenererRapportForm, ResoudreAlerteForm
)
from .services import ConformiteService, AlerteService, LogService, RapportAuditService
from core.models import ZDLOG


def _peut_acceder_audit(employe):
    """Vérifie si l'employé peut accéder au module audit."""
    if not employe:
        return False
    # Vérifier les rôles autorisés
    roles_autorises = ['DRH', 'ADMIN', 'AUDITEUR', 'ASSISTANT_RH']
    return employe.has_role_any(roles_autorises) if hasattr(employe, 'has_role_any') else True


# ============================================================================
# Dashboard
# ============================================================================

@login_required
def dashboard(request):
    """Dashboard du module Conformité & Audit."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    # Statistiques des alertes
    stats_alertes = AlerteService.get_alertes_dashboard()
    alertes_par_type = AlerteService.get_alertes_par_type()

    # Alertes récentes
    alertes_recentes = AUAL.objects.filter(
        STATUT__in=['NOUVEAU', 'EN_COURS']
    ).order_by('-DATE_DETECTION')[:10]

    # Statistiques des logs
    stats_logs = LogService.get_statistiques_logs(
        date_debut=timezone.now().date() - timezone.timedelta(days=7)
    )

    # Rapports récents
    rapports_recents = AURA.objects.all()[:5]

    context = {
        'stats_alertes': stats_alertes,
        'alertes_par_type': alertes_par_type,
        'alertes_recentes': alertes_recentes,
        'stats_logs': stats_logs,
        'rapports_recents': rapports_recents,
    }

    return render(request, 'audit/dashboard.html', context)


# ============================================================================
# Alertes
# ============================================================================

@login_required
def liste_alertes(request):
    """Liste des alertes de conformité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    form = FiltresAlertesForm(request.GET)
    alertes = AUAL.objects.all().select_related('EMPLOYE', 'REGLE', 'ASSIGNE_A')

    if form.is_valid():
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            alertes = alertes.filter(
                Q(TITRE__icontains=q) |
                Q(DESCRIPTION__icontains=q) |
                Q(REFERENCE__icontains=q)
            )
        if form.cleaned_data.get('type_alerte'):
            alertes = alertes.filter(TYPE_ALERTE=form.cleaned_data['type_alerte'])
        if form.cleaned_data.get('statut'):
            alertes = alertes.filter(STATUT=form.cleaned_data['statut'])
        if form.cleaned_data.get('priorite'):
            alertes = alertes.filter(PRIORITE=form.cleaned_data['priorite'])
        if form.cleaned_data.get('date_debut'):
            alertes = alertes.filter(DATE_DETECTION__date__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data.get('date_fin'):
            alertes = alertes.filter(DATE_DETECTION__date__lte=form.cleaned_data['date_fin'])

    paginator = Paginator(alertes, 20)
    page = request.GET.get('page', 1)
    alertes_page = paginator.get_page(page)

    context = {
        'alertes': alertes_page,
        'form': form,
        'stats': AlerteService.get_alertes_dashboard(),
    }

    return render(request, 'audit/liste_alertes.html', context)


@login_required
def detail_alerte(request, uuid):
    """Détail d'une alerte."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    alerte = get_object_or_404(AUAL, uuid=uuid)

    context = {
        'alerte': alerte,
    }

    return render(request, 'audit/detail_alerte.html', context)


@login_required
@require_POST
def resoudre_alerte(request, uuid):
    """Résout une alerte."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    alerte = get_object_or_404(AUAL, uuid=uuid)
    form = ResoudreAlerteForm(request.POST)

    if form.is_valid():
        AlerteService.resoudre_alerte(
            alerte,
            employe,
            form.cleaned_data.get('commentaire', '')
        )
        messages.success(request, f"Alerte {alerte.REFERENCE} résolue.")
    else:
        messages.error(request, "Erreur lors de la résolution.")

    return redirect('audit:detail_alerte', uuid=uuid)


@login_required
@require_POST
def ignorer_alerte(request, uuid):
    """Ignore une alerte."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    alerte = get_object_or_404(AUAL, uuid=uuid)
    commentaire = request.POST.get('commentaire', '')

    AlerteService.ignorer_alerte(alerte, employe, commentaire)
    messages.success(request, f"Alerte {alerte.REFERENCE} ignorée.")

    return redirect('audit:liste_alertes')


@login_required
def executer_verifications(request):
    """Exécute toutes les vérifications de conformité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès à cette fonction.")
        return redirect('audit:dashboard')

    resultats = ConformiteService.executer_toutes_verifications()

    total_alertes = sum(len(v) for k, v in resultats.items() if isinstance(v, list))

    if total_alertes > 0:
        messages.success(request, f"{total_alertes} nouvelle(s) alerte(s) créée(s).")
    else:
        messages.info(request, "Aucune nouvelle alerte détectée.")

    return redirect('audit:liste_alertes')


# ============================================================================
# Logs
# ============================================================================

@login_required
def liste_logs(request):
    """Liste des logs d'activité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    form = FiltresLogsForm(request.GET)
    logs = ZDLOG.objects.all().select_related('USER')

    if form.is_valid():
        if form.cleaned_data.get('recherche'):
            q = form.cleaned_data['recherche']
            logs = logs.filter(
                Q(TABLE_NAME__icontains=q) |
                Q(RECORD_ID__icontains=q) |
                Q(USER_NAME__icontains=q) |
                Q(DESCRIPTION__icontains=q)
            )
        if form.cleaned_data.get('table_name'):
            logs = logs.filter(TABLE_NAME__icontains=form.cleaned_data['table_name'])
        if form.cleaned_data.get('type_mouvement'):
            logs = logs.filter(TYPE_MOUVEMENT=form.cleaned_data['type_mouvement'])
        if form.cleaned_data.get('date_debut'):
            logs = logs.filter(DATE_MODIFICATION__date__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data.get('date_fin'):
            logs = logs.filter(DATE_MODIFICATION__date__lte=form.cleaned_data['date_fin'])

    # Statistiques
    stats = {
        'total': logs.count(),
        'creations': logs.filter(TYPE_MOUVEMENT='CREATE').count(),
        'modifications': logs.filter(TYPE_MOUVEMENT='UPDATE').count(),
        'suppressions': logs.filter(TYPE_MOUVEMENT='DELETE').count(),
    }

    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)

    # Tables disponibles pour le filtre
    tables_disponibles = ZDLOG.objects.values_list('TABLE_NAME', flat=True).distinct()[:50]

    context = {
        'logs': logs_page,
        'form': form,
        'stats': stats,
        'tables_disponibles': tables_disponibles,
    }

    return render(request, 'audit/liste_logs.html', context)


@login_required
def detail_log(request, pk):
    """Détail d'un log."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    log = get_object_or_404(ZDLOG, pk=pk)

    context = {
        'log': log,
    }

    return render(request, 'audit/detail_log.html', context)


# ============================================================================
# Rapports
# ============================================================================

@login_required
def liste_rapports(request):
    """Liste des rapports d'audit générés."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    rapports = AURA.objects.all().select_related('GENERE_PAR')

    paginator = Paginator(rapports, 20)
    page = request.GET.get('page', 1)
    rapports_page = paginator.get_page(page)

    context = {
        'rapports': rapports_page,
    }

    return render(request, 'audit/liste_rapports.html', context)


@login_required
def generer_rapport(request):
    """Génère un nouveau rapport d'audit."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    if request.method == 'POST':
        form = GenererRapportForm(request.POST)
        if form.is_valid():
            type_rapport = form.cleaned_data['type_rapport']
            format_export = form.cleaned_data['format_export']
            date_debut = form.cleaned_data['date_debut']
            date_fin = form.cleaned_data['date_fin']

            if type_rapport == 'CONFORMITE':
                rapport = RapportAuditService.generer_rapport_conformite(
                    date_debut, date_fin, employe, format_export
                )
            elif type_rapport == 'LOGS':
                rapport = RapportAuditService.generer_rapport_logs(
                    date_debut, date_fin, employe, format_export
                )
            elif type_rapport == 'CONTRATS':
                rapport = RapportAuditService.generer_rapport_contrats(
                    date_debut, date_fin, employe, format_export
                )
            else:
                # Rapport personnalisé ou autre type
                rapport = AURA.objects.create(
                    TITRE=f"Rapport {type_rapport} du {date_debut} au {date_fin}",
                    TYPE_RAPPORT=type_rapport,
                    FORMAT=format_export,
                    DATE_DEBUT=date_debut,
                    DATE_FIN=date_fin,
                    GENERE_PAR=employe,
                    STATUT='TERMINE'
                )

            if rapport.STATUT == 'TERMINE':
                messages.success(request, f"Rapport {rapport.REFERENCE} généré avec succès.")
            else:
                messages.error(request, f"Erreur lors de la génération: {rapport.MESSAGE_ERREUR}")

            return redirect('audit:liste_rapports')
    else:
        form = GenererRapportForm(initial={
            'date_debut': timezone.now().date() - timezone.timedelta(days=30),
            'date_fin': timezone.now().date()
        })

    context = {
        'form': form,
    }

    return render(request, 'audit/generer_rapport.html', context)


@login_required
def telecharger_rapport(request, uuid):
    """Télécharge un rapport."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    rapport = get_object_or_404(AURA, uuid=uuid)

    if rapport.FICHIER:
        response = HttpResponse(rapport.FICHIER.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{rapport.REFERENCE}.{rapport.FORMAT.lower()}"'
        return response
    else:
        # Générer à la volée si pas de fichier
        if rapport.FORMAT == 'EXCEL':
            output = RapportAuditService.exporter_rapport_excel(rapport)
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{rapport.REFERENCE}.xlsx"'
            return response
        elif rapport.FORMAT == 'PDF':
            # Pour le PDF, générer un simple fichier texte avec les données
            import io
            from django.template.loader import render_to_string
            
            content = f"""
Rapport d'audit
===============
Référence: {rapport.REFERENCE}
Titre: {rapport.TITRE}
Type: {rapport.get_TYPE_RAPPORT_display}
Période: {rapport.DATE_DEBUT.strftime('%d/%m/%Y')} au {rapport.DATE_FIN.strftime('%d/%m/%Y')}
Généré le: {rapport.DATE_GENERATION.strftime('%d/%m/%Y %H:%M')}
Statut: {rapport.get_STATUT_display}
Format: {rapport.FORMAT}

Résumé:
{rapport.RESUME if rapport.RESUME else 'Aucun résumé disponible'}

Nombre d'enregistrements: {rapport.NB_ENREGISTREMENTS}
"""
            
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{rapport.REFERENCE}.txt"'
            return response
        elif rapport.FORMAT == 'CSV':
            # Pour le CSV, exporter les données brutes
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-tête
            writer.writerow(['Référence', 'Titre', 'Type', 'Date début', 'Date fin', 'Statut', 'Généré le'])
            
            # Données
            writer.writerow([
                rapport.REFERENCE,
                rapport.TITRE,
                rapport.get_TYPE_RAPPORT_display,
                rapport.DATE_DEBUT.strftime('%d/%m/%Y'),
                rapport.DATE_FIN.strftime('%d/%m/%Y'),
                rapport.get_STATUT_display,
                rapport.DATE_GENERATION.strftime('%d/%m/%Y %H:%M')
            ])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{rapport.REFERENCE}.csv"'
            return response

    messages.error(request, "Le fichier du rapport n'est pas disponible.")
    return redirect('audit:liste_rapports')


# ============================================================================
# Règles de conformité
# ============================================================================

@login_required
def liste_regles(request):
    """Liste des règles de conformité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    regles = AURC.objects.all().annotate(
        nb_alertes=Count('alertes', filter=Q(alertes__STATUT__in=['NOUVEAU', 'EN_COURS']))
    )

    # Statistiques pour les info-boxes
    stats = {
        'actives': regles.filter(STATUT=True).count(),
        'inactives': regles.filter(STATUT=False).count(),
        'total_alertes': AUAL.objects.filter(STATUT__in=['NOUVEAU', 'EN_COURS']).count(),
        'critiques': regles.filter(SEVERITE='CRITICAL', STATUT=True).count(),
    }

    context = {
        'regles': regles,
        'stats': stats,
    }

    return render(request, 'audit/liste_regles.html', context)


@login_required
def creer_regle(request):
    """Crée une nouvelle règle de conformité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    if request.method == 'POST':
        form = AURCForm(request.POST)
        if form.is_valid():
            regle = form.save()
            messages.success(request, f"Règle {regle.CODE} créée avec succès.")
            return redirect('audit:liste_regles')
    else:
        form = AURCForm()

    context = {
        'form': form,
        'titre': 'Nouvelle règle de conformité',
        'action': 'Créer',
    }

    return render(request, 'audit/form_regle.html', context)


@login_required
def modifier_regle(request, pk):
    """Modifie une règle de conformité."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        messages.error(request, "Vous n'avez pas accès au module Audit.")
        return redirect('home')

    regle = get_object_or_404(AURC, pk=pk)

    if request.method == 'POST':
        form = AURCForm(request.POST, instance=regle)
        if form.is_valid():
            regle = form.save()
            messages.success(request, f"Règle {regle.CODE} modifiée avec succès.")
            return redirect('audit:liste_regles')
    else:
        form = AURCForm(instance=regle)

    context = {
        'form': form,
        'regle': regle,
        'titre': f'Modifier la règle {regle.CODE}',
        'action': 'Enregistrer',
    }

    return render(request, 'audit/form_regle.html', context)


# ============================================================================
# API
# ============================================================================

@login_required
@require_GET
def api_stats_dashboard(request):
    """API pour les stats du dashboard."""
    employe = getattr(request.user, 'employe', None)
    if not _peut_acceder_audit(employe):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    stats_alertes = AlerteService.get_alertes_dashboard()
    stats_logs = LogService.get_statistiques_logs(
        date_debut=timezone.now().date() - timezone.timedelta(days=7)
    )

    return JsonResponse({
        'alertes': stats_alertes,
        'logs': {
            'total': stats_logs['total'],
            'creations': stats_logs['creations'],
            'modifications': stats_logs['modifications'],
            'suppressions': stats_logs['suppressions'],
        }
    })

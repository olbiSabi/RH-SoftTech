"""
Vues Django pour la gestion des congés et absences
Application: absence
Système HR_ONIAN
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta
import json

from .models import ZDDA, ZDSO, ZDHA, ZDJF, ZDPF, ZDAB, calculer_jours_ouvres, mettre_a_jour_solde_conges
from .forms import (
    DemandeAbsenceForm, ValidationManagerForm, ValidationRHForm,
    AnnulationDemandeForm, RechercheDemandeForm
)
from employee.models import ZY00, ZYAF
from departement.models import ZYMA, ZDDE, ZDPO


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def creer_historique(demande, action, utilisateur, ancien_statut=None, nouveau_statut=None, commentaire=None, request=None):
    """Crée une entrée dans l'historique"""
    ip_address = get_client_ip(request) if request else None

    ZDHA.objects.create(
        demande=demande,
        action=action,
        utilisateur=utilisateur,
        ancien_statut=ancien_statut,
        nouveau_statut=nouveau_statut,
        commentaire=commentaire,
        ip_address=ip_address
    )


def get_employe_from_user(user):
    """Récupère l'employé associé à un utilisateur"""
    try:
        return user.employe
    except:
        return None


def est_manager(employe):
    """Vérifie si un employé est manager"""
    return ZYMA.objects.filter(employe=employe, date_fin__isnull=True).exists()


def est_rh(employe):
    """Vérifie si un employé fait partie du service RH"""
    # À adapter selon votre logique métier
    # Exemple: vérifier si l'employé appartient au département RH
    try:
        affectation = ZYAF.objects.filter(
            employe=employe,
            date_fin__isnull=True
        ).select_related('poste__DEPARTEMENT').first()

        if affectation:
            # Supposons que le département RH a le code 'RH' ou 'DRH'
            return affectation.poste.DEPARTEMENT.CODE in ['RH', 'DRH']
    except:
        pass
    return False


# ==========================================
# VUES EMPLOYÉ
# ==========================================

@login_required
def employe_demandes(request):
    """
    Page principale de l'employé pour gérer ses demandes
    Template: employe_demandes.html
    """
    employe = get_employe_from_user(request.user)

    if not employe:
        messages.error(request, "Vous n'êtes pas associé à un employé.")
        return redirect('dashboard')

    # Récupérer le solde de l'année en cours
    annee_courante = timezone.now().year
    solde = ZDSO.get_or_create_solde(employe, annee_courante)

    # Récupérer toutes les demandes de l'employé
    demandes = ZDDA.objects.filter(employe=employe).order_by('-created_at')

    # Traitement du formulaire de création
    if request.method == 'POST':
        form = DemandeAbsenceForm(request.POST, request.FILES, employe=employe)

        if form.is_valid():
            demande = form.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='CREATION',
                utilisateur=employe,
                nouveau_statut=demande.statut,
                commentaire='Demande créée par l\'employé',
                request=request
            )

            # Mettre à jour le solde
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(employe, annee_courante)

            messages.success(request, f'✅ Votre demande a été soumise avec succès!')
            return redirect('absence:employe_demandes')
        else:
            #messages.error(request, '❌ Erreur lors de la soumission. Veuillez corriger les erreurs.')
            print("Erreur lors de la soumission. Veuillez corriger les erreurs.")
    else:
        form = DemandeAbsenceForm(employe=employe)

    # Préparer les données pour le calendrier (JSON sérialisable)
    demandes_pour_calendrier = []
    for demande in demandes.filter(statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH', 'EN_ATTENTE']):
        demandes_pour_calendrier.append({
            'id': str(demande.id),  # Convertir UUID en string
            'date_debut': demande.date_debut.isoformat(),  # Convertir date en ISO format
            'date_fin': demande.date_fin.isoformat(),
            'statut': demande.statut,
            'duree': demande.duree,
            'type_absence': demande.type_absence.LIBELLE,
        })

    context = {
        'employe': employe,
        'form': form,
        'demandes': demandes,
        'solde': solde,
        'demandes_calendrier': json.dumps(demandes_pour_calendrier),  # Convertir en JSON
        'annee_courante': annee_courante,
    }

    return render(request, 'absence/employe_demandes.html', context)


@login_required
@require_http_methods(["POST"])
def employe_annuler_demande(request, demande_id):
    """Annuler une demande d'absence"""
    employe = get_employe_from_user(request.user)
    demande = get_object_or_404(ZDDA, id=demande_id, employe=employe)

    if not demande.peut_etre_annulee():
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne peut plus être annulée.'
        }, status=400)

    motif_annulation = request.POST.get('motif_annulation', '').strip()

    if not motif_annulation:
        return JsonResponse({
            'success': False,
            'error': 'Le motif d\'annulation est obligatoire.'
        }, status=400)

    try:
        with transaction.atomic():
            ancien_statut = demande.statut

            demande.statut = 'ANNULEE'
            demande.est_annulee = True
            demande.date_annulation = timezone.now()
            demande.motif_annulation = motif_annulation
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='ANNULATION',
                utilisateur=employe,
                ancien_statut=ancien_statut,
                nouveau_statut='ANNULEE',
                commentaire=motif_annulation,
                request=request
            )

            # Mettre à jour le solde
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(employe, demande.date_debut.year)

        return JsonResponse({
            'success': True,
            'message': 'Demande annulée avec succès.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==========================================
# VUES MANAGER
# ==========================================

@login_required
def manager_validation(request):
    """
    Page de validation pour les managers
    Template: manager_validation.html
    """
    employe = get_employe_from_user(request.user)

    if not employe:
        messages.error(request, "Vous n'êtes pas associé à un employé.")
        return redirect('dashboard')

    # Vérifier si l'employé est manager
    management = ZYMA.get_manager_actuel_employe(employe)

    if not management:
        messages.error(request, "Vous n'avez pas les droits de manager.")
        return redirect('absence:employe_demandes')

    departement = management.departement

    # Récupérer tous les employés du département
    postes_dept = departement.postes.all()
    employes_dept = ZY00.objects.filter(
        affectations__poste__in=postes_dept,
        affectations__date_fin__isnull=True,
        type_dossier='SAL',
        etat='actif'
    ).distinct()

    # Récupérer les demandes en attente de validation
    demandes_en_attente = ZDDA.objects.filter(
        employe__in=employes_dept,
        statut='EN_ATTENTE'
    ).select_related('employe', 'type_absence').order_by('-est_urgent', 'created_at')

    # Récupérer toutes les demandes du département pour statistiques
    toutes_demandes = ZDDA.objects.filter(employe__in=employes_dept)

    # Statistiques
    stats = {
        'en_attente': demandes_en_attente.count(),
        'validees': toutes_demandes.filter(statut='VALIDEE_MANAGER').count(),
        'refusees': toutes_demandes.filter(statut='REFUSEE_MANAGER').count(),
        'equipe_total': employes_dept.count(),
    }

    # Récupérer les employés avec leur statut (présent/absent/congé)
    equipe_avec_statut = []
    today = timezone.now().date()

    for emp in employes_dept:
        # Vérifier si l'employé est absent aujourd'hui
        absence_today = ZDDA.objects.filter(
            employe=emp,
            statut='VALIDEE_RH',
            date_debut__lte=today,
            date_fin__gte=today
        ).first()

        if absence_today:
            if absence_today.type_absence.CODE == 'MAL':
                statut = 'absent'
            else:
                statut = 'conge'
        else:
            statut = 'present'

        equipe_avec_statut.append({
            'employe': emp,
            'statut': statut
        })

    # Préparer les données pour le calendrier (absences de l'équipe)
    absences_equipe = ZDDA.objects.filter(
        employe__in=employes_dept,
        statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH']
    ).values('date_debut', 'date_fin', 'employe__nom', 'employe__prenoms')

    context = {
        'employe': employe,
        'management': management,
        'departement': departement,
        'demandes_en_attente': demandes_en_attente,
        'equipe_avec_statut': equipe_avec_statut,
        'stats': stats,
        'absences_equipe': list(absences_equipe),
    }

    return render(request, 'absence/manager_validation.html', context)


@login_required
@require_http_methods(["POST"])
def manager_valider_demande(request, demande_id):
    """Valider une demande en tant que manager"""
    employe = get_employe_from_user(request.user)

    # Vérifier que l'utilisateur est manager
    management = ZYMA.get_manager_actuel_employe(employe)
    if not management:
        return JsonResponse({
            'success': False,
            'error': 'Droits insuffisants'
        }, status=403)

    demande = get_object_or_404(ZDDA, id=demande_id)

    # Vérifier que l'employé de la demande fait partie du département du manager
    demandeur_dept = demande.employe.get_manager_responsable()
    if not demandeur_dept or demandeur_dept.departement != management.departement:
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne fait pas partie de votre département'
        }, status=403)

    if demande.statut != 'EN_ATTENTE':
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne peut plus être validée'
        }, status=400)

    commentaire = request.POST.get('commentaire', '').strip()

    try:
        with transaction.atomic():
            ancien_statut = demande.statut

            demande.statut = 'VALIDEE_MANAGER'
            demande.validee_manager = True
            demande.validateur_manager = employe
            demande.date_validation_manager = timezone.now()
            demande.commentaire_manager = commentaire
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='VALIDATION_MANAGER',
                utilisateur=employe,
                ancien_statut=ancien_statut,
                nouveau_statut='VALIDEE_MANAGER',
                commentaire=commentaire,
                request=request
            )

        return JsonResponse({
            'success': True,
            'message': f'✅ Demande validée avec succès.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def manager_refuser_demande(request, demande_id):
    """Refuser une demande en tant que manager"""
    employe = get_employe_from_user(request.user)

    # Vérifier que l'utilisateur est manager
    management = ZYMA.get_manager_actuel_employe(employe)
    if not management:
        return JsonResponse({
            'success': False,
            'error': 'Droits insuffisants'
        }, status=403)

    demande = get_object_or_404(ZDDA, id=demande_id)

    # Vérifier que l'employé de la demande fait partie du département du manager
    demandeur_dept = demande.employe.get_manager_responsable()
    if not demandeur_dept or demandeur_dept.departement != management.departement:
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne fait pas partie de votre département'
        }, status=403)

    if demande.statut != 'EN_ATTENTE':
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne peut plus être refusée'
        }, status=400)

    motif_refus = request.POST.get('motif_refus', '').strip()

    if not motif_refus:
        return JsonResponse({
            'success': False,
            'error': 'Le motif du refus est obligatoire'
        }, status=400)

    try:
        with transaction.atomic():
            ancien_statut = demande.statut

            demande.statut = 'REFUSEE_MANAGER'
            demande.validateur_manager = employe
            demande.date_validation_manager = timezone.now()
            demande.motif_refus_manager = motif_refus
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='REFUS_MANAGER',
                utilisateur=employe,
                ancien_statut=ancien_statut,
                nouveau_statut='REFUSEE_MANAGER',
                commentaire=motif_refus,
                request=request
            )

            # Mettre à jour le solde (restitution des jours)
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(demande.employe, demande.date_debut.year)

        return JsonResponse({
            'success': True,
            'message': f'❌ Demande refusée.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==========================================
# VUES RH
# ==========================================

@login_required
def rh_validation(request):
    """
    Page de validation finale pour le service RH
    Template: rh_validation.html
    """
    employe = get_employe_from_user(request.user)

    if not employe:
        messages.error(request, "Vous n'êtes pas associé à un employé.")
        return redirect('dashboard')

    # Vérifier si l'employé fait partie du service RH
    if not est_rh(employe):
        messages.error(request, "Vous n'avez pas les droits RH.")
        return redirect('absence:employe_demandes')

    # Récupérer toutes les demandes validées par les managers
    demandes_a_valider = ZDDA.objects.filter(
        statut='VALIDEE_MANAGER'
    ).select_related(
        'employe',
        'type_absence',
        'validateur_manager'
    ).order_by('-est_urgent', 'date_validation_manager')

    # Statistiques globales
    stats = {
        'validation_rh': demandes_a_valider.count(),
        'validees': ZDDA.objects.filter(statut='VALIDEE_RH').count(),
        'refusees': ZDDA.objects.filter(statut__in=['REFUSEE_MANAGER', 'REFUSEE_RH']).count(),
        'total': ZDDA.objects.count(),
        'absents_today': ZDDA.objects.filter(
            statut='VALIDEE_RH',
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        ).count(),
    }

    # Filtres
    filtre_departement = request.GET.get('departement', '')
    filtre_type = request.GET.get('type', '')

    if filtre_departement:
        postes_dept = ZDPO.objects.filter(DEPARTEMENT__id=filtre_departement)
        employes_dept = ZY00.objects.filter(
            affectations__poste__in=postes_dept,
            affectations__date_fin__isnull=True
        ).distinct()
        demandes_a_valider = demandes_a_valider.filter(employe__in=employes_dept)

    if filtre_type:
        demandes_a_valider = demandes_a_valider.filter(type_absence__id=filtre_type)

    # Départements pour le filtre
    departements = ZDDE.objects.filter(STATUT=True).order_by('LIBELLE')

    # Types d'absence pour le filtre
    types_absence = ZDAB.objects.filter(STATUT=True).order_by('CODE')

    context = {
        'employe': employe,
        'demandes_a_valider': demandes_a_valider,
        'stats': stats,
        'departements': departements,
        'types_absence': types_absence,
        'filtre_departement': filtre_departement,
        'filtre_type': filtre_type,
    }

    return render(request, 'absence/rh_validation.html', context)


@login_required
@require_http_methods(["POST"])
def rh_valider_demande(request, demande_id):
    """Validation finale RH d'une demande"""
    employe = get_employe_from_user(request.user)

    # Vérifier les droits RH
    if not est_rh(employe):
        return JsonResponse({
            'success': False,
            'error': 'Droits insuffisants'
        }, status=403)

    demande = get_object_or_404(ZDDA, id=demande_id)

    if demande.statut != 'VALIDEE_MANAGER':
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne peut plus être validée'
        }, status=400)

    commentaire_rh = request.POST.get('commentaire_rh', '').strip()

    try:
        with transaction.atomic():
            ancien_statut = demande.statut

            demande.statut = 'VALIDEE_RH'
            demande.validee_rh = True
            demande.validateur_rh = employe
            demande.date_validation_rh = timezone.now()
            demande.commentaire_rh = commentaire_rh
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='VALIDATION_RH',
                utilisateur=employe,
                ancien_statut=ancien_statut,
                nouveau_statut='VALIDEE_RH',
                commentaire=commentaire_rh,
                request=request
            )

            # Mettre à jour le solde
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(demande.employe, demande.date_debut.year)

        return JsonResponse({
            'success': True,
            'message': f'✅ Demande validée définitivement.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def rh_refuser_demande(request, demande_id):
    """Refus RH d'une demande"""
    employe = get_employe_from_user(request.user)

    # Vérifier les droits RH
    if not est_rh(employe):
        return JsonResponse({
            'success': False,
            'error': 'Droits insuffisants'
        }, status=403)

    demande = get_object_or_404(ZDDA, id=demande_id)

    if demande.statut != 'VALIDEE_MANAGER':
        return JsonResponse({
            'success': False,
            'error': 'Cette demande ne peut plus être refusée'
        }, status=400)

    motif_refus_rh = request.POST.get('motif_refus_rh', '').strip()

    if not motif_refus_rh:
        return JsonResponse({
            'success': False,
            'error': 'Le motif du refus est obligatoire'
        }, status=400)

    try:
        with transaction.atomic():
            ancien_statut = demande.statut

            demande.statut = 'REFUSEE_RH'
            demande.validateur_rh = employe
            demande.date_validation_rh = timezone.now()
            demande.motif_refus_rh = motif_refus_rh
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='REFUS_RH',
                utilisateur=employe,
                ancien_statut=ancien_statut,
                nouveau_statut='REFUSEE_RH',
                commentaire=motif_refus_rh,
                request=request
            )

            # Mettre à jour le solde (restitution des jours)
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(demande.employe, demande.date_debut.year)

        return JsonResponse({
            'success': True,
            'message': f'❌ Demande refusée par RH.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def rh_recherche_employe(request):
    """Recherche d'un employé et affichage de son historique"""
    employe = get_employe_from_user(request.user)

    if not est_rh(employe):
        messages.error(request, "Droits insuffisants.")
        return redirect('absence:employe_demandes')

    employe_recherche = None
    demandes = []
    solde = None

    employe_id = request.GET.get('employe_id')

    if employe_id:
        employe_recherche = get_object_or_404(ZY00, uuid=employe_id)
        demandes = ZDDA.objects.filter(employe=employe_recherche).order_by('-created_at')
        solde = ZDSO.get_or_create_solde(employe_recherche, timezone.now().year)

    # Liste de tous les employés pour le formulaire de recherche
    employes_list = ZY00.objects.filter(
        type_dossier='SAL',
        etat='actif'
    ).order_by('nom', 'prenoms')

    context = {
        'employe': employe,
        'employe_recherche': employe_recherche,
        'demandes': demandes,
        'solde': solde,
        'employes_list': employes_list,
    }

    return render(request, 'absence/rh_recherche_employe.html', context)


# ==========================================
# API POUR LES TEMPLATES
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_calculer_jours(request):
    """API pour calculer le nombre de jours ouvrés"""
    try:
        date_debut_str = request.GET.get('date_debut')
        date_fin_str = request.GET.get('date_fin')
        duree = request.GET.get('duree', 'COMPLETE')

        if not date_debut_str or not date_fin_str:
            return JsonResponse({'error': 'Dates manquantes'}, status=400)

        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()

        if duree == 'DEMI':
            nb_jours = 0.5
        else:
            nb_jours = float(calculer_jours_ouvres(date_debut, date_fin))

        return JsonResponse({
            'success': True,
            'nb_jours': nb_jours
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def api_demande_detail(request, demande_id):
    """API pour récupérer les détails d'une demande"""
    try:
        demande = get_object_or_404(ZDDA, id=demande_id)

        data = {
            'id': str(demande.id),
            'numero_demande': demande.numero_demande,
            'employe': {
                'matricule': demande.employe.matricule,
                'nom': demande.employe.nom,
                'prenoms': demande.employe.prenoms,
            },
            'type_absence': {
                'code': demande.type_absence.CODE,
                'libelle': demande.type_absence.LIBELLE,
            },
            'date_debut': demande.date_debut.strftime('%Y-%m-%d'),
            'date_fin': demande.date_fin.strftime('%Y-%m-%d'),
            'duree': demande.duree,
            'periode': demande.periode,
            'nombre_jours': float(demande.nombre_jours),
            'motif': demande.motif,
            'statut': demande.statut,
            'created_at': demande.created_at.strftime('%Y-%m-%d %H:%M'),
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def api_solde_employe(request):
    """API pour récupérer le solde d'un employé"""
    try:
        employe_id = request.GET.get('employe_id')
        annee = request.GET.get('annee', timezone.now().year)

        if not employe_id:
            return JsonResponse({'error': 'Employé non spécifié'}, status=400)

        employe = get_object_or_404(ZY00, uuid=employe_id)
        solde = ZDSO.get_or_create_solde(employe, int(annee))

        data = {
            'jours_acquis': float(solde.jours_acquis),
            'jours_pris': float(solde.jours_pris),
            'jours_en_attente': float(solde.jours_en_attente),
            'jours_disponibles': float(solde.jours_disponibles),
            'jours_reportes': float(solde.jours_reportes),
            'rtt_acquis': float(solde.rtt_acquis),
            'rtt_pris': float(solde.rtt_pris),
            'rtt_disponibles': float(solde.rtt_disponibles),
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==========================================
# MODIFICATION ET SUPPRESSION DE DEMANDES
# ==========================================

@login_required
def employe_modifier_demande(request, demande_id):
    """
    Modifier une demande d'absence (seulement si EN_ATTENTE)
    """
    employe = get_employe_from_user(request.user)
    demande = get_object_or_404(ZDDA, id=demande_id, employe=employe)

    # Vérifier que la demande est modifiable
    if demande.statut != 'EN_ATTENTE':
        messages.error(request, "❌ Seules les demandes en attente peuvent être modifiées.")
        return redirect('absence:employe_demandes')

    if request.method == 'POST':
        form = DemandeAbsenceForm(request.POST, request.FILES, instance=demande, employe=employe)

        if form.is_valid():
            demande_modifiee = form.save(commit=False)
            demande_modifiee.updated_by = employe
            demande_modifiee.save()

            # Créer l'historique
            creer_historique(
                demande=demande_modifiee,
                action='MODIFICATION',
                utilisateur=employe,
                commentaire='Demande modifiée par l\'employé',
                request=request
            )

            # Mettre à jour le solde si nécessaire
            if demande_modifiee.type_absence.CODE in ['CPN', 'RTT']:
                annee = demande_modifiee.date_debut.year
                mettre_a_jour_solde_conges(employe, annee)

            messages.success(request, f'✅ Votre demande {demande_modifiee.numero_demande} a été modifiée avec succès!')
            return redirect('absence:employe_demandes')
        else:
            messages.error(request, '❌ Erreur lors de la modification. Veuillez corriger les erreurs.')
    else:
        form = DemandeAbsenceForm(instance=demande, employe=employe)

    # Récupérer le solde
    annee_courante = timezone.now().year
    solde = ZDSO.get_or_create_solde(employe, annee_courante)

    # Récupérer toutes les demandes pour le contexte
    demandes = ZDDA.objects.filter(employe=employe).order_by('-created_at')

    # Préparer les données pour le calendrier (JSON sérialisable)
    demandes_pour_calendrier = []
    for demande_cal in demandes.filter(statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH', 'EN_ATTENTE']):
        demandes_pour_calendrier.append({
            'id': str(demande_cal.id),
            'date_debut': demande_cal.date_debut.isoformat(),
            'date_fin': demande_cal.date_fin.isoformat(),
            'statut': demande_cal.statut,
            'duree': demande_cal.duree,
            'type_absence': demande_cal.type_absence.LIBELLE,
        })

    context = {
        'employe': employe,
        'form': form,
        'demandes': demandes,
        'solde': solde,
        'demandes_calendrier': json.dumps(demandes_pour_calendrier),
        'annee_courante': annee_courante,
        'modification_mode': True,
        'demande_en_cours': demande,
    }

    return render(request, 'absence/employe_demandes.html', context)


@login_required
@require_http_methods(["POST"])
def employe_supprimer_demande(request, demande_id):
    """
    Supprimer une demande d'absence (seulement si EN_ATTENTE)
    """
    employe = get_employe_from_user(request.user)
    demande = get_object_or_404(ZDDA, id=demande_id, employe=employe)

    # Vérifier que la demande est supprimable
    if demande.statut != 'EN_ATTENTE':
        return JsonResponse({
            'success': False,
            'error': 'Seules les demandes en attente peuvent être supprimées.'
        }, status=400)

    try:
        with transaction.atomic():
            numero_demande = demande.numero_demande
            type_absence = demande.type_absence.CODE
            annee = demande.date_debut.year

            # Créer l'historique avant suppression
            creer_historique(
                demande=demande,
                action='SUPPRESSION',
                utilisateur=employe,
                commentaire='Demande supprimée par l\'employé',
                request=request
            )

            # Supprimer la demande
            demande.delete()

            # Mettre à jour le solde si c'était un congé
            if type_absence in ['CPN', 'RTT']:
                mettre_a_jour_solde_conges(employe, annee)

            return JsonResponse({
                'success': True,
                'message': f'La demande {numero_demande} a été supprimée avec succès.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
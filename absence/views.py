"""
Vues Django pour la gestion des congés et absences
Application: absence
Système HR_ONIAN
"""
from django.db import transaction
from datetime import datetime
import json
from django.shortcuts import  redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from .decorators import drh_required
from .models import ZDDA, ZDSO, ZDHA, calculer_jours_ouvres, mettre_a_jour_solde_conges
from .forms import (
    DemandeAbsenceForm, ValidationRHForm,
)
from employee.models import ZY00, ZYAF, ZYRE
from departement.models import ZYMA
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import ZANO





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
    Page principale de l'employé pour gérer ses demandes avec système d'onglets
    3 onglets : En cours, Validées, Refusées
    """
    employe = get_employe_from_user(request.user)

    if not employe:
        messages.error(request, "Vous n'êtes pas associé à un employé.")
        return redirect('dashboard')

    # Récupérer le paramètre d'onglet actif
    onglet_actif = request.GET.get('onglet', 'en_cours')

    # Récupérer le solde de l'année en cours
    annee_courante = timezone.now().year
    solde = ZDSO.get_or_create_solde(employe, annee_courante)

    # Récupérer toutes les demandes de l'employé
    toutes_demandes = ZDDA.objects.filter(employe=employe)

    # Séparer les demandes par onglet
    # Onglet 1 : En cours (EN_ATTENTE + VALIDEE_MANAGER)
    demandes_en_cours = toutes_demandes.filter(
        statut__in=['EN_ATTENTE', 'VALIDEE_MANAGER']
    ).order_by('-created_at')

    # Onglet 2 : Validées définitivement (VALIDEE_RH)
    demandes_validees = toutes_demandes.filter(
        statut='VALIDEE_RH'
    ).order_by('-date_validation_rh')

    # Onglet 3 : Refusées (REFUSEE_MANAGER + REFUSEE_RH + ANNULEE)
    demandes_refusees = toutes_demandes.filter(
        statut__in=['REFUSEE_MANAGER', 'REFUSEE_RH', 'ANNULEE']
    ).order_by('-created_at')

    # Compteurs pour les badges
    count_en_cours = demandes_en_cours.count()
    count_validees = demandes_validees.count()
    count_refusees = demandes_refusees.count()

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
            print("Erreur lors de la soumission. Veuillez corriger les erreurs.")
    else:
        form = DemandeAbsenceForm(employe=employe)

    # Préparer les données pour le calendrier (JSON sérialisable)
    demandes_pour_calendrier = []
    for demande in toutes_demandes.filter(statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH', 'EN_ATTENTE']):
        demandes_pour_calendrier.append({
            'id': str(demande.id),
            'date_debut': demande.date_debut.isoformat(),
            'date_fin': demande.date_fin.isoformat(),
            'statut': demande.statut,
            'duree': demande.duree,
            'type_absence': demande.type_absence.LIBELLE,
        })

    context = {
        'employe': employe,
        'form': form,

        # Demandes par onglet
        'demandes_en_cours': demandes_en_cours,
        'demandes_validees': demandes_validees,
        'demandes_refusees': demandes_refusees,

        # Compteurs
        'count_en_cours': count_en_cours,
        'count_validees': count_validees,
        'count_refusees': count_refusees,

        # Solde et autres
        'solde': solde,
        'demandes_calendrier': json.dumps(demandes_pour_calendrier),
        'annee_courante': annee_courante,
        'onglet_actif': onglet_actif,
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
    Page de validation pour les managers avec système d'onglets
    3 onglets : À valider, Validées, Refusées
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

    # ✅ FILTRES + ONGLET ACTIF
    filtre_employe = request.GET.get('employe', '')
    filtre_type = request.GET.get('type', '')
    onglet_actif = request.GET.get('onglet', 'a_valider')  # Par défaut : À valider

    # Récupérer tous les employés du département
    postes_dept = departement.postes.all()
    employes_dept = ZY00.objects.filter(
        affectations__poste__in=postes_dept,
        affectations__date_fin__isnull=True,
        type_dossier='SAL',
        etat='actif'
    ).distinct()

    # Base des demandes du département
    demandes_base = ZDDA.objects.filter(
        employe__in=employes_dept
    ).select_related('employe', 'type_absence', 'validateur_manager')

    # ✅ FONCTION POUR APPLIQUER LES FILTRES
    def appliquer_filtres(queryset):
        qs = queryset
        if filtre_employe:
            qs = qs.filter(
                Q(employe__matricule__icontains=filtre_employe) |
                Q(employe__nom__icontains=filtre_employe) |
                Q(employe__prenoms__icontains=filtre_employe)
            )
        if filtre_type:
            qs = qs.filter(type_absence_id=filtre_type)
        return qs

    # ✅ ONGLET 1 : À VALIDER (EN_ATTENTE)
    demandes_a_valider = appliquer_filtres(
        demandes_base.filter(statut='EN_ATTENTE')
    ).order_by('-est_urgent', '-created_at')

    # ✅ ONGLET 2 : VALIDÉES (VALIDEE_MANAGER + VALIDEE_RH)
    demandes_validees = appliquer_filtres(
        demandes_base.filter(statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH'])
    ).order_by('-date_validation_manager')

    # ✅ ONGLET 3 : REFUSÉES (REFUSEE_MANAGER)
    demandes_refusees = appliquer_filtres(
        demandes_base.filter(statut='REFUSEE_MANAGER')
    ).order_by('-date_validation_manager')

    # Compteurs pour les badges
    count_a_valider = demandes_a_valider.count()
    count_validees = demandes_validees.count()
    count_refusees = demandes_refusees.count()

    # Statistiques globales (sans filtre)
    toutes_demandes = ZDDA.objects.filter(employe__in=employes_dept)
    stats = {
        'en_attente': toutes_demandes.filter(statut='EN_ATTENTE').count(),
        'validees': toutes_demandes.filter(statut='VALIDEE_MANAGER').count(),
        'refusees': toutes_demandes.filter(statut='REFUSEE_MANAGER').count(),
        'equipe_total': employes_dept.count(),
    }

    # Récupérer les employés avec leur statut (présent/absent/congé)
    equipe_avec_statut = []
    today = timezone.now().date()

    for emp in employes_dept:
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

    # Préparer les données pour le calendrier
    absences_equipe = ZDDA.objects.filter(
        employe__in=employes_dept,
        statut__in=['VALIDEE_MANAGER', 'VALIDEE_RH']
    ).values('date_debut', 'date_fin', 'employe__nom', 'employe__prenoms')

    # ✅ DONNÉES POUR LES FILTRES
    from parametre.models import ZDAB
    types_absence = ZDAB.objects.filter(STATUT=True).order_by('LIBELLE')

    context = {
        'employe': employe,
        'management': management,
        'departement': departement,

        # ✅ DEMANDES PAR ONGLET
        'demandes_a_valider': demandes_a_valider,
        'demandes_validees': demandes_validees,
        'demandes_refusees': demandes_refusees,

        # ✅ COMPTEURS
        'count_a_valider': count_a_valider,
        'count_validees': count_validees,
        'count_refusees': count_refusees,

        'equipe_avec_statut': equipe_avec_statut,
        'stats': stats,
        'absences_equipe': list(absences_equipe),

        # ✅ FILTRES
        'types_absence': types_absence,
        'filtre_employe': filtre_employe,
        'filtre_type': filtre_type,

        # ✅ ONGLET ACTIF
        'onglet_actif': onglet_actif,
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
"""
Vue RH corrigée avec les bons noms de variables pour correspondre au template
À remplacer dans absence/views.py
"""

@login_required
@drh_required
def rh_validation(request):
    """
    Page de validation RH avec 5 onglets
    """
    # Filtres
    filtre_departement = request.GET.get('departement', '')
    filtre_type = request.GET.get('type', '')
    filtre_employe = request.GET.get('employe', '')
    onglet_actif = request.GET.get('onglet', 'a_valider_rh')

    # Base query
    demandes_base = ZDDA.objects.select_related(
        'employe', 'type_absence', 'validateur_manager', 'validateur_rh'
    ).prefetch_related('employe__affectations__poste__DEPARTEMENT')

    # Fonction filtres
    def appliquer_filtres(queryset):
        qs = queryset
        if filtre_departement:
            qs = qs.filter(
                employe__affectations__poste__DEPARTEMENT_id=filtre_departement,
                employe__affectations__actif=True
            )
        if filtre_type:
            qs = qs.filter(type_absence_id=filtre_type)
        if filtre_employe:
            qs = qs.filter(
                Q(employe__matricule__icontains=filtre_employe) |
                Q(employe__nom__icontains=filtre_employe) |
                Q(employe__prenoms__icontains=filtre_employe)
            )
        return qs

    # Demandes par onglet
    demandes_a_valider_rh = appliquer_filtres(
        demandes_base.filter(statut='VALIDEE_MANAGER')
    ).order_by('-est_urgent', '-created_at')

    demandes_en_attente = appliquer_filtres(
        demandes_base.filter(statut='EN_ATTENTE')
    ).order_by('-est_urgent', '-created_at')

    demandes_validees_rh = appliquer_filtres(
        demandes_base.filter(statut='VALIDEE_RH')
    ).order_by('-date_validation_rh')

    demandes_refusees_manager = appliquer_filtres(
        demandes_base.filter(statut='REFUSEE_MANAGER')
    ).order_by('-date_validation_manager')

    demandes_refusees_rh = appliquer_filtres(
        demandes_base.filter(statut='REFUSEE_RH')
    ).order_by('-date_validation_rh')

    # Calculer soldes
    from datetime import date
    annee_courante = date.today().year

    def ajouter_soldes(demandes_qs):
        soldes_employes = {}
        result = []
        for demande in demandes_qs:
            emp_id = demande.employe.pk
            if emp_id not in soldes_employes:
                solde = ZDSO.get_or_create_solde(demande.employe, annee_courante)
                soldes_employes[emp_id] = {
                    'jours_disponibles': solde.jours_disponibles,
                    'rtt_disponibles': solde.rtt_disponibles,
                    'jours_pris': solde.jours_pris,
                    'jours_en_attente': solde.jours_en_attente,
                }
            result.append({'demande': demande, 'solde': soldes_employes[emp_id]})
        return result

    demandes_a_valider_rh_avec_solde = ajouter_soldes(demandes_a_valider_rh)
    demandes_en_attente_avec_solde = ajouter_soldes(demandes_en_attente)

    # Données filtres
    from departement.models import ZDDE
    from parametre.models import ZDAB

    departements = ZDDE.objects.all().order_by('LIBELLE')
    types_absence = ZDAB.objects.filter(STATUT=True).order_by('LIBELLE')

    # Stats
    today = date.today()
    toutes = ZDDA.objects.all()

    stats = {
        'validation_rh': demandes_a_valider_rh.count(),
        'en_attente_manager': demandes_en_attente.count(),
        'validees': demandes_validees_rh.count(),
        'refusees_manager': demandes_refusees_manager.count(),
        'refusees_rh': demandes_refusees_rh.count(),
        'refusees': demandes_refusees_manager.count() + demandes_refusees_rh.count(),
        'total': toutes.count(),
        'absents_today': toutes.filter(
            statut='VALIDEE_RH', date_debut__lte=today, date_fin__gte=today
        ).count(),
    }

    context = {
        # ✅ CORRECTION : Utiliser les bons noms pour le template
        'demandes_a_valider_rh': demandes_a_valider_rh_avec_solde,
        'demandes_en_attente': demandes_en_attente_avec_solde,
        'demandes_validees_rh': demandes_validees_rh,  # ✅ BON NOM
        'demandes_refusees_manager': demandes_refusees_manager,  # ✅ BON NOM
        'demandes_refusees_rh': demandes_refusees_rh,  # ✅ BON NOM

        # Compteurs
        'count_a_valider_rh': demandes_a_valider_rh.count(),
        'count_en_attente': demandes_en_attente.count(),
        'count_validees_rh': demandes_validees_rh.count(),
        'count_refusees_manager': demandes_refusees_manager.count(),
        'count_refusees_rh': demandes_refusees_rh.count(),

        # Filtres
        'departements': departements,
        'types_absence': types_absence,
        'filtre_departement': filtre_departement,
        'filtre_type': filtre_type,
        'filtre_employe': filtre_employe,
        'onglet_actif': onglet_actif,
        'stats': stats,
        'annee_courante': annee_courante,
    }

    return render(request, 'absence/rh_validation.html', context)

@login_required
@drh_required
@require_http_methods(["GET"])
def rh_recherche_employe_ajax(request):
    """
    API AJAX pour l'autocomplete de recherche d'employés
    Recherche par matricule, nom ou prénom
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Rechercher dans matricule, nom et prénom
    employes = ZY00.objects.filter(
        Q(matricule__icontains=query) |
        Q(nom__icontains=query) |
        Q(prenoms__icontains=query),
        type_dossier='SAL',
        etat='actif'
    ).values(
        'pk',
        'matricule',
        'nom',
        'prenoms'
    )[:10]  # Limiter à 10 résultats

    results = [
        {
            'id': emp['pk'],
            'text': f"{emp['nom']} {emp['prenoms']} ({emp['matricule']})",
            'matricule': emp['matricule'],
            'nom': emp['nom'],
            'prenoms': emp['prenoms']
        }
        for emp in employes
    ]

    return JsonResponse({'results': results})


@login_required
@drh_required
@require_http_methods(["POST"])
def rh_valider_demande(request, demande_id):
    """
    Valider une demande d'absence (RH) - Version AJAX
    """
    employe = request.user.employe
    demande = get_object_or_404(ZDDA, id=demande_id, statut='VALIDEE_MANAGER')

    commentaire_rh = request.POST.get('commentaire_rh', '').strip()

    try:
        with transaction.atomic():
            # Valider la demande
            demande.statut = 'VALIDEE_RH'
            demande.validee_rh = True
            demande.date_validation_rh = timezone.now()
            demande.validateur_rh = employe
            demande.commentaire_rh = commentaire_rh
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='VALIDATION_RH',
                utilisateur=employe,
                ancien_statut='VALIDEE_MANAGER',
                nouveau_statut='VALIDEE_RH',
                commentaire=commentaire_rh,
                request=request
            )

            # Mettre à jour le solde si nécessaire
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                annee = demande.date_debut.year
                solde = ZDSO.get_or_create_solde(demande.employe, annee)

                # Déduire du solde
                solde.jours_pris += demande.nombre_jours
                solde.jours_en_attente -= demande.nombre_jours
                solde.calculer_soldes()

            return JsonResponse({
                'success': True,
                'message': f'✅ La demande {demande.numero_demande} a été validée par RH.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@drh_required
@require_http_methods(["POST"])
def rh_refuser_demande(request, demande_id):
    """
    Refuser une demande d'absence (RH) - Version AJAX
    """
    employe = request.user.employe
    demande = get_object_or_404(ZDDA, id=demande_id, statut='VALIDEE_MANAGER')

    motif_refus_rh = request.POST.get('motif_refus_rh', '').strip()

    if not motif_refus_rh:
        return JsonResponse({
            'success': False,
            'error': 'Le motif du refus est obligatoire'
        }, status=400)

    try:
        with transaction.atomic():
            # Refuser la demande
            demande.statut = 'REFUSEE_RH'
            demande.date_validation_rh = timezone.now()
            demande.validateur_rh = employe
            demande.motif_refus_rh = motif_refus_rh
            demande.updated_by = employe
            demande.save()

            # Créer l'historique
            creer_historique(
                demande=demande,
                action='REFUS_RH',
                utilisateur=employe,
                ancien_statut='VALIDEE_MANAGER',
                nouveau_statut='REFUSEE_RH',
                commentaire=motif_refus_rh,
                request=request
            )

            # Restituer le solde si nécessaire
            if demande.type_absence.CODE in ['CPN', 'RTT']:
                annee = demande.date_debut.year
                solde = ZDSO.get_or_create_solde(demande.employe, annee)

                # Restituer le solde
                solde.jours_en_attente -= demande.nombre_jours
                solde.calculer_soldes()

            return JsonResponse({
                'success': True,
                'message': f'❌ La demande {demande.numero_demande} a été refusée par RH.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@drh_required
def rh_liste_complete(request):
    """
    Liste complète de toutes les demandes (pour RH)
    """
    # Filtres
    statut = request.GET.get('statut', '')
    type_absence = request.GET.get('type_absence', '')

    demandes = ZDDA.objects.all().select_related('employe', 'type_absence')

    if statut:
        demandes = demandes.filter(statut=statut)

    if type_absence:
        demandes = demandes.filter(type_absence__CODE=type_absence)

    demandes = demandes.order_by('-created_at')

    # Statistiques
    stats = {
        'total': demandes.count(),
        'en_attente': demandes.filter(statut='EN_ATTENTE').count(),
        'validees_manager': demandes.filter(statut='VALIDEE_MANAGER').count(),
        'validees_rh': demandes.filter(statut='VALIDEE_RH').count(),
        'refusees': demandes.filter(statut__in=['REFUSEE_MANAGER', 'REFUSEE_RH']).count(),
    }

    context = {
        'demandes': demandes,
        'stats': stats,
        'statut_filter': statut,
        'type_filter': type_absence,
    }

    return render(request, 'absence/rh_liste_complete.html', context)

@login_required
@drh_required
def rh_recherche_employe(request):
    """Recherche d'un employé et affichage de son historique"""
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
        'employe_recherche': employe_recherche,
        'demandes': demandes,
        'solde': solde,
        'employes_list': employes_list,
    }

    return render(request, 'absence/rh_recherche_employe.html', context)

@drh_required
@login_required
def rh_liste_complete(request):
    """
    Liste complète de toutes les demandes (pour RH)
    """
    # Filtres
    statut = request.GET.get('statut', '')
    type_absence = request.GET.get('type_absence', '')

    demandes = ZDDA.objects.all().select_related('employe', 'type_absence')

    if statut:
        demandes = demandes.filter(statut=statut)

    if type_absence:
        demandes = demandes.filter(type_absence__CODE=type_absence)

    demandes = demandes.order_by('-created_at')

    # Statistiques
    from django.db.models import Count, Sum
    stats = {
        'total': demandes.count(),
        'en_attente': demandes.filter(statut='EN_ATTENTE').count(),
        'validees_manager': demandes.filter(statut='VALIDEE_MANAGER').count(),
        'validees_rh': demandes.filter(statut='VALIDEE_RH').count(),
        'refusees': demandes.filter(statut__in=['REFUSEE_MANAGER', 'REFUSEE_RH']).count(),
    }

    context = {
        'demandes': demandes,
        'stats': stats,
        'statut_filter': statut,
        'type_filter': type_absence,
    }

    return render(request, 'absence/rh_liste_complete.html', context)



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



# ==========================================
# VUES NOTIFICATIONS
# ==========================================

@login_required
@require_POST
@login_required
@require_POST
def marquer_notification_lue(request, notification_id):
    """Marquer une notification comme lue"""
    try:
        print(f"🔍 Notification ID reçu: {notification_id} (type: {type(notification_id)})")

        notification = get_object_or_404(
            ZANO,
            id=notification_id,  # ✅ Directement l'entier, pas de conversion UUID
            destinataire=request.user.employe
        )

        print(f"✅ Notification trouvée: {notification.titre}")

        notification.marquer_comme_lue()

        return JsonResponse({
            'success': True,
            'message': 'Notification marquée comme lue'
        })
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def marquer_toutes_lues(request):
    """Marquer toutes les notifications comme lues"""
    try:
        from django.utils import timezone

        notifications = ZANO.objects.filter(
            destinataire=request.user.employe,
            lue=False
        )

        count = notifications.update(
            lue=True,
            date_lecture=timezone.now()
        )

        return JsonResponse({
            'success': True,
            'message': f'{count} notification(s) marquée(s) comme lue(s)',
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def liste_notifications(request):
    """Page listant toutes les notifications"""
    try:
        notifications = ZANO.objects.filter(
            destinataire=request.user.employe
        ).select_related('demande_absence', 'demande_absence__type_absence').order_by('-date_creation')

        # Pagination
        paginator = Paginator(notifications, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Statistiques
        nb_non_lues = ZANO.objects.filter(
            destinataire=request.user.employe,
            lue=False
        ).count()

        context = {
            'notifications': page_obj,
            'nb_non_lues': nb_non_lues,
            'page_obj': page_obj,
        }

        return render(request, 'absence/liste_notifications.html', context)
    except Exception as e:
        print(f"Erreur liste notifications: {e}")
        return render(request, 'absence/liste_notifications.html', {
            'notifications': [],
            'nb_non_lues': 0,
        })


@login_required
def get_notifications_json(request):
    """API pour récupérer les notifications en JSON"""
    try:
        limit = int(request.GET.get('limit', 10))

        notifications = ZANO.objects.filter(
            destinataire=request.user.employe,
            lue=False
        ).select_related('demande_absence', 'demande_absence__type_absence')[:limit]

        data = []
        for notif in notifications:
            data.append({
                'id': str(notif.id),
                'titre': notif.titre,
                'message': notif.message,
                'type': notif.type_notification,
                'lien': notif.lien or '#',
                'date_creation': notif.date_creation.strftime('%d/%m/%Y %H:%M'),
                'lue': notif.lue,
                'demande': {
                    'numero': notif.demande_absence.numero_demande if notif.demande_absence else '',
                    'date_debut': notif.demande_absence.date_debut.strftime(
                        '%d/%m/%Y') if notif.demande_absence else '',
                    'date_fin': notif.demande_absence.date_fin.strftime('%d/%m/%Y') if notif.demande_absence else '',
                    'nombre_jours': float(notif.demande_absence.nombre_jours) if notif.demande_absence else 0,
                } if notif.demande_absence else None
            })

        return JsonResponse({
            'success': True,
            'notifications': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
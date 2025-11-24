from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from datetime import datetime
from employee.models import ZYAF, ZY00
from .models import ZDDE, ZDPO, ZYMA
from .forms import ZDDEForm, ZDPOForm
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required  # ← AJOUT IMPORT

@login_required
def department_list(request):
    """Vue principale pour afficher et gérer les départements"""
    departments = ZDDE.objects.all().order_by('CODE')

    # Gérer la soumission du formulaire (création)
    if request.method == 'POST':
        form = ZDDEForm(request.POST)

        if form.is_valid():
            department = form.save()
            #messages.success(request, f'✓ Département {department.CODE} créé avec succès!')
            return redirect('list')
        else:
            #messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
            print("Erreur de validation. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ZDDEForm()

    return render(request, 'departement/departement.html', {
        'departments': departments,
        'form': form,
        'editing': False
    })

@login_required
def department_edit(request, pk):
    """Éditer un département existant"""
    department = get_object_or_404(ZDDE, pk=pk)
    departments = ZDDE.objects.all().order_by('CODE')

    if request.method == 'POST':
        form = ZDDEForm(request.POST, instance=department)

        if form.is_valid():
            department = form.save()
            #messages.success(request, f'✓ Département {department.CODE} modifié avec succès!')
            return redirect('list')
        else:
            #messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
            print("Erreur de validation. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ZDDEForm(instance=department)

    return render(request, 'departement/departement.html', {
        'departments': departments,
        'form': form,
        'editing': True,
        'department_id': pk
    })

@login_required
def department_delete(request, pk):
    """Supprimer un département"""
    if request.method == 'POST':
        department = get_object_or_404(ZDDE, pk=pk)
        code = department.CODE
        department.delete()
        #messages.success(request, f'✓ Département {code} supprimé avec succès!')

    return redirect('list')


# ==========================================
# VUES POSTE (ZDPO)
# ==========================================
@login_required
def poste_list(request):
    """Vue principale pour afficher et gérer les postes"""
    postes = ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE')

    if request.method == 'POST':
        form = ZDPOForm(request.POST)

        if form.is_valid():
            poste = form.save()
            #messages.success(request, f'✓ Poste {poste.CODE} créé avec succès!')
            return redirect('poste_list')
        else:
            #messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
            print("Erreur de validation. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ZDPOForm()

    return render(request, 'departement/poste.html', {
        'postes': postes,
        'form': form,
        'editing': False
    })

@login_required
def poste_edit(request, pk):
    """Éditer un poste existant"""
    poste = get_object_or_404(ZDPO, pk=pk)
    postes = ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE')

    if request.method == 'POST':
        form = ZDPOForm(request.POST, instance=poste)

        if form.is_valid():
            poste = form.save()
            #messages.success(request, f'✓ Poste {poste.CODE} modifié avec succès!')
            return redirect('poste_list')
        else:
            #messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
            print("Erreur de validation. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ZDPOForm(instance=poste)

    return render(request, 'departement/poste.html', {
        'postes': postes,
        'form': form,
        'editing': True,
        'poste_id': pk
    })

@login_required
def poste_delete(request, pk):
    """Supprimer un poste"""
    if request.method == 'POST':
        poste = get_object_or_404(ZDPO, pk=pk)
        code = poste.CODE
        poste.delete()
        #messages.success(request, f'✓ Poste {code} supprimé avec succès!')

    return redirect('poste_list')

# ==========================================
# VUES managers (ZYMA)
# ==========================================
@login_required
def liste_managers(request):
    """Page principale de gestion des managers"""
    managers = ZYMA.objects.all().select_related('departement', 'employe').order_by('-date_debut')
    departements_sans_manager = ZYMA.get_departements_sans_manager()

    context = {
        'managers': managers,
        'departements_sans_manager': departements_sans_manager,
        'departements': ZDDE.objects.filter(STATUT=True),
        'employes_eligibles': ZY00.objects.filter(type_dossier='SAL', etat='actif'),
    }
    return render(request, 'departement/liste_managers.html', context)


@require_http_methods(["GET"])
@login_required
def api_manager_detail(request, id):
    """Récupérer les détails d'un manager"""
    try:
        manager = get_object_or_404(ZYMA, id=id)
        data = {
            'id': manager.id,
            'departement': manager.departement.id,
            'departement_libelle': manager.departement.LIBELLE,
            'employe': manager.employe.uuid,
            'employe_nom_complet': f"{manager.employe.nom} {manager.employe.prenoms}",
            'employe_matricule': manager.employe.matricule,
            'date_debut': manager.date_debut.strftime('%Y-%m-%d'),
            'date_fin': manager.date_fin.strftime('%Y-%m-%d') if manager.date_fin else '',
            'actif': manager.actif,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_manager_create_modal(request):
    """Créer un manager via modal"""
    try:
        # Validation
        errors = {}
        required_fields = ['departement', 'employe', 'date_debut']
        for field in required_fields:
            if not request.POST.get(field):
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        departement = get_object_or_404(ZDDE, id=request.POST.get('departement'))
        employe = get_object_or_404(ZY00, uuid=request.POST.get('employe'))
        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Validations supplémentaires
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        # Vérifier que l'employé est un salarié
        if employe.type_dossier != 'SAL':
            errors['employe'] = ['Seuls les employés salariés peuvent être désignés comme managers']
            return JsonResponse({'errors': errors}, status=400)

        # Créer le manager
        with transaction.atomic():
            manager = ZYMA.objects.create(
                departement=departement,
                employe=employe,
                date_debut=date_debut_obj,
                date_fin=date_fin_obj,
            )

        return JsonResponse({
            'success': True,
            'message': '✅ Manager ajouté avec succès',
            'id': manager.id
        })
    except ValidationError as e:
        return JsonResponse({'errors': e.message_dict}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_manager_update_modal(request, id):
    """Mettre à jour un manager via modal"""
    try:
        manager = get_object_or_404(ZYMA, id=id)

        # Validation
        errors = {}
        required_fields = ['departement', 'employe', 'date_debut']
        for field in required_fields:
            if not request.POST.get(field):
                errors[field] = ['Ce champ est requis']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        # Préparation des données
        departement = get_object_or_404(ZDDE, id=request.POST.get('departement'))
        employe = get_object_or_404(ZY00, uuid=request.POST.get('employe'))
        date_debut_obj = datetime.strptime(request.POST.get('date_debut'), '%Y-%m-%d').date()
        date_fin = request.POST.get('date_fin')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date() if date_fin else None

        # Validations
        if date_fin_obj and date_fin_obj <= date_debut_obj:
            errors['date_fin'] = ['La date de fin doit être supérieure à la date de début']
            return JsonResponse({'errors': errors}, status=400)

        if employe.type_dossier != 'SAL':
            errors['employe'] = ['Seuls les employés salariés peuvent être désignés comme managers']
            return JsonResponse({'errors': errors}, status=400)

        # Mettre à jour
        with transaction.atomic():
            manager.departement = departement
            manager.employe = employe
            manager.date_debut = date_debut_obj
            manager.date_fin = date_fin_obj
            manager.save()

        return JsonResponse({
            'success': True,
            'message': '✅ Manager modifié avec succès'
        })
    except ValidationError as e:
        return JsonResponse({'errors': e.message_dict}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def api_manager_delete_modal(request, id):
    """Supprimer un manager via modal"""
    try:
        manager = get_object_or_404(ZYMA, id=id)
        with transaction.atomic():
            manager.delete()

        return JsonResponse({
            'success': True,
            'message': '✅ Manager supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_managers_by_departement(request, departement_id):
    """Récupérer les managers d'un département"""
    try:
        departement = get_object_or_404(ZDDE, id=departement_id)
        managers = ZYMA.objects.filter(departement=departement).order_by('-date_debut')

        data = [
            {
                'id': manager.id,
                'employe_nom': f"{manager.employe.nom} {manager.employe.prenoms}",
                'employe_matricule': manager.employe.matricule,
                'date_debut': manager.date_debut.strftime('%d/%m/%Y'),
                'date_fin': manager.date_fin.strftime('%d/%m/%Y') if manager.date_fin else 'En cours',
                'actif': manager.actif,
            }
            for manager in managers
        ]

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def get_manager_employe(employe):
    """Retourne le manager d'un employé basé sur son département d'affectation"""
    try:
        # Récupérer l'affectation active de l'employé
        affectation_active = ZYAF.objects.filter(
            employe=employe,
            date_fin__isnull=True
        ).first()

        if affectation_active:
            # Récupérer le manager du département de l'affectation
            manager = ZYMA.get_manager_actif(affectation_active.poste.DEPARTEMENT)
            return manager
        return None
    except Exception:
        return None
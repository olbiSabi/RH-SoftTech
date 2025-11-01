from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ZDDE, ZDPO
from .forms import ZDDEForm, ZDPOForm


def department_list(request):
    """Vue principale pour afficher et gérer les départements"""
    departments = ZDDE.objects.all().order_by('CODE')

    # Gérer la soumission du formulaire (création)
    if request.method == 'POST':
        form = ZDDEForm(request.POST)

        if form.is_valid():
            department = form.save()
            messages.success(request, f'✓ Département {department.CODE} créé avec succès!')
            return redirect('list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDDEForm()

    return render(request, 'departement/departement.html', {
        'departments': departments,
        'form': form,
        'editing': False
    })


def department_edit(request, pk):
    """Éditer un département existant"""
    department = get_object_or_404(ZDDE, pk=pk)
    departments = ZDDE.objects.all().order_by('CODE')

    if request.method == 'POST':
        form = ZDDEForm(request.POST, instance=department)

        if form.is_valid():
            department = form.save()
            messages.success(request, f'✓ Département {department.CODE} modifié avec succès!')
            return redirect('list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDDEForm(instance=department)

    return render(request, 'departement/departement.html', {
        'departments': departments,
        'form': form,
        'editing': True,
        'department_id': pk
    })


def department_delete(request, pk):
    """Supprimer un département"""
    if request.method == 'POST':
        department = get_object_or_404(ZDDE, pk=pk)
        code = department.CODE
        department.delete()
        messages.success(request, f'✓ Département {code} supprimé avec succès!')

    return redirect('list')


# ==========================================
# VUES POSTE (ZDPO)
# ==========================================

def poste_list(request):
    """Vue principale pour afficher et gérer les postes"""
    postes = ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE')

    if request.method == 'POST':
        form = ZDPOForm(request.POST)

        if form.is_valid():
            poste = form.save()
            messages.success(request, f'✓ Poste {poste.CODE} créé avec succès!')
            return redirect('poste_list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDPOForm()

    return render(request, 'departement/poste.html', {
        'postes': postes,
        'form': form,
        'editing': False
    })


def poste_edit(request, pk):
    """Éditer un poste existant"""
    poste = get_object_or_404(ZDPO, pk=pk)
    postes = ZDPO.objects.select_related('DEPARTEMENT').all().order_by('CODE')

    if request.method == 'POST':
        form = ZDPOForm(request.POST, instance=poste)

        if form.is_valid():
            poste = form.save()
            messages.success(request, f'✓ Poste {poste.CODE} modifié avec succès!')
            return redirect('poste_list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDPOForm(instance=poste)

    return render(request, 'departement/poste.html', {
        'postes': postes,
        'form': form,
        'editing': True,
        'poste_id': pk
    })


def poste_delete(request, pk):
    """Supprimer un poste"""
    if request.method == 'POST':
        poste = get_object_or_404(ZDPO, pk=pk)
        code = poste.CODE
        poste.delete()
        messages.success(request, f'✓ Poste {code} supprimé avec succès!')

    return redirect('poste_list')

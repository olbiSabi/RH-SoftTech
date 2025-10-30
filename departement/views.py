
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ZDDE
from .forms import ZDDEForm
from datetime import date

DATE_MAX = date(2999, 12, 31)


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
        'date_max': DATE_MAX,
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
        'date_max': DATE_MAX,
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

def poste(request):
    return render(request, "departement/poste.html")
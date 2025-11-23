from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # ← AJOUT IMPORT
from .models import ZDAB
from .forms import ZDABForm

# ==========================================
# VUES code Absence(ZDAB)
# ==========================================
@login_required
def absence_list(request):
    """Vue principale pour afficher et gérer les absence"""
    absences = ZDAB.objects.all().order_by('CODE')

    # Gérer la soumission du formulaire (création)
    if request.method == 'POST':
        form = ZDABForm(request.POST)

        if form.is_valid():
            absence = form.save()
            messages.success(request, f'✓ Absence {absence.CODE} créé avec succès!')
            return redirect('absence_list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDABForm()

    return render(request, 'parametre/type-conge.html', {
        'absences': absences,
        'form': form,
        'editing': False
    })

@login_required
def absence_edit(request, pk):
    """Éditer un absence existant"""
    absence = get_object_or_404(ZDAB, pk=pk )
    absences = ZDAB.objects.all().order_by('CODE')

    if request.method == 'POST':
        form = ZDABForm(request.POST, instance=absence)

        if form.is_valid():
            absence = form.save()
            messages.success(request, f'✓ Absence {absence.CODE} modifié avec succès!')
            return redirect('absence_list')
        else:
            messages.error(request, '✗ Erreur de validation. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ZDABForm(instance=absence)

    return render(request, 'parametre/type-conge.html', {
        'absences': absences,
        'form': form,
        'editing': True,
        'absence_id': pk
    })

@login_required
def absence_delete(request, pk):
    """Supprimer un absence"""
    if request.method == 'POST':
        absence = get_object_or_404(ZDAB, pk=pk)
        code = absence.CODE
        absence.delete()
        messages.success(request, f'✓ Absence {code} supprimé avec succès!')

    return redirect('absence_list')


# ==========================================
# VUES POSTE (ZDPO)
# ==========================================
@login_required
def parametreHome(request):
    return render(request, "parametre/parametre-home.html")

@login_required
def parametreTheme(request):
    return render(request, "parametre/parametre-theme.html")

@login_required
def parametreFacturation(request):
    return render(request, "parametre/parametre-factuation.html")

@login_required
def parametreSalariaux(request):
    return render(request, "parametre/parametre-salariaux.html")

@login_required
def changePassword(request):
    return render(request, "parametre/change-password.html")

@login_required
def loginUser(request):
    return render(request, "parametre/login.html")

@login_required
def forgetPassword(request):
    return render(request, "parametre/password-forget.html")
# Create your views here.

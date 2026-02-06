"""
Vues pour la gestion des paramètres du module GAC.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from gestion_achats.models import GACParametres
from gestion_achats.forms import GACParametresForm
from gestion_achats.permissions import require_permission, GACPermissions


@login_required
def parametres_gac(request):
    """
    Affiche et permet de modifier les paramètres de configuration GAC.

    Accessible uniquement aux utilisateurs ayant le rôle ADMIN_GAC.
    """
    # Vérifier les permissions
    require_permission(
        lambda user: user.employe.has_role('ADMIN_GAC'),
        request.user
    )

    # Récupérer les paramètres existants
    parametres = GACParametres.get_parametres()

    if request.method == 'POST':
        form = GACParametresForm(request.POST, instance=parametres)

        if form.is_valid():
            # Sauvegarder les paramètres
            parametres = form.save(commit=False)
            parametres.modifie_par = request.user.employe
            parametres.save()

            messages.success(
                request,
                'Les paramètres ont été mis à jour avec succès.'
            )

            return redirect('gestion_achats:parametres_gac')
        else:
            messages.error(
                request,
                'Erreur lors de la mise à jour des paramètres. Veuillez vérifier les données saisies.'
            )
    else:
        form = GACParametresForm(instance=parametres)

    context = {
        'form': form,
        'parametres': parametres,
    }

    return render(request, 'gestion_achats/parametres/parametres.html', context)

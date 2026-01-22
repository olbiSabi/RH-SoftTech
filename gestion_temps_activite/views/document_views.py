# gestion_temps_activite/views/document_views.py
"""Vues pour la gestion des documents (ZDDO)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from gestion_temps_activite.models import ZDPJ, ZDTA, ZDDO
from gestion_temps_activite.forms import ZDDOForm


@login_required
def document_upload(request):
    """Upload d'un document."""
    if request.method == 'POST':
        form = ZDDOForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            if hasattr(request.user, 'employe'):
                document.uploade_par = request.user.employe
            document.save()

            messages.success(request, 'Document ajouté avec succès.')

            # Redirection conditionnelle
            if document.projet:
                return redirect('gestion_temps_activite:projet_detail', pk=document.projet.pk)
            elif document.tache:
                return redirect('gestion_temps_activite:tache_detail', pk=document.tache.pk)
            else:
                return redirect('gestion_temps_activite:dashboard')
        else:
            messages.error(request, 'Erreur lors de l\'upload du document.')
    else:
        projet_id = request.GET.get('projet')
        tache_id = request.GET.get('tache')

        initial = {}
        if projet_id:
            initial['type_rattachement'] = 'PROJET'
            initial['projet'] = projet_id
        elif tache_id:
            initial['type_rattachement'] = 'TACHE'
            initial['tache'] = tache_id

        form = ZDDOForm(initial=initial)

    context = {
        'form': form,
        'title': 'Upload Document'
    }

    return render(request, 'gestion_temps_activite/document_form.html', context)


@login_required
def document_delete(request, pk):
    """Supprimer un document."""
    document = get_object_or_404(ZDDO, pk=pk)

    # Déterminer la redirection
    redirect_url = 'gestion_temps_activite:dashboard'
    if document.projet:
        redirect_url = redirect('gestion_temps_activite:projet_detail', pk=document.projet.pk)
    elif document.tache:
        redirect_url = redirect('gestion_temps_activite:tache_detail', pk=document.tache.pk)

    if request.method == 'POST':
        try:
            document.fichier.delete()
            document.delete()
            messages.success(request, 'Document supprimé avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')

        if document.projet:
            return redirect('gestion_temps_activite:projet_detail', pk=document.projet.pk)
        elif document.tache:
            return redirect('gestion_temps_activite:tache_detail', pk=document.tache.pk)
        else:
            return redirect('gestion_temps_activite:dashboard')

    context = {
        'document': document
    }

    return render(request, 'gestion_temps_activite/document_confirm_delete.html', context)

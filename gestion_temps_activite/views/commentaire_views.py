# gestion_temps_activite/views/commentaire_views.py
"""Vues pour la gestion des commentaires (ZDCM)."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

from employee.models import ZY00
from gestion_temps_activite.models import ZDTA, ZDCM
from gestion_temps_activite.forms import ZDCMForm
from gestion_temps_activite.services import CommentaireService
from gestion_temps_activite.views.notification_views import notifier_nouveau_commentaire


@login_required
def commentaire_ajouter(request, tache_pk):
    """Ajouter un commentaire à une tâche."""
    tache = get_object_or_404(ZDTA, pk=tache_pk)

    if not hasattr(request.user, 'employe'):
        messages.error(request, "Vous devez avoir un profil employé.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    employe = request.user.employe

    # Vérifier les permissions
    if not CommentaireService.peut_ajouter_commentaire(employe, tache):
        messages.error(request, "Vous n'avez pas la permission d'ajouter des commentaires.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    if request.method == 'POST':
        form = ZDCMForm(request.POST, tache=tache, employe=employe)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.tache = tache
            commentaire.employe = employe
            commentaire.save()

            # Traiter les mentions
            employes_mentionnes = CommentaireService.trouver_employes_mentionnes(
                commentaire.contenu, exclude_employe=employe
            )
            if employes_mentionnes.exists():
                commentaire.mentions.set(employes_mentionnes)

            # Notification
            notifier_nouveau_commentaire(commentaire, employe)

            messages.success(request, "Commentaire ajouté avec succès.")
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)


@login_required
def commentaire_repondre(request, commentaire_pk):
    """Répondre à un commentaire."""
    parent = get_object_or_404(ZDCM, pk=commentaire_pk)
    tache = parent.tache

    if not hasattr(request.user, 'employe'):
        messages.error(request, "Vous devez avoir un profil employé.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)

    employe = request.user.employe

    # Vérifier les permissions
    if not CommentaireService.peut_ajouter_commentaire(employe, tache):
        messages.error(request, "Vous n'avez pas la permission de répondre.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)

    if request.method == 'POST':
        form = ZDCMForm(request.POST, tache=tache, employe=employe, parent=parent)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.tache = tache
            reponse.employe = employe
            reponse.reponse_a = parent
            reponse.save()

            # Traiter les mentions
            employes_mentionnes = CommentaireService.trouver_employes_mentionnes(
                reponse.contenu, exclude_employe=employe
            )
            if employes_mentionnes.exists():
                reponse.mentions.set(employes_mentionnes)

            # Notification
            notifier_nouveau_commentaire(reponse, employe)

            messages.success(request, "Réponse ajoutée avec succès.")
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('gestion_temps_activite:tache_detail', pk=tache.pk)


@login_required
def commentaire_modifier(request, pk):
    """Modifier un commentaire."""
    commentaire = get_object_or_404(ZDCM, pk=pk)
    tache = commentaire.tache

    if not hasattr(request.user, 'employe'):
        return JsonResponse({'success': False, 'error': 'Profil employé requis'})

    employe = request.user.employe

    # Vérifier les permissions
    if not CommentaireService.peut_modifier_commentaire(employe, commentaire):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    if request.method == 'POST':
        nouveau_contenu = request.POST.get('contenu', '').strip()
        prive = request.POST.get('prive', 'false') == 'true'

        if not nouveau_contenu or len(nouveau_contenu) < 2:
            return JsonResponse({'success': False, 'error': 'Commentaire trop court'})

        if len(nouveau_contenu) > 1000:
            return JsonResponse({'success': False, 'error': 'Commentaire trop long'})

        commentaire.contenu = nouveau_contenu
        commentaire.prive = prive
        commentaire.modifie = True
        commentaire.save()

        # Mettre à jour les mentions
        employes_mentionnes = CommentaireService.trouver_employes_mentionnes(
            nouveau_contenu, exclude_employe=employe
        )
        commentaire.mentions.set(employes_mentionnes)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def commentaire_supprimer(request, pk):
    """Supprimer un commentaire."""
    commentaire = get_object_or_404(ZDCM, pk=pk)
    tache_pk = commentaire.tache.pk

    if not hasattr(request.user, 'employe'):
        messages.error(request, "Vous devez avoir un profil employé.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    employe = request.user.employe

    # Vérifier les permissions
    if not CommentaireService.peut_supprimer_commentaire(employe, commentaire):
        messages.error(request, "Vous n'avez pas la permission de supprimer ce commentaire.")
        return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)

    if request.method == 'POST':
        try:
            commentaire.delete()
            messages.success(request, "Commentaire supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")

    return redirect('gestion_temps_activite:tache_detail', pk=tache_pk)


@login_required
def commentaire_mentions(request):
    """API pour l'autocomplétion des mentions."""
    query = request.GET.get('q', '')

    if not hasattr(request.user, 'employe'):
        return JsonResponse({'results': []})

    employe = request.user.employe

    results = CommentaireService.rechercher_mentions_autocomplete(
        query, exclude_employe=employe
    )

    return JsonResponse({'results': results})

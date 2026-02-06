"""
Vue alternative de soumission pour déboguer les problèmes de permissions.
À SUPPRIMER EN PRODUCTION.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
import traceback

from gestion_achats.models import GACDemandeAchat
from gestion_achats.services import DemandeService
from gestion_achats.permissions import GACPermissions


@login_required
def alt_demande_submit(request, pk):
    """
    Version alternative de la soumission qui fonctionne sans les décorateurs problématiques.
    Accepte GET pour les tests et POST pour la soumission réelle (y compris AJAX).
    """
    demande = get_object_or_404(GACDemandeAchat, uuid=pk)

    # Pour les requêtes GET non-AJAX, afficher les informations de débogage
    if request.method == 'GET' and not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        debug_info = {
            'demande': {
                'numero': demande.numero,
                'statut': demande.statut,
                'demandeur': str(demande.demandeur) if demande.demandeur else None,
                'has_lignes': demande.lignes.exists(),
                'nb_lignes': demande.lignes.count(),
            },
            'user': {
                'username': request.user.username,
                'has_employe': hasattr(request.user, 'employe'),
                'employe_matricule': request.user.employe.matricule if hasattr(request.user, 'employe') else None,
            },
            'permissions': {
                'can_submit': GACPermissions.can_submit_demande(request.user, demande),
                'can_view': GACPermissions.can_view_demande(request.user, demande),
            },
            'message': 'Cliquez sur "Soumettre la demande (TEST)" ci-dessous pour tester la soumission',
        }

        # Créer une page HTML simple avec un bouton POST
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test de soumission</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .button {{ background: #007bff; color: white; padding: 10px 20px;
                          border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
                .button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <h1>Test de soumission de demande</h1>
            <h2>Informations de débogage:</h2>
            <pre>{debug_info}</pre>

            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get('CSRF_COOKIE', '')}">
                <button type="submit" class="button">Soumettre la demande (TEST)</button>
            </form>

            <p><a href="/gac/demandes/{demande.uuid}/">← Retour à la demande</a></p>
        </body>
        </html>
        """
        from django.http import HttpResponse
        return HttpResponse(html)

    # Pour les requêtes POST, tenter la soumission
    if request.method == 'POST':
        try:
            # Vérifier manuellement que l'utilisateur a un employe
            if not hasattr(request.user, 'employe') or not request.user.employe:
                raise ValueError("Utilisateur n'a pas d'employe associé")

            # Afficher les détails avant soumission
            print(f"=== ALT SUBMIT DEBUG ===")
            print(f"User: {request.user.username}")
            print(f"Employe: {request.user.employe.matricule}")
            print(f"Demande: {demande.numero}")
            print(f"Statut: {demande.statut}")
            print(f"Nb lignes: {demande.lignes.count()}")

            # Soumettre la demande
            DemandeService.soumettre_demande(demande, request.user.employe)

            print(f"✓ Soumission réussie!")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Demande {demande.numero} soumise avec succès (via méthode alternative).',
                    'redirect_url': reverse('gestion_achats:demande_detail', kwargs={'pk': demande.uuid})
                })
            else:
                messages.success(
                    request,
                    f'Demande {demande.numero} soumise avec succès (via méthode alternative).'
                )
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

        except Exception as e:
            print(f"✗ Erreur: {e}")
            print(f"Traceback: {traceback.format_exc()}")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Erreur: {str(e)}',
                    'traceback': traceback.format_exc()
                }, status=400)
            else:
                messages.error(request, f'Erreur: {str(e)}')
                return redirect('gestion_achats:demande_detail', pk=demande.uuid)

    # Pour les requêtes GET AJAX ou autres méthodes, rediriger
    return redirect('gestion_achats:demande_detail', pk=demande.uuid)

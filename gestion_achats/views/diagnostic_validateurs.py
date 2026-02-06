"""
Vue de diagnostic pour vérifier les validateurs et leurs comptes utilisateurs.
À utiliser pour identifier les problèmes de liaison User-Employe.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User

from gestion_achats.models import GACDemandeAchat
from employee.models import ZY00


@login_required
def diagnostic_validateurs(request):
    """
    Diagnostic complet des validateurs et de leurs demandes.
    Permet d'identifier les problèmes de liaison User-Employe.
    """

    # Récupérer uniquement si l'utilisateur est admin
    if not request.user.is_superuser and not (hasattr(request.user, 'employe') and request.user.employe.has_role('ADMIN_GAC')):
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    diagnostics = []

    # Récupérer tous les employés qui sont validateurs sur au moins une demande
    validateurs_n1 = GACDemandeAchat.objects.filter(
        statut='SOUMISE'
    ).values_list('validateur_n1', flat=True).distinct()

    validateurs_n2 = GACDemandeAchat.objects.filter(
        statut='VALIDEE_N1'
    ).values_list('validateur_n2', flat=True).distinct()

    tous_validateurs = set(list(validateurs_n1) + list(validateurs_n2))
    tous_validateurs.discard(None)  # Retirer les None

    for emp_id in tous_validateurs:
        try:
            emp = ZY00.objects.get(id=emp_id)

            # Compter les demandes à valider
            demandes_n1 = GACDemandeAchat.objects.filter(
                validateur_n1=emp,
                statut='SOUMISE'
            ).count()

            demandes_n2 = GACDemandeAchat.objects.filter(
                validateur_n2=emp,
                statut='VALIDEE_N1'
            ).count()

            # Vérifier le compte utilisateur
            user_info = {
                'has_user': hasattr(emp, 'user') and emp.user is not None,
                'username': None,
                'is_active': None,
                'problem': None,
            }

            if user_info['has_user']:
                user_info['username'] = emp.user.username
                user_info['is_active'] = emp.user.is_active

                if not emp.user.is_active:
                    user_info['problem'] = 'Compte utilisateur inactif'
            else:
                user_info['problem'] = 'Aucun compte utilisateur lié'

            diagnostics.append({
                'matricule': emp.matricule,
                'nom_complet': f"{emp.nom} {emp.prenoms}",
                'departement': str(emp.DEPARTEMENT) if emp.DEPARTEMENT else None,
                'demandes_n1': demandes_n1,
                'demandes_n2': demandes_n2,
                'user_info': user_info,
            })

        except ZY00.DoesNotExist:
            diagnostics.append({
                'matricule': 'INCONNU',
                'nom_complet': f'Employé ID {emp_id} introuvable',
                'error': True,
            })

    # Tri par nombre de demandes (décroissant)
    diagnostics.sort(key=lambda x: x.get('demandes_n1', 0) + x.get('demandes_n2', 0), reverse=True)

    # Rechercher un matricule spécifique si fourni
    matricule_recherche = request.GET.get('matricule')
    detail_employe = None

    if matricule_recherche:
        try:
            emp = ZY00.objects.get(matricule=matricule_recherche)

            # Récupérer toutes les demandes où il est validateur
            demandes_n1_list = GACDemandeAchat.objects.filter(
                validateur_n1=emp,
                statut='SOUMISE'
            ).values('numero', 'objet', 'demandeur__matricule', 'demandeur__nom', 'date_creation')

            demandes_n2_list = GACDemandeAchat.objects.filter(
                validateur_n2=emp,
                statut='VALIDEE_N1'
            ).values('numero', 'objet', 'demandeur__matricule', 'demandeur__nom', 'date_creation')

            detail_employe = {
                'matricule': emp.matricule,
                'nom': emp.nom,
                'prenoms': emp.prenoms,
                'departement': str(emp.DEPARTEMENT) if emp.DEPARTEMENT else None,
                'has_user': hasattr(emp, 'user') and emp.user is not None,
                'username': emp.user.username if (hasattr(emp, 'user') and emp.user) else None,
                'user_is_active': emp.user.is_active if (hasattr(emp, 'user') and emp.user) else None,
                'roles': [r.CODE for r in emp.get_roles()],
                'demandes_n1': list(demandes_n1_list),
                'demandes_n2': list(demandes_n2_list),
            }

        except ZY00.DoesNotExist:
            detail_employe = {
                'error': f'Employé avec matricule {matricule_recherche} introuvable'
            }

    # Retourner JSON si c'est une requête AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'diagnostics': diagnostics,
            'detail_employe': detail_employe,
            'total_validateurs': len(diagnostics),
        })

    # Sinon retourner HTML
    return render(request, 'gestion_achats/debug/diagnostic_validateurs.html', {
        'diagnostics': diagnostics,
        'detail_employe': detail_employe,
        'matricule_recherche': matricule_recherche,
    })

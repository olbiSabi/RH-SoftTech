# employee/views_api/api/helper_api.py
"""
API helpers pour l'application employee.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from departement.models import ZDPO


@login_required
def api_postes_by_departement(request):
    """Récupérer la liste des postes d'un département."""
    try:
        departement_id = request.GET.get('departement')
        if not departement_id:
            return JsonResponse({'error': 'Le paramètre departement est requis'}, status=400)

        postes = ZDPO.objects.filter(
            DEPARTEMENT_id=departement_id,
            STATUT=True
        ).order_by('LIBELLE')

        data = [
            {
                'id': poste.id,
                'LIBELLE': poste.LIBELLE,
            }
            for poste in postes
        ]

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

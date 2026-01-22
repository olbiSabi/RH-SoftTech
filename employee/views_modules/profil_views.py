# employee/views_modules/profil_views.py
"""
Vues pour le profil employé et la gestion des contacts d'urgence/documents.
"""
import os
from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from absence.models import AcquisitionConges, Absence
from employee.models import ZY00, ZYPP, ZYDO


@login_required
def profil_employe(request, matricule):
    """Vue du profil employé"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    # Contacts d'urgence
    contacts_urgence = employe.personnes_prevenir.filter(
        actif=True,
        date_fin_validite__isnull=True
    ).order_by('ordre_priorite')

    # Acquisition de congés de l'année N-1 (pour consommation en année N)
    annee_actuelle = date.today().year
    annee_acquisition = annee_actuelle - 1  # Année précédente

    try:
        acquisition_conges = AcquisitionConges.objects.get(
            employe=employe,
            annee_reference=annee_acquisition
        )
    except AcquisitionConges.DoesNotExist:
        acquisition_conges = None

    # Absences de l'année en cours (qui consomment les congés de N-1)
    absences = Absence.objects.filter(
        employe=employe,
        date_debut__year=annee_actuelle
    ).select_related('type_absence').order_by('-date_debut')[:10]

    # Documents
    documents = employe.documents.filter(actif=True).order_by('-date_ajout')

    context = {
        'employe': employe,
        'contacts_urgence': contacts_urgence,
        'acquisition_conges': acquisition_conges,
        'annee_acquisition': annee_acquisition,
        'annee_consommation': annee_actuelle,
        'absences': absences,
        'documents': documents,
    }

    return render(request, 'employee/profil.html', context)


@login_required
@require_POST
def upload_photo(request, matricule):
    """Upload de la photo de profil"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    if 'photo' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucune photo fournie'})

    try:
        employe.photo = request.FILES['photo']
        employe.save()

        return JsonResponse({
            'success': True,
            'photo_url': employe.get_photo_url()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_contact_urgence(request, matricule):
    """Créer un contact d'urgence"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    try:
        contact = ZYPP.objects.create(
            employe=employe,
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            lien_parente=request.POST.get('lien_parente'),
            telephone_principal=request.POST.get('telephone_principal'),
            telephone_secondaire=request.POST.get('telephone_secondaire') or None,
            email=request.POST.get('email') or None,
            adresse=request.POST.get('adresse') or None,
            ordre_priorite=request.POST.get('ordre_priorite'),
            remarques=request.POST.get('remarques') or None,
            actif=True
        )

        return JsonResponse({'success': True, 'id': contact.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def contact_urgence_detail(request, contact_id):
    """Détails d'un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    return JsonResponse({
        'id': contact.id,
        'nom': contact.nom,
        'prenom': contact.prenom,
        'lien_parente': contact.lien_parente,
        'telephone_principal': contact.telephone_principal,
        'telephone_secondaire': contact.telephone_secondaire,
        'email': contact.email,
        'adresse': contact.adresse,
        'ordre_priorite': contact.ordre_priorite,
        'remarques': contact.remarques,
    })


@login_required
@require_POST
def update_contact_urgence(request, contact_id):
    """Modifier un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    try:
        contact.nom = request.POST.get('nom')
        contact.prenom = request.POST.get('prenom')
        contact.lien_parente = request.POST.get('lien_parente')
        contact.telephone_principal = request.POST.get('telephone_principal')
        contact.telephone_secondaire = request.POST.get('telephone_secondaire') or None
        contact.email = request.POST.get('email') or None
        contact.adresse = request.POST.get('adresse') or None
        contact.ordre_priorite = request.POST.get('ordre_priorite')
        contact.remarques = request.POST.get('remarques') or None
        contact.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def delete_contact_urgence(request, contact_id):
    """Supprimer un contact d'urgence"""
    contact = get_object_or_404(ZYPP, id=contact_id)

    try:
        contact.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def upload_document(request, matricule):
    """Upload d'un document pour l'employé"""
    employe = get_object_or_404(ZY00, matricule=matricule)

    if 'fichier' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'})

    try:
        # Vérifier la taille du fichier (max 10 MB)
        fichier = request.FILES['fichier']
        if fichier.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Le fichier est trop volumineux (max 10 MB)'})

        # Vérifier l'extension
        ext = os.path.splitext(fichier.name)[1].lower()
        extensions_autorisees = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
        if ext not in extensions_autorisees:
            return JsonResponse({
                'success': False,
                'error': f'Format de fichier non autorisé. Formats acceptés : {", ".join(extensions_autorisees)}'
            })

        # Créer le document
        document = ZYDO.objects.create(
            employe=employe,
            type_document=request.POST.get('type_document'),
            description=request.POST.get('description', ''),
            fichier=fichier,
            actif=True
        )

        return JsonResponse({
            'success': True,
            'id': document.id,
            'message': 'Document ajouté avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def delete_document(request, document_id):
    """Supprimer un document"""
    document = get_object_or_404(ZYDO, id=document_id)

    try:
        # Supprimer le fichier physique
        if document.fichier and os.path.isfile(document.fichier.path):
            os.remove(document.fichier.path)

        # Supprimer l'enregistrement en base
        document.delete()

        return JsonResponse({'success': True, 'message': 'Document supprimé avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

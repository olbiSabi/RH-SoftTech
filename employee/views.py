from django.shortcuts import render


def listeEmployee(request):
    return render(request, "employee/employees-list.html")


def employee(request):
    return render(request, "employee/employees.html")


def validerEmbauche(request):
    return render(request, "employee/valider-embauche.html")


# def supprimer_dossier(request):
#     return render(request, "employe/dossierSortie.html")
#
#
# def gestion_absence(request):
#     return render(request, "employe/gestionAbsence.html")


# def editer_dossier(request):
#     return render(request, "employe/editeEmploye.html")


# Create your views here.

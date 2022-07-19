from django.shortcuts import render


def listeEmployee(request):
    return render(request, "employee/employees-list.html")


def employee(request):
    return render(request, "employee/employees.html")


def validerEmbauche(request):
    return render(request, "employee/valider-embauche.html")


def dossierSortie(request):
    return render(request, "employee/dossier-sortie.html")


def profileEmployee(request):
    return render(request, "employee/profile-employee.html")


def projet(request):
    return render(request, "projet/projets.html")


def detailProjet(request):
    return render(request, "projet/detail-projet.html")
# Create your views here.

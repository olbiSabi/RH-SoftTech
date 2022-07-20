from django.shortcuts import render


def listeEmployee(request):
    return render(request, "employee/employees-list.html")


def employee(request):
    return render(request, "employee/employees.html")


def validerEmbauche(request):
    return render(request, "employee/valider-embauche.html")


def dossierSortie(request):
    return render(request, "employee/dossier-sortie.html")


def profilEmployee(request):
    return render(request, "employee/profil-employee.html")


# Create your views here.

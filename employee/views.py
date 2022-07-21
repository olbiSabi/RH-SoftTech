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


def conges(request):
    return render(request, "employee/conges-employee.html")


def validerConges(request):
    return render(request, "employee/valider-conges.html")


def feuilleDeTemps(request):
    return render(request, "employee/feuille-de-temps.html")


def planification(request):
    return render(request, "employee/planification.html")
# Create your views here.

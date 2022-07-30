from django.shortcuts import render


def validerDepense(request):
    return render(request, "comptabilite/valider-depense.html")


def budget(request):
    return render(request, "comptabilite/budget.html")


def depenseBudgetaire(request):
    return render(request, "comptabilite/depense-budgetaire.html")


def recetteBudgetaire(request):
    return render(request, "comptabilite/recette-budgetaire.html")


def salaireEmploye(request):
    return render(request, "comptabilite/salaire-employe.html")


def elementPaie(request):
    return render(request, "comptabilite/element-paie.html")


def fichePaie(request):
    return render(request, "comptabilite/fiche-paie.html")
# Create your views here.

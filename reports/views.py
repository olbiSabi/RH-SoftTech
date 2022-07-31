from django.shortcuts import render


def rapportConge(request):
    return render(request, "reports/rapport-conge.html")


def rapportFacture(request):
    return render(request, "reports/rapport-facture.html")


def rapportFichePaie(request):
    return render(request, "reports/rapport-fiche-paie.html")

# Create your views here.

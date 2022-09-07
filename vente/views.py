from django.shortcuts import render


def devis(request):
    return render(request, "vente/devis.html")


def facture(request):
    return render(request, "vente/facture.html")


def paiement(request):
    return render(request, "vente/paiement.html")


def depense(request):
    return render(request, "vente/depense.html")


def taxe(request):
    return render(request, "vente/taxe.html")


def creerFacture(request):
    return render(request, "vente/creer-facture.html")


def editerFacture(request):
    return render(request, "vente/editer-facture.html")


def vueFacture(request):
    return render(request, "vente/vue-facture.html")


def creerDevis(request):
    return render(request, "vente/creer-devis.html")


def editerDevis(request):
    return render(request, "vente/editer-devis.html")


def vueDevis(request):
    return render(request, "vente/vue-devis.html")


def voiture(request):
    return render(request, "parcAuto/voiture.html")


def planning(request):
    return render(request, "parcAuto/planning-auto.html")
# Create your views here.

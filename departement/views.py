from django.shortcuts import render


def departement(request):
    return render(request, "departement/departement.html")


def poste(request):
    return render(request, "departement/poste.html")
# Create your views here.

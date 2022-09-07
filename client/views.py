from django.shortcuts import render


def client(request):
    return render(request, "client/client.html")


def profilClient(request):
    return render(request, "client/profil-client.html")


def fournisseur(request):
    return render(request, "client/founisseur.html")


def profilFournisseur(request):
    return render(request, "client/profil-founisseur.html")
# Create your views here.

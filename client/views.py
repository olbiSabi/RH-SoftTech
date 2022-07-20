from django.shortcuts import render


def client(request):
    return render(request, "client/client.html")


def profilClient(request):
    return render(request, "client/profil-client.html")
# def profileClient(request):
#     return render(request, "client/detail-projet.html")
# Create your views here.

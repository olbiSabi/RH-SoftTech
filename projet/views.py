from django.shortcuts import render

def projet(request):
    return render(request, "projet/projets.html")


def detailProjet(request):
    return render(request, "projet/detail-projet.html")
# Create your views here.

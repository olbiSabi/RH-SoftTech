from django.shortcuts import render


def parametreHome(request):
    return render(request, "parametre/parametre-home.html")


def parametreTheme(request):
    return render(request, "parametre/parametre-theme.html")


def parametreFacturation(request):
    return render(request, "parametre/parametre-factuation.html")


def parametreSalariaux(request):
    return render(request, "parametre/parametre-salariaux.html")


def changePassword(request):
    return render(request, "parametre/change-password.html")


def typeConge(request):
    return render(request, "parametre/type-conge.html")

def loginUser(request):
    return render(request, "parametre/login.html")

def forgetPassword(request):
    return render(request, "parametre/password-forget.html")
# Create your views here.

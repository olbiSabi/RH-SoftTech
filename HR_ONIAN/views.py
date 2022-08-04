from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def homeUser(request):
    return render(request, "home-user.html")

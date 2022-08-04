from django.urls import path

from .views import *

urlpatterns = [
    path('parametre-home/', parametreHome, name='parametreHome'),
    path('parametre-theme/', parametreTheme, name='parametreTheme'),
    path('parametre-facturation/', parametreFacturation, name='parametreFacturation'),
    path('parametre-salariaux/', parametreSalariaux, name='parametreSalariaux'),
    path('change-password/', changePassword, name='changePassword'),
    path('type-conge/', typeConge, name='typeConge'),
]
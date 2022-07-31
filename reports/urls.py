from django.urls import path


from .views import *

urlpatterns = [
    path('rapport-conge/', rapportConge, name='rapportConge'),
    path('rapport-facture/', rapportFacture, name='rapportFacture'),
    path('rapport-fiche-paie/', rapportFichePaie, name='rapportFichePaie'),

]
from django.urls import path

from .views import *

urlpatterns = [
    path('devis/', devis, name='devis'),
    path('facture/', facture, name='facture'),
    path('paiement/', paiement, name='paiement'),
    path('depense/', depense, name='depense'),
    path('commande/', commande, name='commande'),
    path('taxe/', taxe, name='taxe'),
    path('creer-facture/', creerFacture, name='creerFacture'),
    path('editer-facture/', editerFacture, name='editerFacture'),
    path('vue-facture/', vueFacture, name='vueFacture'),
    path('creer-devis/', creerDevis, name='creerDevis'),
    path('editer-devis/', editerDevis, name='editerDevis'),
    path('vue-devis/', vueDevis, name='vueDevis'),
]
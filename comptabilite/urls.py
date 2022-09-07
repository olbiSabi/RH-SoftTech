from django.urls import path

from .views import *

urlpatterns = [
    path('valider-depense/', validerDepense, name='validerDepense'),
    path('budget/', budget, name='budget'),
    path('depense-budgetaire/', depenseBudgetaire, name='depenseBudgetaire'),
    path('recette-budgetaire/', recetteBudgetaire, name='recetteBudgetaire'),
    path('salaire-employe/', salaireEmploye, name='salaireEmploye'),
    path('element-paie/', elementPaie, name='elementPaie'),
    path('fiche-paie/', fichePaie, name='fichePaie'),
]
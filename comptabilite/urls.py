from django.urls import path

from .views import *

urlpatterns = [
    path('valider-depense/', validerDepense, name='validerDepense'),
    path('budget/', budget, name='budget'),
    path('depense-budgetaire/', depenseBudgetaire, name='depenseBudgetaire'),
    path('recette-budgetaire/', recetteBudgetaire, name='recetteBudgetaire'),
]
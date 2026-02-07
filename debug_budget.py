#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HR_ONIAN.settings')
django.setup()

from gestion_achats.models import GACBudget
from decimal import Decimal

print("=== VÉRIFICATION DES CALCULS BUDGÉTAIRES ===\n")

# Rechercher les budgets avec montant initial de 550000
budgets = GACBudget.objects.filter(montant_initial=Decimal('550000.00'))

for budget in budgets:
    print(f"Budget: {budget.code} - {budget.libelle}")
    print(f"Exercice: {budget.exercice}")
    print(f"Montant initial: {budget.montant_initial} €")
    print(f"Montant engagé: {budget.montant_engage} €")
    print(f"Montant commandé: {budget.montant_commande} €")
    print(f"Montant consommé: {budget.montant_consomme} €")
    
    # Calcul manuel
    total_utilise = budget.montant_engage + budget.montant_commande + budget.montant_consomme
    disponible_calcule = budget.montant_initial - total_utilise
    disponible_methode = budget.montant_disponible()
    
    print(f"\n--- CALCULS ---")
    print(f"Total utilisé (engage + commande + consommé): {total_utilise} €")
    print(f"Disponible calculé manuellement: {disponible_calcule} €")
    print(f"Disponible via méthode montant_disponible(): {disponible_methode} €")
    
    if disponible_calcule != disponible_methode:
        print("❌ INCOHÉRENCE DÉTECTÉE!")
    else:
        print("✅ Calcul cohérent")
    
    print(f"\nDifférence: {budget.montant_initial - disponible_methode - total_utilise} €")
    print("=" * 50)
    print()

if not budgets:
    print("Aucun budget trouvé avec montant initial de 550000 €")
    
    # Afficher tous les budgets pour debug
    print("\n--- TOUS LES BUDGETS ---")
    for budget in GACBudget.objects.all():
        print(f"{budget.code}: {budget.montant_initial} €")

# employee/urls.py
"""
URLs de l'application employee.
Ce fichier utilise les modules d'URLs organisés dans urls_modules/
"""
from django.urls import path, include

app_name = 'employee'

# Utiliser les URLs modulaires
urlpatterns = [
    # Authentification (login, logout, dashboard, password)
    path('', include('employee.urls_modules.auth_urls')),

    # Embauche (embauche_agent, valider_embauche)
    path('', include('employee.urls_modules.embauche_urls')),

    # Employés CRUD (liste, detail, modifier, supprimer)
    path('', include('employee.urls_modules.employee_urls')),

    # Dossier individuel
    path('', include('employee.urls_modules.dossier_urls')),

    # Gestion des rôles
    path('', include('employee.urls_modules.roles_urls')),

    # Profil (profil, photo, contacts urgence, documents)
    path('', include('employee.urls_modules.profil_urls')),

    # API modales (téléphone, email, adresse, contrat, affectation, document, famille, etc.)
    path('', include('employee.urls_modules.api_urls')),
]

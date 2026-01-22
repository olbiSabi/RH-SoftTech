# employee/urls_modules/__init__.py
"""
Module regroupant toutes les URLs de l'application employee.
Réorganisation du fichier urls.py monolithique en modules spécialisés.

Usage dans urls.py principal:
    from django.urls import path, include

    urlpatterns = [
        path('employee/', include('employee.urls_modules')),
    ]
"""
from django.urls import path, include

app_name = 'employee'

urlpatterns = [
    # Authentification
    path('', include('employee.urls_modules.auth_urls')),

    # Embauche
    path('', include('employee.urls_modules.embauche_urls')),

    # Employés CRUD
    path('', include('employee.urls_modules.employee_urls')),

    # Dossier individuel
    path('', include('employee.urls_modules.dossier_urls')),

    # Gestion des rôles
    path('', include('employee.urls_modules.roles_urls')),

    # Profil
    path('', include('employee.urls_modules.profil_urls')),

    # API modales
    path('', include('employee.urls_modules.api_urls')),
]

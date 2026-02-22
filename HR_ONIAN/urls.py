"""HR_ONIAN URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection
from employee.auth_views import (
    login_view,
    logout_view,
    dashboard_view,
    password_reset_request,
    CustomPasswordResetConfirmView,
    change_password_view
)


def health_check(request):
    """Endpoint de vérification de santé pour le monitoring."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({
        'status': 'ok' if db_ok else 'error',
        'database': 'connected' if db_ok else 'unreachable',
    }, status=status)


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('hronian/', admin.site.urls),
    path('entreprise/', include('entreprise.urls')),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('change-password/', change_password_view, name='change_password'),
    path('password-reset-request/', password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/',
         CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    # Redirection de la racine vers la page de login
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),

    # URLs des applications
    path('employe/', include('employee.urls', namespace='employee')),
    path('absence/', include('absence.urls')),
    path('departement/', include('departement.urls')),
    # Module Notes de Frais
    path('frais/', include('frais.urls', namespace='frais')),
    # Module Suivi du Matériel & Parc
    path('materiel/', include('materiel.urls', namespace='materiel')),
    # Module Conformité & Audit
    path('audit/', include('audit.urls', namespace='audit')),
    # Module Gestion de Projet
    path('pm/', include('project_management.urls', namespace='pm')),
    # Module Gestion des Achats & Commandes
    path('gac/', include('gestion_achats.urls', namespace='gestion_achats')),
    # Module Planning
    path('planning/', include('planning.urls', namespace='planning')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

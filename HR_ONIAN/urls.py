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
from employee.auth_views import (
    login_view,
    logout_view,
    dashboard_view,
    password_reset_request,
    CustomPasswordResetConfirmView,
    change_password_view
)


urlpatterns = [
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
    # Module Gestion Temps et Activités
    path('gestion-temps/', include('gestion_temps_activite.urls', namespace='gestion_temps_activite')),
    # Module Notes de Frais
    path('frais/', include('frais.urls', namespace='frais')),
    # Module Suivi du Matériel & Parc
    path('materiel/', include('materiel.urls', namespace='materiel')),
    # Module Conformité & Audit
    path('audit/', include('audit.urls', namespace='audit')),
    # Module Gestion de Projet (remplace gestion_temps_activite)
    path('project-management/', include('project_management.urls', namespace='pm')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

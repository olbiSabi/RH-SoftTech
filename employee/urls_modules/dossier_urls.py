# employee/urls_modules/dossier_urls.py
"""
URLs pour le dossier individuel des employés.
"""
from django.urls import path

from employee.views_modules.dossier_views import (
    DossierIndividuelView,
    detail_employe,
)

urlpatterns = [
    path('matricule/<uuid:uuid>/', detail_employe, name='detail_employe'),
    path('dossier/', DossierIndividuelView.as_view(), name='dossier_individuel'),
    path('dossier/<uuid:uuid>/', DossierIndividuelView.as_view(), name='dossier_individuel_detail'),
]

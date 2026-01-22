# employee/urls_modules/employee_urls.py
"""
URLs pour les opérations CRUD sur les employés.
"""
from django.urls import path

from employee.views_modules.employee_views import (
    EmployeListView,
    EmployeUpdateView,
    EmployeDeleteView,
)

urlpatterns = [
    path('liste-employee/', EmployeListView.as_view(), name='liste_employes'),
    path('employe/<uuid:uuid>/modifier/', EmployeUpdateView.as_view(), name='modifier_employe'),
    path('employe/<uuid:uuid>/supprimer/', EmployeDeleteView.as_view(), name='supprimer_employe'),
]

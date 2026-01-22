# employee/urls_modules/embauche_urls.py
"""
URLs pour le processus d'embauche.
"""
from django.urls import path

from employee.views_modules.embauche_views import (
    embauche_agent,
    valider_embauche,
)

urlpatterns = [
    path('embauche-agent/', embauche_agent, name='embauche_agent'),
    path('employe/<uuid:uuid>/valider/', valider_embauche, name='valider_embauche'),
]

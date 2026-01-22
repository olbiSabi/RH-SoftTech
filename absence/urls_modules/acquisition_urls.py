# absence/urls_modules/acquisition_urls.py
"""
URLs pour la gestion des acquisitions de congés.
"""
from django.urls import path
from absence import views

# Note: Ces URLs sont incluses avec le préfixe 'acquisitions/' depuis urls.py principal
urlpatterns = [
    # Page liste acquisitions
    path('', views.liste_acquisitions, name='liste_acquisitions'),

    # API Acquisitions
    path('api/<int:id>/', views.api_acquisition_detail, name='api_acquisition_detail'),
    path('api/<int:id>/update/', views.api_acquisition_update, name='api_acquisition_update'),
    path('api/<int:id>/delete/', views.api_acquisition_delete, name='api_acquisition_delete'),
    path('api/<int:id>/recalculer/', views.api_recalculer_acquisition, name='api_recalculer_acquisition'),
    path('api/calculer/', views.api_calculer_acquisitions, name='api_calculer_acquisitions'),
    path('api/calculer-acquis-a-date/', views.api_calculer_acquis_a_date, name='api_calculer_acquis_a_date'),
]

# absence/urls_modules/notification_urls.py
"""
URLs pour la gestion des notifications d'absence.
"""
from django.urls import path
from absence import views

urlpatterns = [
    path('<int:id>/', views.notification_detail, name='notification_detail'),
    path('marquer-toutes-lues/', views.marquer_toutes_lues, name='marquer_toutes_lues'),
    path('toutes/', views.toutes_notifications, name='toutes_notifications'),
    path('counts/', views.notification_counts, name='notification_counts'),
    path('<int:notification_id>/marquer-lue/', views.marquer_notification_lue, name='marquer_notification_lue'),
]

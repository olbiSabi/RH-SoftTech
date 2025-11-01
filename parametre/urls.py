from django.urls import path
from . import views
from .views import *

urlpatterns = [
# Routes Absence
    path('poste/', views.absence_list, name='absence_list'),
    path('poste/edit/<int:pk>/', views.absence_edit, name='absence_edit'),
    path('poste/delete/<int:pk>/', views.absence_delete, name='absence_delete'),

    path('parametre-home/', parametreHome, name='parametreHome'),
    path('parametre-theme/', parametreTheme, name='parametreTheme'),
    path('parametre-facturation/', parametreFacturation, name='parametreFacturation'),
    path('parametre-salariaux/', parametreSalariaux, name='parametreSalariaux'),
    path('change-password/', changePassword, name='changePassword'),
    path('login/', loginUser, name='loginUser'),
    path('password-forget/', forgetPassword, name='forgetPassword'),
]
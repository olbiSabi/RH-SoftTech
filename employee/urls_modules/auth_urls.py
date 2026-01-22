# employee/urls_modules/auth_urls.py
"""
URLs pour l'authentification et la gestion des mots de passe.
"""
from django.urls import path

from employee.auth_views import (
    login_view,
    logout_view,
    dashboard_view,
    change_password_view,
    password_reset_request,
    CustomPasswordResetConfirmView,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('change-password/', change_password_view, name='change_password'),
    path('password-reset-request/', password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

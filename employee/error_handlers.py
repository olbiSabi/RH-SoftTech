# employee/error_handlers.py
"""
Handlers personnalisés pour les erreurs HTTP.
"""
from django.shortcuts import render


def handler404(request, exception):
    """Vue personnalisée pour les erreurs 404."""
    return render(request, '404.html', status=404)


def handler500(request):
    """Vue personnalisée pour les erreurs 500."""
    return render(request, '500.html', status=500)


def handler403(request, exception):
    """Vue personnalisée pour les erreurs 403."""
    return render(request, '403.html', status=403)


def handler400(request, exception):
    """Vue personnalisée pour les erreurs 400."""
    return render(request, '400.html', status=400)

# audit/templatetags/audit_filters.py
"""
Filtres de template personnalisés pour le module audit.
"""
from django import template

register = template.Library()


@register.filter(name='abs')
def abs_filter(value):
    """
    Retourne la valeur absolue d'un nombre.

    Usage dans les templates:
        {{ valeur|abs }}

    Exemple:
        {{ -5|abs }}  # Retourne 5
    """
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

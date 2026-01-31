from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a variable key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def format_heures(value):
    """
    Convertit un nombre décimal d'heures en format 'Xh Ymin'.
    Exemple: 6.25 -> '6h 15min', 2.0 -> '2h', 0.5 -> '0h 30min'
    """
    if value is None:
        return '0h'

    try:
        total_minutes = int(float(value) * 60)
        heures = total_minutes // 60
        minutes = total_minutes % 60

        if minutes > 0:
            return f"{heures}h {minutes}min"
        return f"{heures}h"
    except (ValueError, TypeError):
        return '0h'


@register.filter
def format_minutes(value):
    """
    Convertit un nombre de minutes en format 'Xh Ymin'.
    Exemple: 375 -> '6h 15min', 120 -> '2h', 30 -> '0h 30min'
    """
    if value is None or value == 0:
        return '0h'

    try:
        total_minutes = int(value)
        heures = total_minutes // 60
        minutes = total_minutes % 60

        if minutes > 0:
            return f"{heures}h {minutes}min"
        return f"{heures}h"
    except (ValueError, TypeError):
        return '0h'

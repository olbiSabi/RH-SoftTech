# gestion_temps_activite/templatetags/comment_tags.py
from django import template

register = template.Library()

@register.filter
def peut_modifier(commentaire, employe):
    """Filtre pour vérifier si un employé peut modifier un commentaire"""
    return commentaire.peut_modifier(employe)

@register.filter
def peut_supprimer(commentaire, employe):
    """Filtre pour vérifier si un employé peut supprimer un commentaire"""
    return commentaire.peut_supprimer(employe)
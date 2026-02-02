"""
Template tags pour les permissions du module GAC.

Usage dans un template:
    {% load gac_permissions %}

    {% if_can_modify_demande user demande %}
        <a href="...">Modifier</a>
    {% endif_can_modify_demande %}

    {% can_validate_n1 user demande as can_validate %}
    {% if can_validate %}
        <button>Valider N1</button>
    {% endif %}
"""

from django import template
from gestion_achats.permissions import GACPermissions

register = template.Library()


# ========== Demandes d'achat ==========

@register.simple_tag
def can_view_demande(user, demande):
    """Vérifie si l'utilisateur peut voir une demande."""
    return GACPermissions.can_view_demande(user, demande)


@register.simple_tag
def can_create_demande(user):
    """Vérifie si l'utilisateur peut créer une demande."""
    return GACPermissions.can_create_demande(user)


@register.simple_tag
def can_modify_demande(user, demande):
    """Vérifie si l'utilisateur peut modifier une demande."""
    return GACPermissions.can_modify_demande(user, demande)


@register.simple_tag
def can_submit_demande(user, demande):
    """Vérifie si l'utilisateur peut soumettre une demande."""
    return GACPermissions.can_submit_demande(user, demande)


@register.simple_tag
def can_validate_n1(user, demande):
    """Vérifie si l'utilisateur peut valider N1 une demande."""
    return GACPermissions.can_validate_n1(user, demande)


@register.simple_tag
def can_validate_n2(user, demande):
    """Vérifie si l'utilisateur peut valider N2 une demande."""
    return GACPermissions.can_validate_n2(user, demande)


@register.simple_tag
def can_refuse_demande(user, demande):
    """Vérifie si l'utilisateur peut refuser une demande."""
    return GACPermissions.can_refuse_demande(user, demande)


@register.simple_tag
def can_cancel_demande(user, demande):
    """Vérifie si l'utilisateur peut annuler une demande."""
    return GACPermissions.can_cancel_demande(user, demande)


@register.simple_tag
def can_convert_to_bc(user, demande):
    """Vérifie si l'utilisateur peut convertir une demande en BC."""
    return GACPermissions.can_convert_to_bc(user, demande)


@register.simple_tag
def can_delete_demande(user):
    """Vérifie si l'utilisateur peut supprimer des demandes."""
    return GACPermissions.can_delete_demande(user)


@register.simple_tag
def can_view_all_demandes(user):
    """Vérifie si l'utilisateur peut voir toutes les demandes."""
    return GACPermissions.can_view_all_demandes(user)


# ========== Bons de commande ==========

@register.simple_tag
def can_view_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut voir un BC."""
    return GACPermissions.can_view_bon_commande(user, bc)


@register.simple_tag
def can_create_bon_commande(user):
    """Vérifie si l'utilisateur peut créer un BC."""
    return GACPermissions.can_create_bon_commande(user)


@register.simple_tag
def can_modify_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut modifier un BC."""
    return GACPermissions.can_modify_bon_commande(user, bc)


@register.simple_tag
def can_emit_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut émettre un BC."""
    return GACPermissions.can_emit_bon_commande(user, bc)


@register.simple_tag
def can_send_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut envoyer un BC."""
    return GACPermissions.can_send_bon_commande(user, bc)


@register.simple_tag
def can_confirm_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut confirmer un BC."""
    return GACPermissions.can_confirm_bon_commande(user, bc)


@register.simple_tag
def can_cancel_bon_commande(user, bc):
    """Vérifie si l'utilisateur peut annuler un BC."""
    return GACPermissions.can_cancel_bon_commande(user, bc)


@register.simple_tag
def can_download_pdf(user, bc):
    """Vérifie si l'utilisateur peut télécharger le PDF d'un BC."""
    return GACPermissions.can_download_pdf(user, bc)


@register.simple_tag
def can_view_all_bons_commande(user):
    """Vérifie si l'utilisateur peut voir tous les BCs."""
    return GACPermissions.can_view_all_bons_commande(user)


# ========== Fournisseurs ==========

@register.simple_tag
def can_view_fournisseur(user):
    """Vérifie si l'utilisateur peut voir les fournisseurs."""
    return GACPermissions.can_view_fournisseur(user)


@register.simple_tag
def can_create_fournisseur(user):
    """Vérifie si l'utilisateur peut créer un fournisseur."""
    return GACPermissions.can_create_fournisseur(user)


@register.simple_tag
def can_modify_fournisseur(user):
    """Vérifie si l'utilisateur peut modifier un fournisseur."""
    return GACPermissions.can_modify_fournisseur(user)


@register.simple_tag
def can_evaluate_fournisseur(user):
    """Vérifie si l'utilisateur peut évaluer un fournisseur."""
    return GACPermissions.can_evaluate_fournisseur(user)


# ========== Réceptions ==========

@register.simple_tag
def can_view_reception(user, reception):
    """Vérifie si l'utilisateur peut voir une réception."""
    return GACPermissions.can_view_reception(user, reception)


@register.simple_tag
def can_create_reception(user):
    """Vérifie si l'utilisateur peut créer une réception."""
    return GACPermissions.can_create_reception(user)


@register.simple_tag
def can_modify_reception(user, reception):
    """Vérifie si l'utilisateur peut modifier une réception."""
    return GACPermissions.can_modify_reception(user, reception)


@register.simple_tag
def can_validate_reception(user, reception):
    """Vérifie si l'utilisateur peut valider une réception."""
    return GACPermissions.can_validate_reception(user, reception)


@register.simple_tag
def can_cancel_reception(user):
    """Vérifie si l'utilisateur peut annuler une réception."""
    return GACPermissions.can_cancel_reception(user)


# ========== Catalogue ==========

@register.simple_tag
def can_view_catalogue(user):
    """Vérifie si l'utilisateur peut voir le catalogue."""
    return GACPermissions.can_view_catalogue(user)


@register.simple_tag
def can_manage_catalogue(user):
    """Vérifie si l'utilisateur peut gérer le catalogue."""
    return GACPermissions.can_manage_catalogue(user)


# ========== Budgets ==========

@register.simple_tag
def can_view_budget(user, budget):
    """Vérifie si l'utilisateur peut voir un budget."""
    return GACPermissions.can_view_budget(user, budget)


@register.simple_tag
def can_create_budget(user):
    """Vérifie si l'utilisateur peut créer un budget."""
    return GACPermissions.can_create_budget(user)


@register.simple_tag
def can_modify_budget(user, budget):
    """Vérifie si l'utilisateur peut modifier un budget."""
    return GACPermissions.can_modify_budget(user, budget)


@register.simple_tag
def can_view_all_budgets(user):
    """Vérifie si l'utilisateur peut voir tous les budgets."""
    return GACPermissions.can_view_all_budgets(user)


# ========== Helper pour vérifier les rôles ==========

@register.simple_tag
def has_role(user, role_code):
    """
    Vérifie si l'utilisateur a un rôle spécifique.

    Usage:
        {% has_role user 'ACHETEUR' as is_acheteur %}
        {% if is_acheteur %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_role(role_code)


@register.simple_tag
def has_any_role(user, *role_codes):
    """
    Vérifie si l'utilisateur a au moins un des rôles spécifiés.

    Usage:
        {% has_any_role user 'ACHETEUR' 'RECEPTIONNAIRE' as can_manage %}
        {% if can_manage %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return any(user.has_role(role) for role in role_codes)


# ========== Filtres ==========

@register.filter
def user_has_role(user, role_code):
    """
    Filtre pour vérifier si un utilisateur a un rôle.

    Usage:
        {% if user|user_has_role:'ACHETEUR' %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_role(role_code)


# ========== Tags pour le menu ==========

@register.simple_tag
def can_validate_gac(user):
    """
    Vérifie si l'utilisateur peut valider des demandes GAC (N1, N2 ou Admin).

    Usage: {% can_validate_gac user as can_validate %}
    """
    if not user or not user.is_authenticated or not hasattr(user, 'employe') or not user.employe:
        return False
    return (
        user.employe.has_role('VALIDATEUR_N1') or
        user.employe.has_role('VALIDATEUR_N2') or
        user.employe.has_role('ADMIN_GAC')
    )


@register.simple_tag
def can_manage_bons_commande(user):
    """
    Vérifie si l'utilisateur peut gérer les bons de commande.

    Usage: {% can_manage_bons_commande user as can_manage_bc %}
    """
    if not user or not user.is_authenticated or not hasattr(user, 'employe') or not user.employe:
        return False
    return (
        user.employe.has_role('ACHETEUR') or
        user.employe.has_role('RECEPTIONNAIRE') or
        user.employe.has_role('ADMIN_GAC')
    )


@register.simple_tag
def can_manage_budgets(user):
    """
    Vérifie si l'utilisateur peut gérer les budgets.

    Usage: {% can_manage_budgets user as can_manage %}
    """
    if not user or not user.is_authenticated or not hasattr(user, 'employe') or not user.employe:
        return False
    return (
        user.employe.has_role('GESTIONNAIRE_BUDGET') or
        user.employe.has_role('ADMIN_GAC')
    )


@register.simple_tag
def is_admin_gac(user):
    """
    Vérifie si l'utilisateur est admin GAC.

    Usage: {% is_admin_gac user as is_admin %}
    """
    if not user or not user.is_authenticated or not hasattr(user, 'employe') or not user.employe:
        return False
    return user.employe.has_role('ADMIN_GAC')

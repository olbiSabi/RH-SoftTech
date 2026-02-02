"""
Mixins de permissions pour les Class-Based Views du module GAC.

Ce module fournit des mixins pour sécuriser les CBVs basées sur les rôles
et les permissions du module GAC.
"""

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier qu'un utilisateur a un rôle spécifique.

    Attributes:
        required_role (str): Code du rôle requis

    Usage:
        class MaVue(RoleRequiredMixin, CreateView):
            required_role = 'ACHETEUR'
            model = MonModele
            ...
    """
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not self.required_role:
            raise ValueError("required_role doit être défini")

        if not request.user.has_role(self.required_role):
            raise PermissionDenied(f"Rôle requis: {self.required_role}")

        return super().dispatch(request, *args, **kwargs)


class AnyRoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier qu'un utilisateur a au moins un des rôles spécifiés.

    Attributes:
        required_roles (list): Liste des codes de rôles acceptés

    Usage:
        class MaVue(AnyRoleRequiredMixin, CreateView):
            required_roles = ['ACHETEUR', 'RECEPTIONNAIRE']
            model = MonModele
            ...
    """
    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not self.required_roles:
            raise ValueError("required_roles doit être défini et non vide")

        if not any(request.user.has_role(role) for role in self.required_roles):
            roles_str = ', '.join(self.required_roles)
            raise PermissionDenied(f"Un de ces rôles est requis: {roles_str}")

        return super().dispatch(request, *args, **kwargs)


class DemandeAccessMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier l'accès à une demande d'achat.

    Vérifie automatiquement que l'utilisateur peut voir la demande
    en fonction des règles de permissions.

    Usage:
        class DemandeDetailView(DemandeAccessMixin, DetailView):
            model = GACDemandeAchat
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        demande = self.get_object()

        if not GACPermissions.can_view_demande(request.user, demande):
            raise PermissionDenied("Vous n'avez pas accès à cette demande")

        return super().dispatch(request, *args, **kwargs)


class BonCommandeAccessMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier l'accès à un bon de commande.

    Vérifie automatiquement que l'utilisateur peut voir le BC
    en fonction des règles de permissions.

    Usage:
        class BonCommandeDetailView(BonCommandeAccessMixin, DetailView):
            model = GACBonCommande
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        bc = self.get_object()

        if not GACPermissions.can_view_bon_commande(request.user, bc):
            raise PermissionDenied("Vous n'avez pas accès à ce bon de commande")

        return super().dispatch(request, *args, **kwargs)


class ReceptionAccessMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier l'accès à une réception.

    Vérifie automatiquement que l'utilisateur peut voir la réception
    en fonction des règles de permissions.

    Usage:
        class ReceptionDetailView(ReceptionAccessMixin, DetailView):
            model = GACReception
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        reception = self.get_object()

        if not GACPermissions.can_view_reception(request.user, reception):
            raise PermissionDenied("Vous n'avez pas accès à cette réception")

        return super().dispatch(request, *args, **kwargs)


class BudgetAccessMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier l'accès à un budget.

    Vérifie automatiquement que l'utilisateur peut voir le budget
    en fonction des règles de permissions.

    Usage:
        class BudgetDetailView(BudgetAccessMixin, DetailView):
            model = GACBudget
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        budget = self.get_object()

        if not GACPermissions.can_view_budget(request.user, budget):
            raise PermissionDenied("Vous n'avez pas accès à ce budget")

        return super().dispatch(request, *args, **kwargs)


class CatalogueManagementMixin(LoginRequiredMixin):
    """
    Mixin pour les vues de gestion du catalogue (articles, catégories).

    Vérifie que l'utilisateur a les droits de gestion du catalogue.

    Usage:
        class ArticleCreateView(CatalogueManagementMixin, CreateView):
            model = GACArticle
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        if not GACPermissions.can_manage_catalogue(request.user):
            raise PermissionDenied("Vous n'avez pas les droits de gestion du catalogue")

        return super().dispatch(request, *args, **kwargs)


class FournisseurManagementMixin(LoginRequiredMixin):
    """
    Mixin pour les vues de gestion des fournisseurs.

    Vérifie que l'utilisateur a les droits de modification des fournisseurs.

    Usage:
        class FournisseurCreateView(FournisseurManagementMixin, CreateView):
            model = GACFournisseur
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        from gestion_achats.permissions import GACPermissions

        if not GACPermissions.can_modify_fournisseur(request.user):
            raise PermissionDenied("Vous n'avez pas les droits de gestion des fournisseurs")

        return super().dispatch(request, *args, **kwargs)

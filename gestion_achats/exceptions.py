"""
Exceptions personnalisées pour le module Gestion des Achats & Commandes (GAC).
"""


class GACException(Exception):
    """Exception de base pour le module GAC."""

    pass


class BudgetInsuffisantError(GACException):
    """
    Exception levée quand le budget est insuffisant pour une opération.

    Utilisée lors de:
    - Validation N2 d'une demande
    - Engagement d'un montant
    """

    pass


class WorkflowError(GACException):
    """
    Exception levée pour les erreurs de workflow.

    Utilisée lors de:
    - Tentative de transition d'état invalide
    - Opération non autorisée dans l'état actuel
    """

    pass


class ValidationError(GACException):
    """
    Exception levée pour les erreurs de validation métier.

    Utilisée lors de:
    - Données invalides
    - Règles métier non respectées
    - Contraintes métier violées
    """

    pass


class PermissionError(GACException):
    """
    Exception levée pour les erreurs de permission.

    Utilisée lors de:
    - Utilisateur non autorisé pour une action
    - Rôle insuffisant
    """

    pass


class DemandeError(GACException):
    """Exception spécifique aux demandes d'achat."""

    pass


class BonCommandeError(GACException):
    """Exception spécifique aux bons de commande."""

    pass


class ReceptionError(GACException):
    """Exception spécifique aux réceptions."""

    pass


class FournisseurError(GACException):
    """Exception spécifique aux fournisseurs."""

    pass


class BudgetError(GACException):
    """Exception spécifique aux budgets."""

    pass


class PDFGenerationError(GACException):
    """
    Exception levée lors d'une erreur de génération de PDF.

    Utilisée lors de:
    - Erreur de génération de PDF de bon de commande
    - Template PDF invalide
    """

    pass


class EmailSendError(GACException):
    """
    Exception levée lors d'une erreur d'envoi d'email.

    Utilisée lors de:
    - Erreur d'envoi d'email au fournisseur
    - Erreur d'envoi de notification par email
    """

    pass

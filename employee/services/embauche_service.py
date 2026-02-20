# employee/services/embauche_service.py
"""
Service de gestion du processus d'embauche.
Centralise la logique de création d'employés et de comptes utilisateurs.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, Tuple
from datetime import date
import logging

from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

if TYPE_CHECKING:
    from employee.models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYNP

logger = logging.getLogger(__name__)


class EmbaucheService:
    """
    Service pour le processus d'embauche.

    Ce service centralise toute la logique de création d'employés,
    de comptes utilisateurs et des données associées.

    Utilisation:
        from employee.services import EmbaucheService

        # Créer une pré-embauche complète
        result = EmbaucheService.create_pre_embauche(form_data)

        # Valider une embauche
        EmbaucheService.validate_embauche(employe)

        # Créer un compte utilisateur
        username, password = EmbaucheService.create_user_account(employe)
    """

    # Mot de passe par défaut pour les nouveaux comptes
    DEFAULT_PASSWORD = "Hronian2024!"

    # ==================== CRÉATION D'EMPLOYÉ ====================

    @staticmethod
    @transaction.atomic
    def create_pre_embauche(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une pré-embauche complète avec toutes les données associées.

        Cette méthode crée en une seule transaction atomique :
        - L'employé (ZY00)
        - Le compte utilisateur (User)
        - L'historique nom/prénom (ZYNP)
        - Le contrat (ZYCO)
        - Le téléphone (ZYTE)
        - L'email (ZYME)
        - L'affectation (ZYAF)
        - L'adresse principale (ZYAD)

        Args:
            form_data: Dictionnaire contenant toutes les données du formulaire
                Required keys:
                    - nom, prenoms, date_naissance, sexe
                    - type_id, numero_id, date_validite_id, date_expiration_id
                    - type_contrat, date_debut_contrat
                    - numero_telephone, email
                    - poste (instance ZDPO)
                    - rue, ville, pays, code_postal, date_debut_adresse
                Optional keys:
                    - entreprise, convention_personnalisee
                    - date_entree_entreprise, coefficient_temps_travail
                    - ville_naissance, pays_naissance, situation_familiale
                    - date_fin_contrat, complement

        Returns:
            dict: {
                'success': bool,
                'employe': ZY00 instance,
                'username': str,
                'password': str,
                'error': str (si échec)
            }

        Raises:
            Exception: En cas d'erreur (la transaction est rollback)
        """
        from employee.models import ZY00, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYNP

        try:
            # 1. Créer l'employé
            employe = ZY00(
                nom=form_data['nom'],
                prenoms=form_data['prenoms'],
                date_naissance=form_data['date_naissance'],
                sexe=form_data['sexe'],
                type_id=form_data['type_id'],
                numero_id=form_data['numero_id'],
                date_validite_id=form_data['date_validite_id'],
                date_expiration_id=form_data['date_expiration_id'],
                type_dossier='PRE',
                etat='actif',
                # Champs optionnels
                ville_naissance=form_data.get('ville_naissance', ''),
                pays_naissance=form_data.get('pays_naissance', ''),
                situation_familiale=form_data.get('situation_familiale', ''),
                entreprise=form_data.get('entreprise'),
                convention_personnalisee=form_data.get('convention_personnalisee'),
                date_entree_entreprise=form_data.get('date_entree_entreprise'),
                coefficient_temps_travail=form_data.get('coefficient_temps_travail', 1.00),
            )

            # Initialiser username et prenomuser
            employe.username = employe.nom
            employe.prenomuser = employe.prenoms

            # Sauvegarder (génère le matricule automatiquement)
            employe.save()

            logger.info(f"Employé créé: {employe.matricule} - {employe.nom} {employe.prenoms}")

            date_jour = timezone.now().date()

            # 2. Créer l'historique nom/prénom
            ZYNP.objects.create(
                employe=employe,
                nom=employe.nom,
                prenoms=employe.prenoms,
                date_debut_validite=date_jour,
                actif=True
            )

            # 3. Créer le contrat
            ZYCO.objects.create(
                employe=employe,
                type_contrat=form_data['type_contrat'],
                date_debut=form_data['date_debut_contrat'],
                date_fin=form_data.get('date_fin_contrat')
            )

            # 4. Créer le téléphone
            ZYTE.objects.create(
                employe=employe,
                numero=form_data['numero_telephone'],
                date_debut_validite=date_jour
            )

            # 5. Créer l'email (AVANT le compte utilisateur pour que l'email ZYME soit utilisé)
            ZYME.objects.create(
                employe=employe,
                email=form_data['email'],
                date_debut_validite=date_jour
            )

            # 6. Créer le compte utilisateur (utilise l'email ZYME le plus récent)
            username, password = EmbaucheService.create_user_account(employe)

            # 7. Créer l'affectation
            ZYAF.objects.create(
                employe=employe,
                poste=form_data['poste'],
                date_debut=date_jour
            )

            # 8. Créer l'adresse principale
            ZYAD.objects.create(
                employe=employe,
                rue=form_data['rue'],
                ville=form_data['ville'],
                complement=form_data.get('complement', ''),
                pays=form_data['pays'],
                code_postal=form_data['code_postal'],
                type_adresse='PRINCIPALE',
                date_debut=form_data['date_debut_adresse']
            )

            logger.info(
                f"Pré-embauche complète créée pour {employe.matricule} "
                f"(username: {username})"
            )

            return {
                'success': True,
                'employe': employe,
                'username': username,
                'password': password,
            }

        except Exception as e:
            logger.error(f"Erreur lors de la création de la pré-embauche: {e}")
            raise

    @staticmethod
    def create_employee_only(
        nom: str,
        prenoms: str,
        date_naissance: date,
        sexe: str,
        type_id: str,
        numero_id: str,
        date_validite_id: date,
        date_expiration_id: date,
        **kwargs
    ) -> 'ZY00':
        """
        Crée uniquement un employé (sans les données associées).

        Args:
            nom: Nom de l'employé
            prenoms: Prénom(s)
            date_naissance: Date de naissance
            sexe: 'M' ou 'F'
            type_id: Type d'identité (CNI, PASSEPORT, AUTRES)
            numero_id: Numéro d'identité
            date_validite_id: Date de validité de l'ID
            date_expiration_id: Date d'expiration de l'ID
            **kwargs: Autres champs optionnels

        Returns:
            ZY00: Instance de l'employé créé
        """
        from employee.models import ZY00

        employe = ZY00(
            nom=nom,
            prenoms=prenoms,
            date_naissance=date_naissance,
            sexe=sexe,
            type_id=type_id,
            numero_id=numero_id,
            date_validite_id=date_validite_id,
            date_expiration_id=date_expiration_id,
            type_dossier=kwargs.get('type_dossier', 'PRE'),
            etat=kwargs.get('etat', 'actif'),
            **{k: v for k, v in kwargs.items() if k not in ['type_dossier', 'etat']}
        )

        employe.username = employe.nom
        employe.prenomuser = employe.prenoms
        employe.save()

        return employe

    # ==================== GESTION DES COMPTES UTILISATEURS ====================

    @staticmethod
    def create_user_account(
        employe: 'ZY00',
        password: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Crée un compte utilisateur pour un employé.

        Args:
            employe: Instance de ZY00
            password: Mot de passe personnalisé (optionnel)

        Returns:
            Tuple[str, str]: (username, password)
        """
        # Générer un username unique basé sur le nom et prénom
        base_username = EmbaucheService._generate_base_username(employe)
        username = EmbaucheService._get_unique_username(base_username)

        # Utiliser le mot de passe fourni ou le mot de passe par défaut
        final_password = password or EmbaucheService.DEFAULT_PASSWORD

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            password=final_password,
            first_name=employe.prenomuser or employe.prenoms.split()[0],
            last_name=employe.username or employe.nom,
            email=EmbaucheService._get_email_for_user(employe, username)
        )

        # Lier l'utilisateur à l'employé
        employe.user = user
        employe.save(update_fields=['user'])

        logger.info(f"Compte utilisateur créé pour {employe.matricule}: {username}")

        return username, final_password

    @staticmethod
    def _generate_base_username(employe: 'ZY00') -> str:
        """Génère le username de base à partir du nom et prénom."""
        nom = employe.nom.lower().replace(' ', '').replace('-', '')
        prenom = employe.prenoms.split()[0].lower().replace(' ', '').replace('-', '')
        return f"{nom}.{prenom}"

    @staticmethod
    def _get_unique_username(base_username: str) -> str:
        """Retourne un username unique en ajoutant un suffixe si nécessaire."""
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    @staticmethod
    def _get_email_for_user(employe: 'ZY00', username: str) -> str:
        """Retourne l'email à utiliser pour le compte utilisateur."""
        # Essayer de récupérer l'email de l'employé
        if hasattr(employe, 'emails'):
            email_obj = employe.emails.filter(actif=True).first()
            if email_obj:
                return email_obj.email

        # Sinon, générer un email par défaut
        return f"{username}@onian-easym.com"

    @staticmethod
    def reset_user_password(
        employe: 'ZY00',
        new_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Réinitialise le mot de passe d'un utilisateur.

        Args:
            employe: Instance de ZY00
            new_password: Nouveau mot de passe (optionnel)

        Returns:
            Tuple[bool, str]: (success, new_password)
        """
        if not employe.user:
            logger.warning(f"Pas de compte utilisateur pour {employe.matricule}")
            return False, ""

        password = new_password or EmbaucheService.DEFAULT_PASSWORD
        employe.user.set_password(password)
        employe.user.save()

        logger.info(f"Mot de passe réinitialisé pour {employe.matricule}")
        return True, password

    # ==================== VALIDATION D'EMBAUCHE ====================

    @staticmethod
    def validate_embauche(employe: 'ZY00') -> Tuple[bool, str]:
        """
        Valide une pré-embauche (passe de PRE à SAL).

        Args:
            employe: Instance de ZY00

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if employe.type_dossier != 'PRE':
            return False, "Cet employé n'est pas en pré-embauche."

        employe.type_dossier = 'SAL'
        employe.date_validation_embauche = timezone.now().date()
        employe.save(update_fields=['type_dossier', 'date_validation_embauche'])

        logger.info(f"Embauche validée pour {employe.matricule}")
        return True, f"Embauche de {employe.nom} {employe.prenoms} validée avec succès!"

    @staticmethod
    def cancel_embauche(employe: 'ZY00') -> Tuple[bool, str]:
        """
        Annule une pré-embauche (supprime l'employé et ses données).

        Args:
            employe: Instance de ZY00

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if employe.type_dossier != 'PRE':
            return False, "Seules les pré-embauches peuvent être annulées."

        matricule = employe.matricule
        nom_complet = f"{employe.nom} {employe.prenoms}"

        # Supprimer le compte utilisateur si existant
        if employe.user:
            employe.user.delete()

        # Supprimer l'employé (les données liées seront supprimées en cascade)
        employe.delete()

        logger.info(f"Pré-embauche annulée pour {matricule}")
        return True, f"Pré-embauche de {nom_complet} annulée."

    # ==================== VÉRIFICATIONS ====================

    @staticmethod
    def can_validate_embauche(employe: 'ZY00') -> Tuple[bool, str]:
        """
        Vérifie si une embauche peut être validée.

        Args:
            employe: Instance de ZY00

        Returns:
            Tuple[bool, str]: (can_validate, reason)
        """
        if employe.type_dossier != 'PRE':
            return False, "L'employé n'est pas en pré-embauche."

        # Vérifier qu'il a un contrat actif
        if not employe.contrats.filter(actif=True).exists():
            return False, "L'employé n'a pas de contrat actif."

        # Vérifier qu'il a une affectation active
        if not employe.affectations.filter(date_fin__isnull=True).exists():
            return False, "L'employé n'a pas d'affectation active."

        return True, "L'embauche peut être validée."

    @staticmethod
    def get_pre_embauches_pending() -> 'QuerySet':
        """
        Retourne la liste des pré-embauches en attente de validation.

        Returns:
            QuerySet[ZY00]: Les employés en pré-embauche
        """
        from employee.models import ZY00

        return ZY00.objects.filter(
            type_dossier='PRE',
            etat='actif'
        ).order_by('-matricule')

    @staticmethod
    def get_embauche_stats() -> Dict[str, int]:
        """
        Retourne des statistiques sur les embauches.

        Returns:
            dict: {
                'pre_embauches': int,
                'salaries_actifs': int,
                'salaries_inactifs': int,
                'total': int
            }
        """
        from employee.models import ZY00

        return {
            'pre_embauches': ZY00.objects.filter(type_dossier='PRE').count(),
            'salaries_actifs': ZY00.objects.filter(type_dossier='SAL', etat='actif').count(),
            'salaries_inactifs': ZY00.objects.filter(type_dossier='SAL', etat='inactif').count(),
            'total': ZY00.objects.count(),
        }

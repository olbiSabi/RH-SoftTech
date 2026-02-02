"""
Validateurs personnalisés pour le module GAC (Gestion des Achats & Commandes).

Ce module contient les validateurs utilisés pour vérifier la cohérence
et la validité des données avant leur enregistrement.
"""

import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def valider_siret(value):
    """
    Valide le format et la clé de contrôle d'un numéro SIRET.

    Le SIRET est composé de 14 chiffres dont les 9 premiers constituent
    le numéro SIREN et les 5 suivants le NIC (Numéro Interne de Classement).

    Args:
        value: Le numéro SIRET à valider

    Raises:
        ValidationError: Si le SIRET est invalide
    """
    if not value:
        raise ValidationError(_('Le numéro SIRET est obligatoire.'))

    # Nettoyer le SIRET (enlever espaces et caractères spéciaux)
    siret = re.sub(r'[^0-9]', '', str(value))

    # Vérifier la longueur
    if len(siret) != 14:
        raise ValidationError(
            _('Le numéro SIRET doit contenir exactement 14 chiffres. '
              f'Vous avez fourni {len(siret)} chiffres.')
        )

    # Vérifier que ce sont bien des chiffres
    if not siret.isdigit():
        raise ValidationError(_('Le SIRET ne doit contenir que des chiffres.'))

    # Algorithme de Luhn pour vérifier la clé de contrôle
    total = 0
    for i, digit in enumerate(siret):
        n = int(digit)
        if i % 2 == 0:  # Position paire (0, 2, 4, ...)
            n *= 2
            if n > 9:
                n -= 9
        total += n

    if total % 10 != 0:
        raise ValidationError(
            _('Le numéro SIRET est invalide (erreur de clé de contrôle).')
        )

    return siret


def valider_numero_tva(value):
    """
    Valide le format d'un numéro de TVA intracommunautaire français.

    Format français: FR + clé sur 2 chiffres + SIREN sur 9 chiffres
    Exemple: FR12345678901

    Args:
        value: Le numéro de TVA à valider

    Raises:
        ValidationError: Si le numéro de TVA est invalide
    """
    if not value:
        return  # Optionnel

    # Nettoyer le numéro
    tva = re.sub(r'\s+', '', str(value).upper())

    # Vérifier le format général (2 lettres + 11 chiffres)
    if not re.match(r'^[A-Z]{2}\d{11}$', tva):
        raise ValidationError(
            _('Le numéro de TVA doit être au format: FR + 11 chiffres '
              '(ex: FR12345678901)')
        )

    # Vérifier que c'est bien français
    if not tva.startswith('FR'):
        raise ValidationError(
            _('Seuls les numéros de TVA français (FR) sont acceptés.')
        )

    return tva


def valider_iban(value):
    """
    Valide le format d'un IBAN français.

    Format français: FR + clé sur 2 chiffres + code banque + code guichet +
                     numéro de compte + clé RIB
    Longueur: 27 caractères

    Args:
        value: L'IBAN à valider

    Raises:
        ValidationError: Si l'IBAN est invalide
    """
    if not value:
        return  # Optionnel

    # Nettoyer l'IBAN
    iban = re.sub(r'\s+', '', str(value).upper())

    # Vérifier la longueur pour un IBAN français
    if not iban.startswith('FR'):
        raise ValidationError(_('Seuls les IBAN français sont acceptés.'))

    if len(iban) != 27:
        raise ValidationError(
            _('Un IBAN français doit contenir 27 caractères. '
              f'Vous avez fourni {len(iban)} caractères.')
        )

    # Vérifier le format (2 lettres + 25 chiffres)
    if not re.match(r'^FR\d{25}$', iban):
        raise ValidationError(
            _('Format IBAN invalide. Attendu: FR suivi de 25 chiffres.')
        )

    # Validation selon l'algorithme IBAN (modulo 97)
    # Déplacer les 4 premiers caractères à la fin
    reordered = iban[4:] + iban[:4]

    # Remplacer les lettres par des chiffres (A=10, B=11, ..., Z=35)
    numeric = ''
    for char in reordered:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - ord('A') + 10)

    # Vérifier le modulo 97
    if int(numeric) % 97 != 1:
        raise ValidationError(
            _('L\'IBAN est invalide (erreur de clé de contrôle).')
        )

    return iban


def valider_montant_positif(value):
    """
    Valide qu'un montant est positif.

    Args:
        value: Le montant à valider

    Raises:
        ValidationError: Si le montant est négatif
    """
    if value is not None and value < 0:
        raise ValidationError(_('Le montant doit être positif.'))


def valider_montant_non_nul(value):
    """
    Valide qu'un montant est strictement positif (non nul).

    Args:
        value: Le montant à valider

    Raises:
        ValidationError: Si le montant est nul ou négatif
    """
    if value is not None and value <= 0:
        raise ValidationError(_('Le montant doit être strictement positif.'))


def valider_taux_tva(value):
    """
    Valide un taux de TVA.

    Args:
        value: Le taux de TVA à valider (en pourcentage)

    Raises:
        ValidationError: Si le taux est invalide
    """
    if value is None:
        return

    if value < 0 or value > 100:
        raise ValidationError(
            _('Le taux de TVA doit être compris entre 0 et 100%.')
        )

    # Vérifier que c'est un taux de TVA français valide
    taux_valides = [Decimal('0'), Decimal('2.1'), Decimal('5.5'),
                    Decimal('10'), Decimal('20')]

    if value not in taux_valides:
        raise ValidationError(
            _('Taux de TVA non standard. Taux français valides: '
              '0%, 2,1%, 5,5%, 10%, 20%')
        )


def valider_pourcentage(value):
    """
    Valide un pourcentage (entre 0 et 100).

    Args:
        value: Le pourcentage à valider

    Raises:
        ValidationError: Si le pourcentage est invalide
    """
    if value is not None and (value < 0 or value > 100):
        raise ValidationError(
            _('La valeur doit être comprise entre 0 et 100%.')
        )


def valider_quantite(value):
    """
    Valide une quantité.

    Args:
        value: La quantité à valider

    Raises:
        ValidationError: Si la quantité est invalide
    """
    if value is not None and value <= 0:
        raise ValidationError(_('La quantité doit être strictement positive.'))

    # Limiter la précision à 2 décimales
    if value is not None:
        if abs(value - round(value, 2)) > 0.001:
            raise ValidationError(
                _('La quantité ne peut avoir plus de 2 décimales.')
            )


def valider_code_unique(model, code, instance=None):
    """
    Valide l'unicité d'un code dans un modèle.

    Args:
        model: Le modèle Django
        code: Le code à valider
        instance: L'instance en cours de modification (None pour création)

    Raises:
        ValidationError: Si le code existe déjà
    """
    qs = model.objects.filter(code=code)

    # Exclure l'instance en cours de modification
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        raise ValidationError(
            _(f'Un élément avec le code "{code}" existe déjà.')
        )


def valider_email_professionnel(value):
    """
    Valide qu'un email est professionnel (pas gmail, hotmail, etc.).

    Args:
        value: L'email à valider

    Raises:
        ValidationError: Si l'email est personnel
    """
    if not value:
        return

    domaines_personnels = [
        'gmail.com', 'hotmail.com', 'hotmail.fr', 'outlook.com',
        'yahoo.com', 'yahoo.fr', 'live.com', 'live.fr',
        'laposte.net', 'orange.fr', 'wanadoo.fr', 'free.fr',
        'sfr.fr', 'bbox.fr'
    ]

    domaine = value.lower().split('@')[-1]

    if domaine in domaines_personnels:
        raise ValidationError(
            _('Veuillez utiliser une adresse email professionnelle.')
        )


def valider_telephone_francais(value):
    """
    Valide le format d'un numéro de téléphone français.

    Args:
        value: Le numéro de téléphone à valider

    Raises:
        ValidationError: Si le format est invalide
    """
    if not value:
        return

    # Nettoyer le numéro
    telephone = re.sub(r'[^0-9+]', '', str(value))

    # Formats acceptés:
    # - 0123456789 (10 chiffres)
    # - +33123456789 (indicatif international)

    if telephone.startswith('+33'):
        telephone = '0' + telephone[3:]  # Convertir en format national

    if len(telephone) != 10:
        raise ValidationError(
            _('Le numéro de téléphone doit contenir 10 chiffres.')
        )

    if not telephone.startswith('0'):
        raise ValidationError(
            _('Le numéro de téléphone doit commencer par 0.')
        )

    # Vérifier que le deuxième chiffre est valide (1-9)
    if telephone[1] not in '123456789':
        raise ValidationError(
            _('Format de numéro de téléphone invalide.')
        )


def valider_code_postal_francais(value):
    """
    Valide un code postal français.

    Args:
        value: Le code postal à valider

    Raises:
        ValidationError: Si le code postal est invalide
    """
    if not value:
        return

    # Code postal français: 5 chiffres
    if not re.match(r'^\d{5}$', str(value)):
        raise ValidationError(
            _('Le code postal doit contenir 5 chiffres.')
        )

    # Vérifier que le département existe (01 à 95, 971 à 976)
    dept = int(str(value)[:2])
    if not (1 <= dept <= 95 or 971 <= int(str(value)[:3]) <= 976):
        raise ValidationError(
            _('Code postal français invalide.')
        )


def valider_periode_budget(date_debut, date_fin):
    """
    Valide la cohérence d'une période budgétaire.

    Args:
        date_debut: Date de début
        date_fin: Date de fin

    Raises:
        ValidationError: Si la période est incohérente
    """
    if date_debut and date_fin:
        if date_debut >= date_fin:
            raise ValidationError(
                _('La date de fin doit être postérieure à la date de début.')
            )

        # Vérifier que la période ne dépasse pas 3 ans
        duree = (date_fin - date_debut).days
        if duree > 1095:  # 3 ans
            raise ValidationError(
                _('La période budgétaire ne peut pas dépasser 3 ans.')
            )


def valider_delai_livraison(value):
    """
    Valide un délai de livraison (en jours).

    Args:
        value: Le délai en jours

    Raises:
        ValidationError: Si le délai est invalide
    """
    if value is not None:
        if value < 0:
            raise ValidationError(_('Le délai ne peut pas être négatif.'))

        if value > 365:
            raise ValidationError(
                _('Le délai de livraison ne peut pas dépasser 365 jours.')
            )

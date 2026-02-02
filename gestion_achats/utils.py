"""
Fonctions utilitaires pour le module Gestion des Achats & Commandes (GAC).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone


def generer_numero_demande():
    """
    Génère un numéro de demande d'achat unique.

    Format: DA-YYYY-NNNN
    Exemple: DA-2026-0001

    Returns:
        str: Numéro de demande généré
    """
    from gestion_achats.models import GACDemandeAchat

    annee = timezone.now().year
    dernier_numero = GACDemandeAchat.objects.filter(
        numero__startswith=f'DA-{annee}-'
    ).count()

    return f'DA-{annee}-{str(dernier_numero + 1).zfill(4)}'


def generer_numero_bon_commande():
    """
    Génère un numéro de bon de commande unique.

    Format: BC-YYYY-NNNN
    Exemple: BC-2026-0001

    Returns:
        str: Numéro de bon de commande généré
    """
    from gestion_achats.models import GACBonCommande

    annee = timezone.now().year
    dernier_numero = GACBonCommande.objects.filter(
        numero__startswith=f'BC-{annee}-'
    ).count()

    return f'BC-{annee}-{str(dernier_numero + 1).zfill(4)}'


def generer_numero_reception():
    """
    Génère un numéro de réception unique.

    Format: REC-YYYY-NNNN
    Exemple: REC-2026-0001

    Returns:
        str: Numéro de réception généré
    """
    from gestion_achats.models import GACReception

    annee = timezone.now().year
    dernier_numero = GACReception.objects.filter(
        numero__startswith=f'REC-{annee}-'
    ).count()

    return f'REC-{annee}-{str(dernier_numero + 1).zfill(4)}'


def generer_numero_bon_retour():
    """
    Génère un numéro de bon de retour unique.

    Format: BR-YYYY-NNNN
    Exemple: BR-2026-0001

    Returns:
        str: Numéro de bon de retour généré
    """
    from gestion_achats.models import GACBonRetour

    annee = timezone.now().year
    dernier_numero = GACBonRetour.objects.filter(
        numero__startswith=f'BR-{annee}-'
    ).count()

    return f'BR-{annee}-{str(dernier_numero + 1).zfill(4)}'


def generer_code_categorie():
    """
    Génère un code de catégorie unique.

    Format: CAT-NNNN
    Exemple: CAT-0001

    Returns:
        str: Code de catégorie généré
    """
    from gestion_achats.models import GACCategorie

    dernier_numero = GACCategorie.objects.filter(
        code__startswith='CAT-'
    ).count()

    return f'CAT-{str(dernier_numero + 1).zfill(4)}'


def calculer_montant_ttc(montant_ht, taux_tva=None):
    """
    Calcule le montant TTC à partir du montant HT et du taux de TVA.

    Args:
        montant_ht (Decimal): Montant hors taxe
        taux_tva (Decimal, optional): Taux de TVA en pourcentage. 
                                       Défaut: TAUX_TVA_DEFAUT (20%)

    Returns:
        Decimal: Montant TTC arrondi à 2 décimales
    """
    from gestion_achats.constants import TAUX_TVA_DEFAUT

    if taux_tva is None:
        taux_tva = Decimal(str(TAUX_TVA_DEFAUT))

    montant_ht = Decimal(str(montant_ht))
    taux_tva = Decimal(str(taux_tva))

    montant_tva = (montant_ht * taux_tva) / Decimal('100')
    montant_ttc = montant_ht + montant_tva

    return montant_ttc.quantize(Decimal('0.01'))


def calculer_montant_tva(montant_ht, taux_tva=None):
    """
    Calcule le montant de TVA à partir du montant HT et du taux de TVA.

    Args:
        montant_ht (Decimal): Montant hors taxe
        taux_tva (Decimal, optional): Taux de TVA en pourcentage. 
                                       Défaut: TAUX_TVA_DEFAUT (20%)

    Returns:
        Decimal: Montant de TVA arrondi à 2 décimales
    """
    from gestion_achats.constants import TAUX_TVA_DEFAUT

    if taux_tva is None:
        taux_tva = Decimal(str(TAUX_TVA_DEFAUT))

    montant_ht = Decimal(str(montant_ht))
    taux_tva = Decimal(str(taux_tva))

    montant_tva = (montant_ht * taux_tva) / Decimal('100')

    return montant_tva.quantize(Decimal('0.01'))


def calculer_jours_ouvres(date_debut, date_fin):
    """
    Calcule le nombre de jours ouvrés entre deux dates.

    Args:
        date_debut (date): Date de début
        date_fin (date): Date de fin

    Returns:
        int: Nombre de jours ouvrés (excluant samedis et dimanches)
    """
    if isinstance(date_debut, datetime):
        date_debut = date_debut.date()
    if isinstance(date_fin, datetime):
        date_fin = date_fin.date()

    jours = 0
    current_date = date_debut

    while current_date <= date_fin:
        # 0 = Lundi, 6 = Dimanche
        if current_date.weekday() < 5:  # Lundi à Vendredi
            jours += 1
        current_date += timedelta(days=1)

    return jours


def determiner_validateur_n2(demande):
    """
    Détermine le validateur N2 selon les règles métier.

    Règles:
    - Si montant > 10 000 € → Direction générale
    - Si catégorie IT → Responsable IT
    - Sinon → Responsable achats

    Args:
        demande (GACDemandeAchat): La demande d'achat

    Returns:
        ZY00: L'employé validateur N2, ou None si non trouvé
    """
    from employee.models import ZY00, ZYRO

    # Règle 1: Montant > 10 000 € → Direction générale
    if demande.montant_total_ttc > Decimal('10000.00'):
        try:
            role_dg = ZYRO.objects.get(CODE='DIRECTEUR_GENERAL')
            validateur = ZY00.objects.filter(
                roles_attribues__role=role_dg,
                roles_attribues__actif=True,
                etat='actif'
            ).first()
            if validateur:
                return validateur
        except ZYRO.DoesNotExist:
            pass

    # Règle 2: Catégorie IT → Responsable IT
    # (À implémenter si catégorisation disponible sur demandes)

    # Règle 3: Par défaut → Responsable achats
    try:
        role_achats = ZYRO.objects.get(CODE='RESPONSABLE_ACHATS')
        validateur = ZY00.objects.filter(
            roles_attribues__role=role_achats,
            roles_attribues__actif=True,
            etat='actif'
        ).first()
        if validateur:
            return validateur
    except ZYRO.DoesNotExist:
        pass

    # Fallback: Premier utilisateur avec rôle ACHETEUR
    try:
        role_acheteur = ZYRO.objects.get(CODE='ACHETEUR')
        validateur = ZY00.objects.filter(
            roles_attribues__role=role_acheteur,
            roles_attribues__actif=True,
            etat='actif'
        ).first()
        return validateur
    except ZYRO.DoesNotExist:
        return None


def formater_montant(montant, symbole='€'):
    """
    Formate un montant pour l'affichage.

    Args:
        montant (Decimal): Montant à formater
        symbole (str): Symbole monétaire

    Returns:
        str: Montant formaté (ex: "1 234,56 €")
    """
    if montant is None:
        return f"0,00 {symbole}"

    montant = Decimal(str(montant))
    
    # Arrondir à 2 décimales
    montant_arrondi = montant.quantize(Decimal('0.01'))
    
    # Séparer partie entière et décimale
    partie_entiere = int(montant_arrondi)
    partie_decimale = abs(montant_arrondi - Decimal(partie_entiere))
    
    # Formater la partie entière avec séparateur de milliers
    partie_entiere_str = f"{partie_entiere:,}".replace(',', ' ')
    
    # Formater la partie décimale
    decimales = int((partie_decimale * 100).quantize(Decimal('1')))
    
    return f"{partie_entiere_str},{decimales:02d} {symbole}"


def valider_siret(siret):
    """
    Valide un numéro SIRET français.

    Args:
        siret (str): Numéro SIRET à valider (14 chiffres)

    Returns:
        bool: True si valide, False sinon
    """
    if not siret:
        return False

    # Enlever les espaces
    siret = siret.replace(' ', '')

    # Vérifier la longueur
    if len(siret) != 14:
        return False

    # Vérifier que ce sont des chiffres
    if not siret.isdigit():
        return False

    # Algorithme de Luhn pour valider le SIRET
    total = 0
    for i, digit in enumerate(siret):
        value = int(digit)
        if i % 2 == 0:
            value *= 2
            if value > 9:
                value -= 9
        total += value

    return total % 10 == 0


def valider_email(email):
    """
    Valide basiquement une adresse email.

    Args:
        email (str): Adresse email à valider

    Returns:
        bool: True si valide, False sinon
    """
    import re

    if not email:
        return False

    # Pattern basique pour email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return re.match(pattern, email) is not None


def formater_telephone(telephone):
    """
    Formate un numéro de téléphone français.

    Args:
        telephone (str): Numéro de téléphone

    Returns:
        str: Numéro formaté (ex: "01 23 45 67 89")
    """
    if not telephone:
        return ""

    # Enlever tous les caractères non numériques
    chiffres = ''.join(c for c in telephone if c.isdigit())

    # Formater par groupes de 2
    if len(chiffres) == 10:
        return ' '.join([chiffres[i:i+2] for i in range(0, 10, 2)])

    return telephone


def calculer_delai_livraison(date_livraison):
    """
    Calcule le délai en jours avant une date de livraison.

    Args:
        date_livraison (date): Date de livraison

    Returns:
        int: Nombre de jours (négatif si en retard)
    """
    if not date_livraison:
        return None

    if isinstance(date_livraison, datetime):
        date_livraison = date_livraison.date()

    aujourd_hui = timezone.now().date()
    delta = date_livraison - aujourd_hui

    return delta.days


def est_en_retard(date_livraison):
    """
    Détermine si une livraison est en retard.

    Args:
        date_livraison (date): Date de livraison prévue

    Returns:
        bool: True si en retard, False sinon
    """
    delai = calculer_delai_livraison(date_livraison)
    return delai is not None and delai < 0

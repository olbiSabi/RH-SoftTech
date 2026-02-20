"""
Fonctions utilitaires pour le module Gestion des Achats & Commandes (GAC).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction


def _generer_numero(model_class, prefix, champ='numero'):
    """
    Genere un numero sequentiel unique avec verrouillage transactionnel.

    Utilise select_for_update() pour eviter les doublons en acces concurrent.

    Args:
        model_class: Le modele Django
        prefix: Le prefixe du numero (ex: 'DA-2026-')
        champ: Le nom du champ contenant le numero

    Returns:
        str: Le nouveau numero genere
    """
    with transaction.atomic():
        filtre = {f'{champ}__startswith': prefix}
        dernier = (
            model_class.objects
            .select_for_update()
            .filter(**filtre)
            .order_by(f'-{champ}')
            .values_list(champ, flat=True)
            .first()
        )

        if dernier:
            dernier_numero = int(dernier.split('-')[-1])
        else:
            dernier_numero = 0

        return f'{prefix}{str(dernier_numero + 1).zfill(4)}'


def generer_numero_demande():
    """
    Genere un numero de demande d'achat unique.

    Format: DA-YYYY-NNNN
    Exemple: DA-2026-0001
    """
    from gestion_achats.models import GACDemandeAchat

    annee = timezone.now().year
    return _generer_numero(GACDemandeAchat, f'DA-{annee}-')


def generer_numero_bon_commande():
    """
    Genere un numero de bon de commande unique.

    Format: BC-YYYY-NNNN
    Exemple: BC-2026-0001
    """
    from gestion_achats.models import GACBonCommande

    annee = timezone.now().year
    return _generer_numero(GACBonCommande, f'BC-{annee}-')


def generer_numero_reception():
    """
    Genere un numero de reception unique.

    Format: REC-YYYY-NNNN
    Exemple: REC-2026-0001
    """
    from gestion_achats.models import GACReception

    annee = timezone.now().year
    return _generer_numero(GACReception, f'REC-{annee}-')


def generer_numero_bon_retour():
    """
    Genere un numero de bon de retour unique.

    Format: BR-YYYY-NNNN
    Exemple: BR-2026-0001
    """
    from gestion_achats.models import GACBonRetour

    annee = timezone.now().year
    return _generer_numero(GACBonRetour, f'BR-{annee}-')


def generer_code_categorie():
    """
    Genere un code de categorie unique.

    Format: CAT-NNNN
    Exemple: CAT-0001
    """
    from gestion_achats.models import GACCategorie

    return _generer_numero(GACCategorie, 'CAT-', champ='code')


def generer_code_fournisseur():
    """
    Genere un code fournisseur unique.

    Format: FRN-NNNN
    Exemple: FRN-0001
    """
    from gestion_achats.models import GACFournisseur

    return _generer_numero(GACFournisseur, 'FRN-', champ='code')


def generer_code_article():
    """
    Genere un code article unique.

    Format: ART-NNNN
    Exemple: ART-0001
    """
    from gestion_achats.models import GACArticle

    return _generer_numero(GACArticle, 'ART-', champ='reference')


def generer_code_budget():
    """
    Genere un code budget unique.

    Format: BUD-NNNN
    Exemple: BUD-0001
    """
    from gestion_achats.models import GACBudget

    return _generer_numero(GACBudget, 'BUD-', champ='code')


def calculer_montant_ttc(montant_ht, taux_tva=None):
    """
    Calcule le montant TTC a partir du montant HT et du taux de TVA.

    Args:
        montant_ht (Decimal): Montant hors taxe
        taux_tva (Decimal, optional): Taux de TVA en pourcentage.
                                       Defaut: TAUX_TVA_DEFAUT (20%)

    Returns:
        Decimal: Montant TTC arrondi a 2 decimales
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
    Calcule le montant de TVA a partir du montant HT et du taux de TVA.

    Args:
        montant_ht (Decimal): Montant hors taxe
        taux_tva (Decimal, optional): Taux de TVA en pourcentage.
                                       Defaut: TAUX_TVA_DEFAUT (20%)

    Returns:
        Decimal: Montant de TVA arrondi a 2 decimales
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
    Calcule le nombre de jours ouvres entre deux dates.

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin

    Returns:
        int: Nombre de jours ouvres (excluant samedis et dimanches)
    """
    if isinstance(date_debut, datetime):
        date_debut = date_debut.date()
    if isinstance(date_fin, datetime):
        date_fin = date_fin.date()

    jours = 0
    current_date = date_debut

    while current_date <= date_fin:
        # 0 = Lundi, 6 = Dimanche
        if current_date.weekday() < 5:  # Lundi a Vendredi
            jours += 1
        current_date += timedelta(days=1)

    return jours


def determiner_validateur_n2(demande):
    """
    Determine le validateur N2 selon les regles metier.

    Regles:
    - Si montant > 10 000 FCFA -> Direction generale
    - Si categorie IT -> Responsable IT
    - Sinon -> Responsable achats

    Args:
        demande (GACDemandeAchat): La demande d'achat

    Returns:
        ZY00: L'employe validateur N2, ou None si non trouve
    """
    from employee.models import ZY00, ZYRO

    # Regle 1: Montant > 10 000 FCFA -> Direction generale
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

    # Regle 2: Categorie IT -> Responsable IT
    # (A implementer si categorisation disponible sur demandes)

    # Regle 3: Par defaut -> Responsable achats
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

    # Fallback 1: Premier utilisateur avec role ACHETEUR
    try:
        role_acheteur = ZYRO.objects.get(CODE='ACHETEUR')
        validateur = ZY00.objects.filter(
            roles_attribues__role=role_acheteur,
            roles_attribues__actif=True,
            etat='actif'
        ).first()
        if validateur:
            return validateur
    except ZYRO.DoesNotExist:
        pass

    # Fallback 2: Premier utilisateur avec role ADMIN_GAC
    try:
        role_admin_gac = ZYRO.objects.get(CODE='ADMIN_GAC')
        validateur = ZY00.objects.filter(
            roles_attribues__role=role_admin_gac,
            roles_attribues__actif=True,
            etat='actif'
        ).first()
        if validateur:
            return validateur
    except ZYRO.DoesNotExist:
        pass

    return None


def formater_montant(montant, symbole='FCFA'):
    """
    Formate un montant pour l'affichage.

    Args:
        montant (Decimal): Montant a formater
        symbole (str): Symbole monetaire

    Returns:
        str: Montant formate (ex: "1 234,56 FCFA")
    """
    if montant is None:
        return f"0,00 {symbole}"

    montant = Decimal(str(montant))

    # Arrondir a 2 decimales
    montant_arrondi = montant.quantize(Decimal('0.01'))

    # Separer partie entiere et decimale
    partie_entiere = int(montant_arrondi)
    partie_decimale = abs(montant_arrondi - Decimal(partie_entiere))

    # Formater la partie entiere avec separateur de milliers
    partie_entiere_str = f"{partie_entiere:,}".replace(',', ' ')

    # Formater la partie decimale
    decimales = int((partie_decimale * 100).quantize(Decimal('1')))

    return f"{partie_entiere_str},{decimales:02d} {symbole}"


def valider_nif(nif):
    """
    Valide un Numero d'Identification Fiscale (NIF) togolais.

    Args:
        nif (str): Numero NIF a valider (9 a 10 chiffres)

    Returns:
        bool: True si valide, False sinon
    """
    if not nif:
        return True  # Le NIF est optionnel

    # Enlever les espaces
    nif = nif.replace(' ', '')

    # Verifier la longueur (9 ou 10 chiffres)
    if len(nif) < 9 or len(nif) > 10:
        return False

    # Verifier que ce sont des chiffres
    if not nif.isdigit():
        return False

    return True


def valider_email(email):
    """
    Valide basiquement une adresse email.

    Args:
        email (str): Adresse email a valider

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
    Formate un numero de telephone.

    Args:
        telephone (str): Numero de telephone

    Returns:
        str: Numero formate (ex: "01 23 45 67 89")
    """
    if not telephone:
        return ""

    # Enlever tous les caracteres non numeriques
    chiffres = ''.join(c for c in telephone if c.isdigit())

    # Formater par groupes de 2
    if len(chiffres) == 10:
        return ' '.join([chiffres[i:i+2] for i in range(0, 10, 2)])

    return telephone


def calculer_delai_livraison(date_livraison):
    """
    Calcule le delai en jours avant une date de livraison.

    Args:
        date_livraison (date): Date de livraison

    Returns:
        int: Nombre de jours (negatif si en retard)
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
    Determine si une livraison est en retard.

    Args:
        date_livraison (date): Date de livraison prevue

    Returns:
        bool: True si en retard, False sinon
    """
    delai = calculer_delai_livraison(date_livraison)
    return delai is not None and delai < 0

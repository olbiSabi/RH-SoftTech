"""
Constantes du module Gestion des Achats & Commandes (GAC).
"""

# ==============================================================================
# STATUTS DES DEMANDES D'ACHAT
# ==============================================================================

STATUT_DEMANDE_BROUILLON = 'BROUILLON'
STATUT_DEMANDE_SOUMISE = 'SOUMISE'
STATUT_DEMANDE_VALIDEE_N1 = 'VALIDEE_N1'
STATUT_DEMANDE_VALIDEE_N2 = 'VALIDEE_N2'
STATUT_DEMANDE_CONVERTIE_BC = 'CONVERTIE_BC'
STATUT_DEMANDE_REFUSEE = 'REFUSEE'
STATUT_DEMANDE_ANNULEE = 'ANNULEE'

STATUT_DEMANDE_CHOICES = [
    (STATUT_DEMANDE_BROUILLON, 'Brouillon'),
    (STATUT_DEMANDE_SOUMISE, 'Soumise'),
    (STATUT_DEMANDE_VALIDEE_N1, 'Validée N1'),
    (STATUT_DEMANDE_VALIDEE_N2, 'Validée N2'),
    (STATUT_DEMANDE_CONVERTIE_BC, 'Convertie en BC'),
    (STATUT_DEMANDE_REFUSEE, 'Refusée'),
    (STATUT_DEMANDE_ANNULEE, 'Annulée'),
]

# ==============================================================================
# STATUTS DES BONS DE COMMANDE
# ==============================================================================

STATUT_BC_BROUILLON = 'BROUILLON'
STATUT_BC_EMIS = 'EMIS'
STATUT_BC_ENVOYE = 'ENVOYE'
STATUT_BC_CONFIRME = 'CONFIRME'
STATUT_BC_RECU_PARTIEL = 'RECU_PARTIEL'
STATUT_BC_RECU_COMPLET = 'RECU_COMPLET'
STATUT_BC_ANNULE = 'ANNULE'

STATUT_BC_CHOICES = [
    (STATUT_BC_BROUILLON, 'Brouillon'),
    (STATUT_BC_EMIS, 'Émis'),
    (STATUT_BC_ENVOYE, 'Envoyé'),
    (STATUT_BC_CONFIRME, 'Confirmé'),
    (STATUT_BC_RECU_PARTIEL, 'Reçu partiel'),
    (STATUT_BC_RECU_COMPLET, 'Reçu complet'),
    (STATUT_BC_ANNULE, 'Annulé'),
]

# ==============================================================================
# STATUTS DES RÉCEPTIONS
# ==============================================================================

STATUT_RECEPTION_BROUILLON = 'BROUILLON'
STATUT_RECEPTION_VALIDEE = 'VALIDEE'
STATUT_RECEPTION_ANNULEE = 'ANNULEE'

STATUT_RECEPTION_CHOICES = [
    (STATUT_RECEPTION_BROUILLON, 'Brouillon'),
    (STATUT_RECEPTION_VALIDEE, 'Validée'),
    (STATUT_RECEPTION_ANNULEE, 'Annulée'),
]

# ==============================================================================
# STATUTS BON DE RETOUR
# ==============================================================================

STATUT_RETOUR_BROUILLON = 'BROUILLON'
STATUT_RETOUR_EMIS = 'EMIS'
STATUT_RETOUR_ENVOYE = 'ENVOYE'
STATUT_RETOUR_RECU_FOURNISSEUR = 'RECU_FOURNISSEUR'
STATUT_RETOUR_REMBOURSE = 'REMBOURSE'
STATUT_RETOUR_AVOIR_EMIS = 'AVOIR_EMIS'
STATUT_RETOUR_ANNULE = 'ANNULE'

STATUT_RETOUR_CHOICES = [
    (STATUT_RETOUR_BROUILLON, 'Brouillon'),
    (STATUT_RETOUR_EMIS, 'Émis'),
    (STATUT_RETOUR_ENVOYE, 'Envoyé au fournisseur'),
    (STATUT_RETOUR_RECU_FOURNISSEUR, 'Reçu par le fournisseur'),
    (STATUT_RETOUR_REMBOURSE, 'Remboursé'),
    (STATUT_RETOUR_AVOIR_EMIS, 'Avoir émis'),
    (STATUT_RETOUR_ANNULE, 'Annulé'),
]

# ==============================================================================
# PRIORITÉS DES DEMANDES
# ==============================================================================

PRIORITE_BASSE = 'BASSE'
PRIORITE_NORMALE = 'NORMALE'
PRIORITE_HAUTE = 'HAUTE'
PRIORITE_URGENTE = 'URGENTE'

PRIORITE_CHOICES = [
    (PRIORITE_BASSE, 'Basse'),
    (PRIORITE_NORMALE, 'Normale'),
    (PRIORITE_HAUTE, 'Haute'),
    (PRIORITE_URGENTE, 'Urgente'),
]

# ==============================================================================
# STATUTS DES FOURNISSEURS
# ==============================================================================

STATUT_FOURNISSEUR_ACTIF = 'ACTIF'
STATUT_FOURNISSEUR_INACTIF = 'INACTIF'
STATUT_FOURNISSEUR_SUSPENDU = 'SUSPENDU'

STATUT_FOURNISSEUR_CHOICES = [
    (STATUT_FOURNISSEUR_ACTIF, 'Actif'),
    (STATUT_FOURNISSEUR_INACTIF, 'Inactif'),
    (STATUT_FOURNISSEUR_SUSPENDU, 'Suspendu'),
]

# ==============================================================================
# STATUTS DES ARTICLES
# ==============================================================================

STATUT_ARTICLE_ACTIF = 'ACTIF'
STATUT_ARTICLE_INACTIF = 'INACTIF'

STATUT_ARTICLE_CHOICES = [
    (STATUT_ARTICLE_ACTIF, 'Actif'),
    (STATUT_ARTICLE_INACTIF, 'Inactif'),
]

# ==============================================================================
# UNITÉS DE MESURE
# ==============================================================================

UNITE_PIECE = 'piece'
UNITE_KG = 'kg'
UNITE_LITRE = 'litre'
UNITE_METRE = 'metre'
UNITE_METRE_CARRE = 'm2'
UNITE_METRE_CUBE = 'm3'
UNITE_HEURE = 'heure'
UNITE_JOUR = 'jour'
UNITE_LOT = 'lot'
UNITE_PAQUET = 'paquet'

UNITE_CHOICES = [
    (UNITE_PIECE, 'Pièce'),
    (UNITE_KG, 'Kilogramme'),
    (UNITE_LITRE, 'Litre'),
    (UNITE_METRE, 'Mètre'),
    (UNITE_METRE_CARRE, 'Mètre carré'),
    (UNITE_METRE_CUBE, 'Mètre cube'),
    (UNITE_HEURE, 'Heure'),
    (UNITE_JOUR, 'Jour'),
    (UNITE_LOT, 'Lot'),
    (UNITE_PAQUET, 'Paquet'),
]

# ==============================================================================
# ACTIONS HISTORIQUE
# ==============================================================================

ACTION_CREATION = 'CREATION'
ACTION_MODIFICATION = 'MODIFICATION'
ACTION_SOUMISSION = 'SOUMISSION'
ACTION_VALIDATION_N1 = 'VALIDATION_N1'
ACTION_VALIDATION_N2 = 'VALIDATION_N2'
ACTION_REFUS = 'REFUS'
ACTION_ANNULATION = 'ANNULATION'
ACTION_CONVERSION_BC = 'CONVERSION_BC'
ACTION_EMISSION = 'EMISSION'
ACTION_ENVOI = 'ENVOI'
ACTION_CONFIRMATION = 'CONFIRMATION'
ACTION_RECEPTION = 'RECEPTION'
ACTION_VALIDATION = 'VALIDATION'
ACTION_ENGAGEMENT = 'ENGAGEMENT'
ACTION_COMMANDE = 'COMMANDE'
ACTION_CONSOMMATION = 'CONSOMMATION'
ACTION_LIBERATION = 'LIBERATION'

ACTION_CHOICES = [
    (ACTION_CREATION, 'Création'),
    (ACTION_MODIFICATION, 'Modification'),
    (ACTION_SOUMISSION, 'Soumission'),
    (ACTION_VALIDATION_N1, 'Validation N1'),
    (ACTION_VALIDATION_N2, 'Validation N2'),
    (ACTION_REFUS, 'Refus'),
    (ACTION_ANNULATION, 'Annulation'),
    (ACTION_CONVERSION_BC, 'Conversion en BC'),
    (ACTION_EMISSION, 'Émission'),
    (ACTION_ENVOI, 'Envoi'),
    (ACTION_CONFIRMATION, 'Confirmation'),
    (ACTION_RECEPTION, 'Réception'),
    (ACTION_VALIDATION, 'Validation'),
    (ACTION_ENGAGEMENT, 'Engagement budgétaire'),
    (ACTION_COMMANDE, 'Commande budgétaire'),
    (ACTION_CONSOMMATION, 'Consommation budgétaire'),
    (ACTION_LIBERATION, 'Libération budgétaire'),
]

# ==============================================================================
# CONDITIONS DE PAIEMENT
# ==============================================================================

PAIEMENT_COMPTANT = 'COMPTANT'
PAIEMENT_30_JOURS = '30_JOURS'
PAIEMENT_45_JOURS = '45_JOURS'
PAIEMENT_60_JOURS = '60_JOURS'
PAIEMENT_90_JOURS = '90_JOURS'

PAIEMENT_CHOICES = [
    (PAIEMENT_COMPTANT, 'Comptant'),
    (PAIEMENT_30_JOURS, '30 jours'),
    (PAIEMENT_45_JOURS, '45 jours'),
    (PAIEMENT_60_JOURS, '60 jours'),
    (PAIEMENT_90_JOURS, '90 jours'),
]

# ==============================================================================
# SEUILS ET PARAMÈTRES
# ==============================================================================

# Montant TTC au-delà duquel une validation N2 est obligatoire
SEUIL_VALIDATION_N2 = 5000.00

# Délai SLA pour validation complète (jours ouvrés)
DELAI_SLA_VALIDATION = 5

# Taux de TVA par défaut (%)
TAUX_TVA_DEFAUT = 20.0

# Seuils d'alerte budgétaire par défaut (%)
SEUIL_ALERTE_BUDGET_1 = 80.0  # Premier niveau d'alerte
SEUIL_ALERTE_BUDGET_2 = 95.0  # Deuxième niveau d'alerte (critique)

# ==============================================================================
# LONGUEURS MAXIMALES DES CHAMPS
# ==============================================================================

MAX_LENGTH_CODE = 20
MAX_LENGTH_REFERENCE = 50
MAX_LENGTH_NUMERO = 30
MAX_LENGTH_NOM = 200
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_TELEPHONE = 20
MAX_LENGTH_NIF = 10  # Numéro d'Identification Fiscale (Togo)
MAX_LENGTH_TVA = 20
MAX_LENGTH_IBAN = 34

# Spécifications détaillées des modèles - Module GAC

## Table des matières
1. [Fournisseur (GACFournisseur)](#1-fournisseur)
2. [Catégorie (GACCategorie)](#2-catégorie)
3. [Article/Produit (GACArticle)](#3-article)
4. [Demande d'achat (GACDemandeAchat)](#4-demande-dachat)
5. [Ligne de demande (GACLigneDemandeAchat)](#5-ligne-de-demande)
6. [Bon de commande (GACBonCommande)](#6-bon-de-commande)
7. [Ligne de bon de commande (GACLigneBonCommande)](#7-ligne-de-bon-de-commande)
8. [Réception (GACReception)](#8-réception)
9. [Ligne de réception (GACLigneReception)](#9-ligne-de-réception)
10. [Budget (GACBudget)](#10-budget)
11. [Pièce jointe (GACPieceJointe)](#11-pièce-jointe)
12. [Historique (GACHistorique)](#12-historique)

---

## 1. Fournisseur (GACFournisseur)

### 1.1 Description
Représente un fournisseur de l'entreprise.

### 1.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| code | CharField(20) | unique, required | Code fournisseur (ex: FOUR-001) |
| raison_sociale | CharField(200) | required | Nom commercial |
| siret | CharField(14) | unique, null | Numéro SIRET |
| adresse | TextField | null | Adresse complète |
| code_postal | CharField(10) | null | Code postal |
| ville | CharField(100) | null | Ville |
| pays | CharField(100) | default='France' | Pays |
| telephone | CharField(20) | null | Téléphone principal |
| email | EmailField | null | Email principal |
| site_web | URLField | null | Site internet |
| contact_nom | CharField(100) | null | Nom contact principal |
| contact_prenom | CharField(100) | null | Prénom contact |
| contact_fonction | CharField(100) | null | Fonction du contact |
| contact_telephone | CharField(20) | null | Téléphone direct contact |
| contact_email | EmailField | null | Email du contact |
| categorie | CharField(50) | choices | Catégorie fournisseur |
| devise | CharField(3) | default='EUR' | Devise (EUR, USD, etc.) |
| delai_paiement | IntegerField | default=30 | Délai de paiement en jours |
| conditions_paiement | TextField | null | Conditions détaillées |
| mode_reglement_prefere | CharField(20) | choices | Mode de règlement |
| iban | CharField(34) | null | IBAN |
| bic | CharField(11) | null | BIC/SWIFT |
| note_evaluation | DecimalField(2,1) | null | Note de 1 à 5 |
| commentaire_evaluation | TextField | null | Commentaires sur le fournisseur |
| statut | CharField(20) | choices, default='ACTIF' | ACTIF, INACTIF, BLOQUE |
| date_premier_achat | DateField | null | Date du premier achat |
| montant_achats_annee | DecimalField(12,2) | default=0 | Total achats année en cours |
| nombre_commandes | IntegerField | default=0 | Nombre total de commandes |
| created_at | DateTimeField | auto_now_add | Date de création |
| updated_at | DateTimeField | auto_now | Date de modification |
| created_by | ForeignKey(ZY00) | null | Créé par |
| updated_by | ForeignKey(ZY00) | null | Modifié par |

### 1.3 Choices

\`\`\`python
CATEGORIE_CHOICES = [
    ('INFORMATIQUE', 'Informatique & Bureautique'),
    ('FOURNITURES', 'Fournitures de bureau'),
    ('MATERIEL', 'Matériel & Équipements'),
    ('SERVICES', 'Services & Prestations'),
    ('MOBILIER', 'Mobilier'),
    ('MAINTENANCE', 'Maintenance & Réparation'),
    ('FORMATION', 'Formation'),
    ('AUTRE', 'Autre'),
]

MODE_REGLEMENT_CHOICES = [
    ('VIREMENT', 'Virement bancaire'),
    ('CHEQUE', 'Chèque'),
    ('CARTE', 'Carte bancaire'),
    ('PRELEVEMENT', 'Prélèvement'),
]

STATUT_CHOICES = [
    ('ACTIF', 'Actif'),
    ('INACTIF', 'Inactif'),
    ('BLOQUE', 'Bloqué'),
]
\`\`\`

### 1.4 Méthodes

- \`__str__()\`: Retourne le code et la raison sociale
- \`save()\`: Auto-génère le code si non fourni
- \`get_absolute_url()\`: URL vers le détail fournisseur
- \`mettre_a_jour_statistiques()\`: Met à jour les stats (montant, nb commandes)
- \`evaluer(note, commentaire)\`: Enregistre une évaluation

### 1.5 Meta

\`\`\`python
class Meta:
    db_table = 'gac_fournisseur'
    verbose_name = 'Fournisseur'
    verbose_name_plural = 'Fournisseurs'
    ordering = ['raison_sociale']
    indexes = [
        models.Index(fields=['code']),
        models.Index(fields=['statut']),
        models.Index(fields=['categorie']),
    ]
\`\`\`

---

## 2. Catégorie (GACCategorie)

### 2.1 Description
Catégories hiérarchiques pour organiser les articles.

### 2.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| code | CharField(20) | unique | Code catégorie |
| libelle | CharField(100) | required | Libellé |
| description | TextField | null | Description |
| parent | ForeignKey(self) | null | Catégorie parente |
| niveau | IntegerField | default=1 | Niveau hiérarchique (1, 2, 3) |
| budget_annuel | DecimalField(12,2) | null | Budget annuel alloué |
| icone | CharField(50) | null | Icône Font Awesome |
| ordre | IntegerField | default=0 | Ordre d'affichage |
| actif | BooleanField | default=True | Actif/Inactif |
| created_at | DateTimeField | auto_now_add | Date de création |

### 2.3 Méthodes

- \`__str__()\`: Retourne le libellé complet avec hiérarchie
- \`get_chemin_complet()\`: Retourne "Parent > Enfant > Sous-enfant"
- \`get_enfants()\`: Retourne les sous-catégories
- \`get_articles_count()\`: Nombre d'articles dans la catégorie

---

## 3. Article (GACArticle)

### 3.1 Description
Catalogue des articles/produits référencés.

### 3.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| reference | CharField(50) | unique | Référence article |
| designation | CharField(200) | required | Désignation courte |
| description | TextField | null | Description détaillée |
| categorie | ForeignKey(GACCategorie) | null | Catégorie |
| unite_mesure | CharField(20) | choices | Unité (pièce, kg, lot...) |
| prix_unitaire_reference | DecimalField(10,2) | default=0 | Prix de référence HT |
| fournisseur_principal | ForeignKey(GACFournisseur) | null | Fournisseur principal |
| fournisseur_alternatif | ForeignKey(GACFournisseur) | null | Fournisseur alternatif |
| reference_fournisseur | CharField(100) | null | Référence chez le fournisseur |
| delai_livraison_jours | IntegerField | default=0 | Délai de livraison standard |
| stock_minimum | DecimalField(10,2) | default=0 | Stock minimum |
| stock_actuel | DecimalField(10,2) | default=0 | Stock actuel (si géré) |
| gere_en_stock | BooleanField | default=False | Géré en stock ? |
| lien_materiel | ForeignKey('materiel.ZYM') | null | Lien avec module matériel |
| specifications_techniques | TextField | null | Spécifications |
| lien_fiche_technique | URLField | null | URL fiche technique |
| image | ImageField | null | Image produit |
| tags | CharField(200) | null | Tags séparés par virgules |
| actif | BooleanField | default=True | Article actif |
| date_creation | DateTimeField | auto_now_add | Date de création |
| date_modification | DateTimeField | auto_now | Date de modification |
| created_by | ForeignKey(ZY00) | null | Créé par |

### 3.3 Choices

\`\`\`python
UNITE_MESURE_CHOICES = [
    ('PIECE', 'Pièce'),
    ('LOT', 'Lot'),
    ('KG', 'Kilogramme'),
    ('LITRE', 'Litre'),
    ('METRE', 'Mètre'),
    ('M2', 'Mètre carré'),
    ('HEURE', 'Heure'),
    ('JOUR', 'Jour'),
    ('FORFAIT', 'Forfait'),
]
\`\`\`

### 3.4 Méthodes

- \`__str__()\`: Retourne référence + désignation
- \`verifier_stock()\`: Vérifie si stock < minimum
- \`actualiser_prix(nouveau_prix)\`: Met à jour le prix de référence
- \`get_historique_prix()\`: Historique des prix

---

## 4. Demande d'achat (GACDemandeAchat)

### 4.1 Description
Demande d'achat émise par un employé.

### 4.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| numero | CharField(20) | unique | Numéro DA (ex: DA2026-0001) |
| date_demande | DateTimeField | auto_now_add | Date de création |
| demandeur | ForeignKey(ZY00) | required | Employé demandeur |
| departement | ForeignKey(ZYDE) | null | Département |
| service | CharField(100) | null | Service |
| priorite | CharField(20) | choices | Priorité de la demande |
| statut | CharField(20) | choices | Statut workflow |
| motif_demande | TextField | required | Justification |
| date_besoin | DateField | required | Date à laquelle le besoin est requis |
| lieu_livraison | CharField(200) | null | Adresse de livraison |
| contact_livraison | CharField(100) | null | Personne à contacter |
| montant_total_estime_ht | DecimalField(12,2) | default=0 | Montant total HT estimé |
| montant_total_estime_ttc | DecimalField(12,2) | default=0 | Montant total TTC estimé |
| budget_impute | ForeignKey(GACBudget) | null | Budget à imputer |
| validation_n1_requise | BooleanField | default=True | Validation N1 nécessaire |
| validateur_n1 | ForeignKey(ZY00) | null | Validateur niveau 1 (manager) |
| date_validation_n1 | DateTimeField | null | Date validation N1 |
| commentaire_validation_n1 | TextField | null | Commentaire N1 |
| validation_n2_requise | BooleanField | default=False | Validation N2 nécessaire |
| validateur_n2 | ForeignKey(ZY00) | null | Validateur niveau 2 |
| date_validation_n2 | DateTimeField | null | Date validation N2 |
| commentaire_validation_n2 | TextField | null | Commentaire N2 |
| motif_refus | TextField | null | Motif si refusée |
| acheteur_assigne | ForeignKey(ZY00) | null | Acheteur assigné |
| date_assignation_acheteur | DateTimeField | null | Date d'assignation |
| bon_commande | ForeignKey(GACBonCommande) | null | BC généré |
| date_conversion_bc | DateTimeField | null | Date conversion en BC |
| notes_internes | TextField | null | Notes internes |
| created_at | DateTimeField | auto_now_add | Date de création |
| updated_at | DateTimeField | auto_now | Date de modification |

### 4.3 Choices

\`\`\`python
PRIORITE_CHOICES = [
    ('NORMALE', 'Normale'),
    ('URGENTE', 'Urgente'),
    ('TRES_URGENTE', 'Très urgente'),
]

STATUT_CHOICES = [
    ('BROUILLON', 'Brouillon'),
    ('SOUMISE', 'Soumise'),
    ('EN_VALIDATION_N1', 'En validation N1'),
    ('VALIDEE_N1', 'Validée N1'),
    ('EN_VALIDATION_N2', 'En validation N2'),
    ('VALIDEE_N2', 'Validée N2 / Approuvée'),
    ('REFUSEE', 'Refusée'),
    ('ANNULEE', 'Annulée'),
    ('EN_TRAITEMENT', 'En traitement acheteur'),
    ('CONVERTIE_BC', 'Convertie en bon de commande'),
    ('CLOTUREE', 'Clôturée'),
]
\`\`\`

### 4.4 Méthodes

- \`__str__()\`: Retourne le numéro
- \`save()\`: Génère le numéro automatiquement
- \`soumettre()\`: Soumet la demande pour validation
- \`valider_n1(validateur, commentaire)\`: Validation N1
- \`valider_n2(validateur, commentaire)\`: Validation N2
- \`refuser(validateur, motif)\`: Refuse la demande
- \`annuler(motif)\`: Annule la demande
- \`assigner_acheteur(acheteur)\`: Assigne un acheteur
- \`convertir_en_bc()\`: Crée un bon de commande
- \`calculer_montants()\`: Recalcule les montants totaux
- \`verifier_budget_disponible()\`: Vérifie la disponibilité budgétaire
- \`get_workflow_state()\`: État actuel du workflow
- \`peut_etre_modifiee_par(user)\`: Vérifie les droits de modification
- \`get_prochaine_action()\`: Prochaine action possible

---

## 5. Ligne de demande (GACLigneDemandeAchat)

### 5.1 Description
Ligne de détail d'une demande d'achat.

### 5.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| demande_achat | ForeignKey(GACDemandeAchat) | CASCADE | Demande parente |
| numero_ligne | IntegerField | default=1 | Numéro de ligne |
| article | ForeignKey(GACArticle) | null | Article du catalogue |
| designation | CharField(200) | required | Désignation (libre si hors catalogue) |
| description | TextField | null | Description détaillée |
| quantite | DecimalField(10,2) | required | Quantité |
| unite | CharField(20) | required | Unité |
| prix_unitaire_estime_ht | DecimalField(10,2) | default=0 | Prix unitaire HT estimé |
| taux_tva | DecimalField(5,2) | default=20.00 | Taux de TVA |
| montant_ht | DecimalField(12,2) | default=0 | Montant ligne HT |
| montant_tva | DecimalField(12,2) | default=0 | Montant TVA |
| montant_ttc | DecimalField(12,2) | default=0 | Montant ligne TTC |
| fournisseur_suggere | ForeignKey(GACFournisseur) | null | Fournisseur suggéré |
| reference_fournisseur | CharField(100) | null | Référence chez fournisseur |
| lien_devis | URLField | null | Lien vers devis |
| commentaire | TextField | null | Commentaire |
| created_at | DateTimeField | auto_now_add | Date de création |

### 5.3 Méthodes

- \`save()\`: Calcule automatiquement les montants
- \`calculer_montants()\`: Recalcule HT, TVA, TTC
- \`__str__()\`: Retourne désignation + quantité


---

## 6. Bon de commande (GACBonCommande)

### 6.1 Description
Bon de commande émis auprès d'un fournisseur.

### 6.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| numero | CharField(20) | unique | Numéro BC (ex: BC2026-0001) |
| date_emission | DateField | auto_now_add | Date d'émission |
| demandes_origine | ManyToMany(GACDemandeAchat) | | Demandes d'achat sources |
| fournisseur | ForeignKey(GACFournisseur) | required | Fournisseur |
| acheteur | ForeignKey(ZY00) | required | Acheteur qui émet le BC |
| statut | CharField(20) | choices | Statut du BC |
| date_envoi_fournisseur | DateTimeField | null | Date d'envoi au fournisseur |
| date_reponse_fournisseur | DateTimeField | null | Date réponse fournisseur |
| numero_commande_fournisseur | CharField(50) | null | N° de confirmation fournisseur |
| date_livraison_prevue | DateField | null | Date de livraison prévue |
| date_livraison_reelle | DateField | null | Date de livraison réelle |
| adresse_livraison | TextField | required | Adresse de livraison |
| contact_livraison_nom | CharField(100) | null | Contact réception |
| contact_livraison_tel | CharField(20) | null | Téléphone contact |
| contact_livraison_email | EmailField | null | Email contact |
| conditions_paiement | TextField | null | Conditions de paiement |
| delai_paiement_jours | IntegerField | default=30 | Délai de paiement |
| mode_reglement | CharField(20) | choices | Mode de règlement |
| montant_ht | DecimalField(12,2) | default=0 | Montant total HT |
| montant_tva | DecimalField(12,2) | default=0 | Montant TVA |
| montant_ttc | DecimalField(12,2) | default=0 | Montant total TTC |
| devise | CharField(3) | default='EUR' | Devise |
| taux_change | DecimalField(10,4) | default=1.0000 | Taux de change si devise étrangère |
| frais_port | DecimalField(10,2) | default=0 | Frais de port |
| remise_globale_pourcent | DecimalField(5,2) | default=0 | Remise en % |
| remise_globale_montant | DecimalField(10,2) | default=0 | Remise en montant |
| notes_internes | TextField | null | Notes internes |
| conditions_generales | TextField | null | Conditions générales |
| fichier_pdf | FileField | null | BC généré en PDF |
| fichier_signe | FileField | null | BC signé par fournisseur |
| budget_impute | ForeignKey(GACBudget) | null | Budget imputé |
| created_at | DateTimeField | auto_now_add | Date de création |
| updated_at | DateTimeField | auto_now | Date de modification |
| created_by | ForeignKey(ZY00) | null | Créé par |

### 6.3 Choices

\`\`\`python
STATUT_CHOICES = [
    ('BROUILLON', 'Brouillon'),
    ('EMIS', 'Émis'),
    ('ENVOYE', 'Envoyé au fournisseur'),
    ('CONFIRME', 'Confirmé par fournisseur'),
    ('EN_COURS', 'En cours de livraison'),
    ('PARTIELLEMENT_RECU', 'Partiellement reçu'),
    ('RECU', 'Complètement reçu'),
    ('ANNULE', 'Annulé'),
    ('LITIGE', 'En litige'),
]
\`\`\`

### 6.4 Méthodes

- \`save()\`: Génère le numéro automatiquement
- \`generer_numero()\`: Génère BC2026-XXXX
- \`calculer_montants()\`: Recalcule HT, TVA, TTC
- \`envoyer_fournisseur()\`: Marque comme envoyé
- \`confirmer_reception_fournisseur(numero)\`: Enregistre confirmation
- \`annuler(motif)\`: Annule le BC
- \`generer_pdf()\`: Génère le PDF du BC
- \`get_pourcentage_reception()\`: % de réception
- \`est_completement_recu()\`: True si tout reçu

---

## 7. Ligne de bon de commande (GACLigneBonCommande)

### 7.1 Description
Ligne de détail d'un bon de commande.

### 7.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| bon_commande | ForeignKey(GACBonCommande) | CASCADE | BC parent |
| numero_ligne | IntegerField | default=1 | N° de ligne |
| ligne_demande_origine | ForeignKey(GACLigneDemandeAchat) | null | Ligne DA source |
| article | ForeignKey(GACArticle) | null | Article du catalogue |
| designation | CharField(200) | required | Désignation |
| reference_fournisseur | CharField(100) | null | Référence fournisseur |
| quantite_commandee | DecimalField(10,2) | required | Quantité commandée |
| quantite_recue | DecimalField(10,2) | default=0 | Quantité reçue |
| unite | CharField(20) | required | Unité |
| prix_unitaire_ht | DecimalField(10,2) | required | Prix unitaire HT |
| taux_tva | DecimalField(5,2) | default=20.00 | Taux TVA |
| remise_pourcent | DecimalField(5,2) | default=0 | Remise ligne en % |
| prix_unitaire_net_ht | DecimalField(10,2) | default=0 | Prix après remise |
| montant_ligne_ht | DecimalField(12,2) | default=0 | Montant ligne HT |
| montant_tva | DecimalField(12,2) | default=0 | Montant TVA |
| montant_ttc | DecimalField(12,2) | default=0 | Montant TTC |
| commentaire | TextField | null | Commentaire |
| created_at | DateTimeField | auto_now_add | Date de création |

### 7.3 Méthodes

- \`save()\`: Calcule les montants
- \`calculer_montants()\`: Recalcule prix net, HT, TVA, TTC
- \`est_completement_recu()\`: True si quantité reçue = commandée
- \`quantite_restante()\`: Quantité restant à recevoir

---

## 8. Réception (GACReception)

### 8.1 Description
Enregistrement d'une réception de marchandises.

### 8.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| numero | CharField(20) | unique | N° réception (REC2026-0001) |
| bon_commande | ForeignKey(GACBonCommande) | required | BC concerné |
| date_reception | DateField | required | Date de réception |
| heure_reception | TimeField | null | Heure de réception |
| receptionnaire | ForeignKey(ZY00) | required | Personne qui réceptionne |
| statut | CharField(20) | choices | Statut réception |
| bon_livraison_fournisseur | CharField(100) | null | N° BL fournisseur |
| transporteur | CharField(100) | null | Nom transporteur |
| numero_colis | IntegerField | null | Nombre de colis |
| poids_total | DecimalField(10,2) | null | Poids total (kg) |
| conforme | BooleanField | default=True | Livraison conforme ? |
| reserves | TextField | null | Réserves éventuelles |
| commentaire | TextField | null | Commentaire général |
| photos | JSONField | default=list | Liste URLs photos |
| signature_receptionnaire | ImageField | null | Signature |
| created_at | DateTimeField | auto_now_add | Date de création |
| updated_at | DateTimeField | auto_now | Date de modification |

### 8.3 Choices

\`\`\`python
STATUT_CHOICES = [
    ('PARTIELLE', 'Réception partielle'),
    ('COMPLETE', 'Réception complète'),
    ('AVEC_RESERVES', 'Avec réserves'),
    ('REFUSEE', 'Refusée'),
]
\`\`\`

### 8.4 Méthodes

- \`save()\`: Génère le numéro
- \`valider()\`: Valide la réception
- \`generer_bon_reception()\`: Génère PDF bon de réception
- \`notifier_demandeur()\`: Notifie le demandeur initial

---

## 9. Ligne de réception (GACLigneReception)

### 9.1 Description
Détail des quantités reçues par ligne de BC.

### 9.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| reception | ForeignKey(GACReception) | CASCADE | Réception parente |
| ligne_bon_commande | ForeignKey(GACLigneBonCommande) | required | Ligne BC |
| quantite_attendue | DecimalField(10,2) | default=0 | Quantité attendue |
| quantite_recue | DecimalField(10,2) | required | Quantité réellement reçue |
| quantite_acceptee | DecimalField(10,2) | default=0 | Quantité acceptée |
| quantite_refusee | DecimalField(10,2) | default=0 | Quantité refusée |
| motif_refus | TextField | null | Motif si refus partiel/total |
| conforme | BooleanField | default=True | Article conforme ? |
| commentaire | TextField | null | Commentaire |
| emplacement_stockage | CharField(100) | null | Emplacement si stocké |
| numero_serie | CharField(100) | null | N° série si applicable |
| created_at | DateTimeField | auto_now_add | Date de création |

### 9.3 Méthodes

- \`save()\`: Met à jour la ligne BC (quantité reçue)
- \`valider()\`: Valide les quantités
- \`affecter_stock()\`: Affecte au stock si géré

---

## 10. Budget (GACBudget)

### 10.1 Description
Enveloppe budgétaire par département/catégorie/année.

### 10.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| code | CharField(20) | unique | Code budget |
| libelle | CharField(200) | required | Libellé |
| annee | IntegerField | required | Année budgétaire |
| departement | ForeignKey(ZYDE) | null | Département |
| service | CharField(100) | null | Service |
| categorie | ForeignKey(GACCategorie) | null | Catégorie produits |
| montant_initial | DecimalField(12,2) | required | Budget initial |
| montant_ajustements | DecimalField(12,2) | default=0 | Ajustements (+/-) |
| montant_disponible | DecimalField(12,2) | default=0 | Budget disponible (calculé) |
| montant_engage | DecimalField(12,2) | default=0 | Montant engagé (DAs approuvées) |
| montant_commande | DecimalField(12,2) | default=0 | Montant commandé (BCs émis) |
| montant_consomme | DecimalField(12,2) | default=0 | Montant consommé (réceptions) |
| seuil_alerte_pourcent | IntegerField | default=80 | Seuil d'alerte en % |
| gestionnaire | ForeignKey(ZY00) | required | Gestionnaire budget |
| gestionnaires_delegues | ManyToMany(ZY00) | | Gestionnaires délégués |
| statut | CharField(20) | choices | Statut |
| notes | TextField | null | Notes |
| created_at | DateTimeField | auto_now_add | Date de création |
| updated_at | DateTimeField | auto_now | Date de modification |

### 10.3 Choices

\`\`\`python
STATUT_CHOICES = [
    ('ACTIF', 'Actif'),
    ('CLOTURE', 'Clôturé'),
    ('SUSPENDU', 'Suspendu'),
]
\`\`\`

### 10.4 Méthodes

- \`calculer_disponible()\`: Budget disponible
- \`calculer_taux_consommation()\`: % consommé
- \`verifier_disponibilite(montant)\`: True si budget suffisant
- \`engager(montant)\`: Engage un montant (DA approuvée)
- \`commander(montant)\`: Passe en commandé (BC émis)
- \`consommer(montant)\`: Consomme (réception)
- \`desengager(montant)\`: Désengage (DA annulée)
- \`ajuster(montant, motif)\`: Ajuste le budget
- \`est_alerte_atteinte()\`: True si seuil atteint

---

## 11. Pièce jointe (GACPieceJointe)

### 11.1 Description
Fichiers attachés aux demandes, BCs, réceptions.

### 11.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| uuid | UUIDField | unique | Identifiant universel |
| content_type | ForeignKey(ContentType) | required | Type d'objet lié |
| object_id | PositiveIntegerField | required | ID objet lié |
| content_object | GenericForeignKey | | Objet lié (DA, BC, Réception) |
| type_document | CharField(50) | choices | Type de document |
| fichier | FileField | required | Fichier |
| nom_fichier | CharField(200) | | Nom original |
| taille | IntegerField | | Taille en octets |
| description | CharField(200) | null | Description |
| uploaded_by | ForeignKey(ZY00) | required | Uploadé par |
| uploaded_at | DateTimeField | auto_now_add | Date upload |

### 11.3 Choices

\`\`\`python
TYPE_DOCUMENT_CHOICES = [
    ('DEVIS', 'Devis'),
    ('FACTURE', 'Facture'),
    ('BON_LIVRAISON', 'Bon de livraison'),
    ('SPECIFICATIONS', 'Spécifications techniques'),
    ('PHOTO', 'Photo'),
    ('CONTRAT', 'Contrat'),
    ('AUTRE', 'Autre'),
]
\`\`\`

---

## 12. Historique (GACHistorique)

### 12.1 Description
Traçabilité des modifications importantes.

### 12.2 Champs

| Champ | Type | Propriétés | Description |
|-------|------|------------|-------------|
| id | BigAutoField | PK, auto | ID technique |
| content_type | ForeignKey(ContentType) | required | Type d'objet |
| object_id | PositiveIntegerField | required | ID objet |
| content_object | GenericForeignKey | | Objet lié |
| action | CharField(50) | choices | Type d'action |
| champ_modifie | CharField(100) | null | Champ modifié |
| ancienne_valeur | TextField | null | Ancienne valeur |
| nouvelle_valeur | TextField | null | Nouvelle valeur |
| utilisateur | ForeignKey(ZY00) | required | Utilisateur |
| date_action | DateTimeField | auto_now_add | Date/heure |
| commentaire | TextField | null | Commentaire |
| ip_address | GenericIPAddressField | null | Adresse IP |

### 12.3 Choices

\`\`\`python
ACTION_CHOICES = [
    ('CREATION', 'Création'),
    ('MODIFICATION', 'Modification'),
    ('VALIDATION', 'Validation'),
    ('REFUS', 'Refus'),
    ('ANNULATION', 'Annulation'),
    ('ENVOI', 'Envoi'),
    ('RECEPTION', 'Réception'),
]
\`\`\`

---

## Résumé des relations

\`\`\`
GACDemandeAchat (1) ----< (N) GACLigneDemandeAchat
GACDemandeAchat (N) ----< (N) GACBonCommande (ManyToMany)
GACBonCommande (1) ----< (N) GACLigneBonCommande
GACBonCommande (1) ----< (N) GACReception
GACReception (1) ----< (N) GACLigneReception
GACLigneBonCommande (1) ----< (N) GACLigneReception

GACFournisseur (1) ----< (N) GACArticle
GACFournisseur (1) ----< (N) GACBonCommande
GACCategorie (1) ----< (N) GACArticle
GACCategorie (self-FK) - Hiérarchie

GACBudget (1) ----< (N) GACDemandeAchat
GACBudget (1) ----< (N) GACBonCommande

ZY00 (Employé) ----< (N) GACDemandeAchat (demandeur)
ZY00 (Employé) ----< (N) GACDemandeAchat (validateurs)
ZY00 (Employé) ----< (N) GACBonCommande (acheteur)
ZY00 (Employé) ----< (N) GACReception (receptionnaire)
ZY00 (Employé) ----< (N) GACBudget (gestionnaire)
\`\`\`


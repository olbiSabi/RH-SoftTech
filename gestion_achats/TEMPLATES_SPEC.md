# Spécifications des Templates - Module GAC

**Version**: 1.0
**Date**: 01/02/2026
**Projet**: HR_ONIAN
**Module**: Gestion des Achats & Commandes

---

## Vue d'ensemble

Ce document spécifie la structure et le contenu de tous les templates HTML du module GAC, ainsi que les composants réutilisables et les directives UX/UI.

### Emplacements des fichiers

**IMPORTANT** : Les fichiers doivent être créés dans les emplacements suivants :

- **Templates** : `HR_ONIAN/templates/gestion_achats/` (et non dans `gestion_achats/templates/`)
- **Fichiers statiques** : `HR_ONIAN/static/gestion_achats/` (et non dans `gestion_achats/static/`)

Cette structure suit l'architecture Django du projet où tous les templates et fichiers statiques sont centralisés au niveau du projet.

---

## 1. Structure des templates

### 1.1 Arborescence

**Chemin complet** : `HR_ONIAN/templates/gestion_achats/`

```
templates/gestion_achats/
├── dashboard/
│   └── dashboard.html               # Tableau de bord principal
│
├── demande/
│   ├── demande_list.html            # Liste des demandes
│   ├── demande_detail.html          # Détail d'une demande
│   ├── demande_form.html            # Formulaire de création/modification
│   ├── mes_demandes.html            # Mes demandes
│   ├── a_valider.html               # Demandes à valider
│   ├── valider_n1.html              # Formulaire validation N1
│   ├── valider_n2.html              # Formulaire validation N2
│   ├── refuser.html                 # Formulaire de refus
│   └── convertir_bc.html            # Formulaire conversion BC
│
├── bon_commande/
│   ├── bon_commande_list.html       # Liste des BCs
│   ├── bon_commande_detail.html     # Détail d'un BC
│   ├── bon_commande_form.html       # Formulaire de création/modification
│   ├── envoyer.html                 # Formulaire d'envoi
│   └── confirmer.html               # Formulaire de confirmation
│
├── fournisseur/
│   ├── fournisseur_list.html        # Liste des fournisseurs
│   ├── fournisseur_detail.html      # Détail d'un fournisseur
│   ├── fournisseur_form.html        # Formulaire de création/modification
│   └── evaluer.html                 # Formulaire d'évaluation
│
├── reception/
│   ├── reception_list.html          # Liste des réceptions
│   ├── reception_detail.html        # Détail d'une réception
│   └── reception_form.html          # Formulaire de réception
│
├── catalogue/
│   ├── article_list.html            # Liste des articles
│   ├── article_detail.html          # Détail d'un article
│   ├── article_form.html            # Formulaire article
│   ├── categorie_list.html          # Liste des catégories
│   └── categorie_form.html          # Formulaire catégorie
│
├── budget/
│   ├── budget_list.html             # Liste des budgets
│   ├── budget_detail.html           # Détail d'un budget
│   ├── budget_form.html             # Formulaire budget
│   └── budget_historique.html       # Historique des mouvements
│
├── pdf/
│   └── bon_commande.html            # Template PDF pour BC
│
└── includes/
    ├── breadcrumb.html              # Fil d'Ariane
    ├── statut_badge.html            # Badge de statut
    ├── action_buttons.html          # Boutons d'action
    ├── historique.html              # Historique
    ├── pagination.html              # Pagination
    ├── messages.html                # Messages flash
    ├── filters.html                 # Filtres de recherche
    └── stats_card.html              # Carte de statistique
```

---

## 2. Dashboard

### 2.1 dashboard.html

**Fichier** : `templates/gestion_achats/dashboard/dashboard.html`

**Description** : Tableau de bord principal du module GAC

**Contenu** :
```django
{% extends 'base/baseSansMatricule.html' %}
{% load static %}

{% block extrastylet %}
<link rel="stylesheet" href="{% static 'gestion_achats/css/gac_styles.css' %}">
{% endblock %}

{% block pageContent %}
<div class="dashboard-container">
    <h2 class="page-title">
        <i class="fas fa-chart-line"></i> Tableau de bord - Gestion des Achats
    </h2>

    <!-- Statistiques principales -->
    <div class="row mb-4">
        <!-- Demandes d'achat -->
        <div class="col-md-3">
            {% include 'gestion_achats/includes/stats_card.html' with icon='file-alt' title='Demandes d\'achat' value=stats_demandes.total color='primary' %}
        </div>

        <!-- Demandes en attente -->
        <div class="col-md-3">
            {% include 'gestion_achats/includes/stats_card.html' with icon='clock' title='En attente de validation' value=stats_demandes.en_attente color='warning' %}
        </div>

        <!-- Bons de commande -->
        <div class="col-md-3">
            {% include 'gestion_achats/includes/stats_card.html' with icon='shopping-bag' title='Bons de commande' value=stats_bons_commande.total color='success' %}
        </div>

        <!-- Budget disponible -->
        <div class="col-md-3">
            {% include 'gestion_achats/includes/stats_card.html' with icon='euro-sign' title='Budget disponible' value=stats_budgets.total_disponible|floatformat:2 suffix='€' color='info' %}
        </div>
    </div>

    <!-- Graphiques -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-pie"></i> Demandes par statut</h5>
                </div>
                <div class="card-body">
                    <canvas id="chartDemandesStatut"></canvas>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-bar"></i> Consommation budgétaire</h5>
                </div>
                <div class="card-body">
                    <canvas id="chartBudget"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Demandes à valider -->
    {% if demandes_a_valider %}
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header bg-warning text-white">
                    <h5><i class="fas fa-exclamation-circle"></i> Demandes en attente de votre validation</h5>
                </div>
                <div class="card-body">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Numéro</th>
                                <th>Demandeur</th>
                                <th>Objet</th>
                                <th>Montant TTC</th>
                                <th>Date</th>
                                <th>Statut</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for demande in demandes_a_valider %}
                            <tr>
                                <td><a href="{% url 'gestion_achats:demande_detail' demande.pk %}">{{ demande.numero }}</a></td>
                                <td>{{ demande.demandeur.get_full_name }}</td>
                                <td>{{ demande.objet|truncatewords:10 }}</td>
                                <td>{{ demande.montant_total_ttc|floatformat:2 }} €</td>
                                <td>{{ demande.date_soumission|date:'d/m/Y' }}</td>
                                <td>{% include 'gestion_achats/includes/statut_badge.html' with statut=demande.statut %}</td>
                                <td>
                                    <a href="{% url 'gestion_achats:demande_detail' demande.pk %}" class="btn btn-sm btn-primary">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Alertes budgétaires -->
    {% if alertes_budgetaires %}
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <h5><i class="fas fa-exclamation-triangle"></i> Alertes budgétaires</h5>
                </div>
                <div class="card-body">
                    <ul class="list-group">
                        {% for budget in alertes_budgetaires %}
                        <li class="list-group-item list-group-item-danger">
                            <strong>{{ budget.code }}</strong> - {{ budget.libelle }} :
                            Consommation à {{ budget.taux_consommation|floatformat:1 }}%
                            ({{ budget.montant_disponible|floatformat:2 }} € disponible)
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block extrascript %}
<script src="{% static 'gestion_achats/js/gac_common.js' %}"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="{% static 'gestion_achats/js/dashboard_charts.js' %}"></script>
{% endblock %}
```

---

## 3. Templates des Demandes

### 3.1 demande_list.html

**Fichier** : `templates/gestion_achats/demande/demande_list.html`

**Structure** :
```django
{% extends 'base/baseSansMatricule.html' %}
{% load static %}

{% block extrastylet %}
<link rel="stylesheet" href="{% static 'gestion_achats/css/gac_styles.css' %}">
{% endblock %}

{% block pageContent %}
<div class="demande-list-container">
    <!-- En-tête avec bouton de création -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2><i class="fas fa-file-alt"></i> Demandes d'achat</h2>
        <a href="{% url 'gestion_achats:demande_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Nouvelle demande
        </a>
    </div>

    <!-- Filtres -->
    {% include 'gestion_achats/includes/filters.html' %}

    <!-- Statistiques résumées -->
    <div class="row mb-3">
        <div class="col-md-12">
            <div class="alert alert-info">
                <strong>{{ stats.total }}</strong> demande(s) trouvée(s) -
                Montant total : <strong>{{ stats.montant_total|floatformat:2 }} €</strong>
            </div>
        </div>
    </div>

    <!-- Table des demandes -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover" id="demandesTable">
                <thead>
                    <tr>
                        <th>Numéro</th>
                        <th>Date</th>
                        <th>Demandeur</th>
                        <th>Objet</th>
                        <th>Montant TTC</th>
                        <th>Statut</th>
                        <th>Priorité</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for demande in demandes %}
                    <tr>
                        <td>
                            <a href="{% url 'gestion_achats:demande_detail' demande.pk %}">
                                <strong>{{ demande.numero }}</strong>
                            </a>
                        </td>
                        <td>{{ demande.date_creation|date:'d/m/Y' }}</td>
                        <td>{{ demande.demandeur.get_full_name }}</td>
                        <td>{{ demande.objet|truncatewords:15 }}</td>
                        <td>{{ demande.montant_total_ttc|floatformat:2 }} €</td>
                        <td>{% include 'gestion_achats/includes/statut_badge.html' with statut=demande.statut %}</td>
                        <td>
                            {% if demande.priorite == 'URGENTE' %}
                                <span class="badge bg-danger">Urgente</span>
                            {% elif demande.priorite == 'HAUTE' %}
                                <span class="badge bg-warning">Haute</span>
                            {% elif demande.priorite == 'NORMALE' %}
                                <span class="badge bg-info">Normale</span>
                            {% else %}
                                <span class="badge bg-secondary">Basse</span>
                            {% endif %}
                        </td>
                        <td>
                            <a href="{% url 'gestion_achats:demande_detail' demande.pk %}"
                               class="btn btn-sm btn-primary"
                               title="Voir le détail">
                                <i class="fas fa-eye"></i>
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="8" class="text-center">
                            <em>Aucune demande trouvée</em>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            <!-- Pagination -->
            {% include 'gestion_achats/includes/pagination.html' %}
        </div>
    </div>
</div>
{% endblock %}

{% block extrascript %}
<script src="{% static 'gestion_achats/js/gac_common.js' %}"></script>
<script src="{% static 'gestion_achats/js/demande_list.js' %}"></script>
{% endblock %}
```

---

### 3.2 demande_detail.html

**Fichier** : `templates/gestion_achats/demande/demande_detail.html`

**Structure** :
```django
{% extends 'base/baseSansMatricule.html' %}
{% load static %}
{% load gac_permissions %}

{% block extrastylet %}
<link rel="stylesheet" href="{% static 'gestion_achats/css/gac_styles.css' %}">
{% endblock %}

{% block pageContent %}
<div class="demande-detail-container">
    <!-- En-tête -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>
            <i class="fas fa-file-alt"></i> Demande {{ demande.numero }}
            {% include 'gestion_achats/includes/statut_badge.html' with statut=demande.statut %}
        </h2>

        <!-- Boutons d'action -->
        {% include 'gestion_achats/includes/action_buttons.html' with objet=demande type='demande' %}
    </div>

    <!-- Informations générales -->
    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-info-circle"></i> Informations générales</h5>
                </div>
                <div class="card-body">
                    <dl class="row">
                        <dt class="col-sm-4">Numéro :</dt>
                        <dd class="col-sm-8">{{ demande.numero }}</dd>

                        <dt class="col-sm-4">Date de création :</dt>
                        <dd class="col-sm-8">{{ demande.date_creation|date:'d/m/Y à H:i' }}</dd>

                        <dt class="col-sm-4">Demandeur :</dt>
                        <dd class="col-sm-8">{{ demande.demandeur.get_full_name }}</dd>

                        <dt class="col-sm-4">Département :</dt>
                        <dd class="col-sm-8">{{ demande.departement|default:'-' }}</dd>

                        <dt class="col-sm-4">Projet lié :</dt>
                        <dd class="col-sm-8">
                            {% if demande.projet %}
                                <a href="{% url 'project_management:projet_detail' demande.projet.pk %}">
                                    {{ demande.projet.nom }}
                                </a>
                            {% else %}
                                -
                            {% endif %}
                        </dd>

                        <dt class="col-sm-4">Budget :</dt>
                        <dd class="col-sm-8">
                            {% if demande.budget %}
                                <a href="{% url 'gestion_achats:budget_detail' demande.budget.pk %}">
                                    {{ demande.budget.code }} - {{ demande.budget.libelle }}
                                </a>
                            {% else %}
                                -
                            {% endif %}
                        </dd>

                        <dt class="col-sm-4">Priorité :</dt>
                        <dd class="col-sm-8">
                            {% if demande.priorite == 'URGENTE' %}
                                <span class="badge bg-danger">Urgente</span>
                            {% elif demande.priorite == 'HAUTE' %}
                                <span class="badge bg-warning">Haute</span>
                            {% elif demande.priorite == 'NORMALE' %}
                                <span class="badge bg-info">Normale</span>
                            {% else %}
                                <span class="badge bg-secondary">Basse</span>
                            {% endif %}
                        </dd>

                        <dt class="col-sm-4">Objet :</dt>
                        <dd class="col-sm-8">{{ demande.objet }}</dd>

                        <dt class="col-sm-4">Justification :</dt>
                        <dd class="col-sm-8">{{ demande.justification|linebreaks }}</dd>
                    </dl>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-euro-sign"></i> Montants</h5>
                </div>
                <div class="card-body">
                    <dl class="row">
                        <dt class="col-sm-6">Montant HT :</dt>
                        <dd class="col-sm-6 text-end">{{ demande.montant_total_ht|floatformat:2 }} €</dd>

                        <dt class="col-sm-6">TVA :</dt>
                        <dd class="col-sm-6 text-end">{{ demande.montant_total_tva|floatformat:2 }} €</dd>

                        <dt class="col-sm-6"><strong>Total TTC :</strong></dt>
                        <dd class="col-sm-6 text-end">
                            <strong class="text-primary fs-4">{{ demande.montant_total_ttc|floatformat:2 }} €</strong>
                        </dd>
                    </dl>
                </div>
            </div>

            <!-- Validations -->
            <div class="card mt-3">
                <div class="card-header">
                    <h5><i class="fas fa-check-circle"></i> Validations</h5>
                </div>
                <div class="card-body">
                    <!-- Validation N1 -->
                    <div class="mb-3">
                        <h6>Validation N1 (Manager)</h6>
                        {% if demande.validateur_n1 %}
                            <p class="mb-1"><strong>{{ demande.validateur_n1.get_full_name }}</strong></p>
                            {% if demande.date_validation_n1 %}
                                <p class="mb-0 text-success">
                                    <i class="fas fa-check"></i> Validée le {{ demande.date_validation_n1|date:'d/m/Y' }}
                                </p>
                                {% if demande.commentaire_validation_n1 %}
                                    <p class="small text-muted mt-1">{{ demande.commentaire_validation_n1 }}</p>
                                {% endif %}
                            {% else %}
                                <p class="mb-0 text-warning">
                                    <i class="fas fa-clock"></i> En attente
                                </p>
                            {% endif %}
                        {% else %}
                            <p class="text-muted">Non défini</p>
                        {% endif %}
                    </div>

                    <!-- Validation N2 -->
                    <div>
                        <h6>Validation N2 (Direction)</h6>
                        {% if demande.validateur_n2 %}
                            <p class="mb-1"><strong>{{ demande.validateur_n2.get_full_name }}</strong></p>
                            {% if demande.date_validation_n2 %}
                                <p class="mb-0 text-success">
                                    <i class="fas fa-check"></i> Validée le {{ demande.date_validation_n2|date:'d/m/Y' }}
                                </p>
                                {% if demande.commentaire_validation_n2 %}
                                    <p class="small text-muted mt-1">{{ demande.commentaire_validation_n2 }}</p>
                                {% endif %}
                            {% else %}
                                <p class="mb-0 text-warning">
                                    <i class="fas fa-clock"></i> En attente
                                </p>
                            {% endif %}
                        {% else %}
                            <p class="text-muted">Non défini</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Lignes de la demande -->
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5><i class="fas fa-list"></i> Lignes de la demande</h5>
                    {% if peut_modifier %}
                        <button type="button" class="btn btn-sm btn-success" data-bs-toggle="modal" data-bs-target="#ajouterLigneModal">
                            <i class="fas fa-plus"></i> Ajouter une ligne
                        </button>
                    {% endif %}
                </div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Article</th>
                                <th>Référence</th>
                                <th>Quantité</th>
                                <th>Prix unitaire</th>
                                <th>Montant HT</th>
                                {% if peut_modifier %}
                                <th>Actions</th>
                                {% endif %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for ligne in demande.lignes.all %}
                            <tr>
                                <td>{{ ligne.article.designation }}</td>
                                <td>{{ ligne.article.reference }}</td>
                                <td>{{ ligne.quantite }} {{ ligne.article.unite }}</td>
                                <td>{{ ligne.prix_unitaire|floatformat:2 }} €</td>
                                <td>{{ ligne.montant|floatformat:2 }} €</td>
                                {% if peut_modifier %}
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="supprimerLigne('{{ ligne.pk }}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                                {% endif %}
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="{% if peut_modifier %}6{% else %}5{% endif %}" class="text-center">
                                    <em>Aucune ligne ajoutée</em>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Bon de commande associé -->
    {% if demande.bon_commande %}
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h5><i class="fas fa-shopping-bag"></i> Bon de commande associé</h5>
                </div>
                <div class="card-body">
                    <p>
                        Cette demande a été convertie en bon de commande :
                        <a href="{% url 'gestion_achats:bon_commande_detail' demande.bon_commande.pk %}"
                           class="btn btn-success btn-sm">
                            <i class="fas fa-eye"></i> Voir le BC {{ demande.bon_commande.numero }}
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Historique -->
    <div class="row">
        <div class="col-md-12">
            {% include 'gestion_achats/includes/historique.html' with objet=demande %}
        </div>
    </div>
</div>

<!-- Modal pour ajouter une ligne -->
{% if peut_modifier %}
<div class="modal fade" id="ajouterLigneModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Ajouter une ligne</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="ajouterLigneForm" method="post" action="{% url 'gestion_achats:demande_ajouter_ligne' demande.pk %}">
                {% csrf_token %}
                <div class="modal-body">
                    <!-- Formulaire d'ajout de ligne -->
                    <div class="mb-3">
                        <label for="id_article" class="form-label">Article</label>
                        <select name="article" id="id_article" class="form-select select2" required>
                            <option value="">-- Sélectionner un article --</option>
                        </select>
                    </div>

                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="id_quantite" class="form-label">Quantité</label>
                                <input type="number" step="0.01" name="quantite" id="id_quantite" class="form-control" required>
                            </div>
                        </div>

                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="id_prix_unitaire" class="form-label">Prix unitaire</label>
                                <input type="number" step="0.01" name="prix_unitaire" id="id_prix_unitaire" class="form-control" required>
                            </div>
                        </div>

                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Montant</label>
                                <input type="text" id="montant_calcule" class="form-control" readonly>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="id_commentaire" class="form-label">Commentaire (optionnel)</label>
                        <textarea name="commentaire" id="id_commentaire" class="form-control" rows="2"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="submit" class="btn btn-primary">Ajouter</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}

{% block extrascript %}
<script src="{% static 'gestion_achats/js/gac_common.js' %}"></script>
<script src="{% static 'gestion_achats/js/demande_detail.js' %}"></script>
{% endblock %}
```

---

## 5. Composants réutilisables (includes)

### 5.1 statut_badge.html

**Fichier** : `templates/gestion_achats/includes/statut_badge.html`

```django
{% if statut == 'BROUILLON' %}
    <span class="badge bg-secondary">Brouillon</span>
{% elif statut == 'SOUMISE' %}
    <span class="badge bg-info">Soumise</span>
{% elif statut == 'VALIDEE_N1' %}
    <span class="badge bg-primary">Validée N1</span>
{% elif statut == 'VALIDEE_N2' %}
    <span class="badge bg-success">Validée N2</span>
{% elif statut == 'CONVERTIE_BC' %}
    <span class="badge bg-success">Convertie BC</span>
{% elif statut == 'REFUSEE' %}
    <span class="badge bg-danger">Refusée</span>
{% elif statut == 'ANNULEE' %}
    <span class="badge bg-dark">Annulée</span>
{% elif statut == 'EMIS' %}
    <span class="badge bg-warning">Émis</span>
{% elif statut == 'ENVOYE' %}
    <span class="badge bg-info">Envoyé</span>
{% elif statut == 'CONFIRME' %}
    <span class="badge bg-primary">Confirmé</span>
{% elif statut == 'RECU_PARTIEL' %}
    <span class="badge bg-warning">Reçu partiel</span>
{% elif statut == 'RECU_COMPLET' %}
    <span class="badge bg-success">Reçu complet</span>
{% elif statut == 'ANNULE' %}
    <span class="badge bg-danger">Annulé</span>
{% else %}
    <span class="badge bg-light text-dark">{{ statut }}</span>
{% endif %}
```

---

### 5.2 action_buttons.html

**Fichier** : `templates/gestion_achats/includes/action_buttons.html`

```django
{% load gac_permissions %}

<div class="btn-group" role="group">
    {% if type == 'demande' %}
        {% if peut_modifier %}
            <a href="{% url 'gestion_achats:demande_update' objet.pk %}" class="btn btn-sm btn-warning">
                <i class="fas fa-edit"></i> Modifier
            </a>
        {% endif %}

        {% if peut_soumettre %}
            <form method="post" action="{% url 'gestion_achats:demande_soumettre' objet.pk %}" style="display: inline;">
                {% csrf_token %}
                <button type="submit" class="btn btn-sm btn-primary" onclick="return confirm('Confirmer la soumission ?')">
                    <i class="fas fa-paper-plane"></i> Soumettre
                </button>
            </form>
        {% endif %}

        {% if peut_valider_n1 %}
            <a href="{% url 'gestion_achats:demande_valider_n1' objet.pk %}" class="btn btn-sm btn-success">
                <i class="fas fa-check"></i> Valider (N1)
            </a>
        {% endif %}

        {% if peut_valider_n2 %}
            <a href="{% url 'gestion_achats:demande_valider_n2' objet.pk %}" class="btn btn-sm btn-success">
                <i class="fas fa-check-double"></i> Valider (N2)
            </a>
        {% endif %}

        {% if peut_refuser %}
            <a href="{% url 'gestion_achats:demande_refuser' objet.pk %}" class="btn btn-sm btn-danger">
                <i class="fas fa-times"></i> Refuser
            </a>
        {% endif %}

        {% if peut_convertir_bc %}
            <a href="{% url 'gestion_achats:demande_convertir_bc' objet.pk %}" class="btn btn-sm btn-success">
                <i class="fas fa-exchange-alt"></i> Convertir en BC
            </a>
        {% endif %}
    {% endif %}
</div>
```

---

### 5.3 historique.html

**Fichier** : `templates/gestion_achats/includes/historique.html`

```django
<div class="card">
    <div class="card-header">
        <h5><i class="fas fa-history"></i> Historique</h5>
    </div>
    <div class="card-body">
        <div class="timeline">
            {% for entree in historique %}
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <p class="timeline-date">{{ entree.date_action|date:'d/m/Y à H:i' }}</p>
                    <p class="timeline-user">
                        {% if entree.utilisateur %}
                            <strong>{{ entree.utilisateur.get_full_name }}</strong>
                        {% else %}
                            <strong>Système</strong>
                        {% endif %}
                    </p>
                    <p class="timeline-action">
                        <span class="badge bg-info">{{ entree.get_action_display }}</span>
                    </p>
                    <p class="timeline-description">{{ entree.description }}</p>
                </div>
            </div>
            {% empty %}
            <p class="text-muted"><em>Aucun historique</em></p>
            {% endfor %}
        </div>
    </div>
</div>
```

---

### 5.4 stats_card.html

**Fichier** : `templates/gestion_achats/includes/stats_card.html`

```django
<div class="card stats-card border-{{ color }}">
    <div class="card-body">
        <div class="d-flex align-items-center">
            <div class="flex-shrink-0">
                <i class="fas fa-{{ icon }} fa-3x text-{{ color }}"></i>
            </div>
            <div class="flex-grow-1 ms-3">
                <p class="card-title text-muted mb-1">{{ title }}</p>
                <h3 class="mb-0">
                    {{ value }}{% if suffix %} {{ suffix }}{% endif %}
                </h3>
            </div>
        </div>
    </div>
</div>
```

---

## 6. Templates PDF

### 6.1 bon_commande.html (PDF)

**Fichier** : `templates/gestion_achats/pdf/bon_commande.html`

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Bon de commande {{ bc.numero }}</title>
    <style>
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        .header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .logo {
            float: left;
            width: 200px;
        }
        .entreprise-info {
            float: right;
            text-align: right;
        }
        .clear {
            clear: both;
        }
        .bc-numero {
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            margin: 20px 0;
        }
        .fournisseur-info {
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        .text-right {
            text-align: right;
        }
        .totaux {
            float: right;
            width: 300px;
        }
        .totaux table {
            margin-bottom: 0;
        }
        .footer {
            margin-top: 40px;
            font-size: 9pt;
            color: #666;
        }
    </style>
</head>
<body>
    <!-- En-tête -->
    <div class="header">
        <div class="logo">
            {% if entreprise.logo %}
                <img src="{{ entreprise.logo }}" alt="Logo" style="max-width: 200px;">
            {% endif %}
        </div>
        <div class="entreprise-info">
            <strong>{{ entreprise.nom }}</strong><br>
            {{ entreprise.adresse|linebreaks }}
            SIRET : {{ entreprise.siret }}
        </div>
        <div class="clear"></div>
    </div>

    <!-- Numéro BC -->
    <div class="bc-numero">
        BON DE COMMANDE N° {{ bc.numero }}
    </div>

    <!-- Informations fournisseur -->
    <div class="fournisseur-info">
        <strong>FOURNISSEUR :</strong><br>
        {{ bc.fournisseur.raison_sociale }}<br>
        {{ bc.fournisseur.adresse }}<br>
        {{ bc.fournisseur.code_postal }} {{ bc.fournisseur.ville }}<br>
        SIRET : {{ bc.fournisseur.siret }}<br>
        Téléphone : {{ bc.fournisseur.telephone }}<br>
        Email : {{ bc.fournisseur.email }}
    </div>

    <!-- Informations BC -->
    <table>
        <tr>
            <th>Date d'émission</th>
            <td>{{ bc.date_emission|date:'d/m/Y' }}</td>
            <th>Date de livraison souhaitée</th>
            <td>{{ bc.date_livraison_souhaitee|date:'d/m/Y'|default:'-' }}</td>
        </tr>
        <tr>
            <th>Acheteur</th>
            <td>{{ bc.acheteur.get_full_name }}</td>
            <th>Conditions de paiement</th>
            <td>{{ bc.conditions_paiement }}</td>
        </tr>
    </table>

    <!-- Lignes du BC -->
    <table>
        <thead>
            <tr>
                <th style="width: 40%;">Désignation</th>
                <th style="width: 15%;">Référence</th>
                <th style="width: 10%;">Quantité</th>
                <th style="width: 15%;">Prix unitaire</th>
                <th style="width: 20%;">Montant HT</th>
            </tr>
        </thead>
        <tbody>
            {% for ligne in bc.lignes.all %}
            <tr>
                <td>{{ ligne.article.designation }}</td>
                <td>{{ ligne.article.reference }}</td>
                <td class="text-right">{{ ligne.quantite_commandee }} {{ ligne.article.unite }}</td>
                <td class="text-right">{{ ligne.prix_unitaire|floatformat:2 }} €</td>
                <td class="text-right">{{ ligne.montant|floatformat:2 }} €</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- Totaux -->
    <div class="totaux">
        <table>
            <tr>
                <th>Total HT</th>
                <td class="text-right">{{ bc.montant_total_ht|floatformat:2 }} €</td>
            </tr>
            <tr>
                <th>TVA</th>
                <td class="text-right">{{ bc.montant_total_tva|floatformat:2 }} €</td>
            </tr>
            <tr>
                <th><strong>Total TTC</strong></th>
                <td class="text-right"><strong>{{ bc.montant_total_ttc|floatformat:2 }} €</strong></td>
            </tr>
        </table>
    </div>

    <div class="clear"></div>

    <!-- Conditions -->
    <div style="margin-top: 40px;">
        <p><strong>Conditions générales :</strong></p>
        <ul style="font-size: 9pt;">
            <li>Livraison franco de port</li>
            <li>Paiement selon les conditions convenues : {{ bc.conditions_paiement }}</li>
            <li>Toute livraison non conforme sera refusée</li>
        </ul>
    </div>

    <!-- Signature -->
    <div style="margin-top: 40px;">
        <p><strong>Signature de l'acheteur :</strong></p>
        <p>{{ bc.acheteur.get_full_name }}</p>
        <p>Date : {{ bc.date_emission|date:'d/m/Y' }}</p>
    </div>

    <!-- Footer -->
    <div class="footer">
        <p style="text-align: center;">
            Document généré automatiquement par HR_ONIAN - Module GAC<br>
            {{ entreprise.nom }} - {{ entreprise.siret }}
        </p>
    </div>
</body>
</html>
```

---

## 7. Styles CSS

### 7.1 gac_styles.css

**Fichier** : `HR_ONIAN/static/gestion_achats/css/gac_styles.css`

```css
/* === MODULE GAC - STYLES === */

/* Container principal */
.gac-container {
    padding: 20px;
}

/* Sidebar */
.gac-sidebar {
    position: sticky;
    top: 20px;
}

.gac-sidebar .nav-link {
    color: #333;
    padding: 10px 15px;
    border-radius: 5px;
    transition: all 0.3s;
}

.gac-sidebar .nav-link:hover {
    background-color: #f0f0f0;
    color: #0066cc;
}

.gac-sidebar .nav-link.active {
    background-color: #0066cc;
    color: white;
}

.gac-sidebar .nav-link i {
    margin-right: 8px;
}

/* Cartes de statistiques */
.stats-card {
    border-left-width: 4px;
    transition: transform 0.2s;
}

.stats-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stats-card h3 {
    color: #333;
    font-weight: bold;
}

/* Badges de statut */
.badge {
    padding: 5px 10px;
    font-size: 12px;
}

/* Timeline (historique) */
.timeline {
    position: relative;
    padding-left: 30px;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 10px;
    top: 0;
    bottom: 0;
    width: 2px;
    background-color: #ddd;
}

.timeline-item {
    position: relative;
    margin-bottom: 20px;
}

.timeline-marker {
    position: absolute;
    left: -24px;
    top: 5px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #0066cc;
    border: 3px solid #fff;
    box-shadow: 0 0 0 2px #0066cc;
}

.timeline-content {
    padding: 10px 15px;
    background-color: #f8f9fa;
    border-radius: 5px;
}

.timeline-date {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.timeline-user {
    margin-bottom: 5px;
}

.timeline-action {
    margin-bottom: 5px;
}

.timeline-description {
    margin-bottom: 0;
    color: #333;
}

/* Tables */
.table th {
    background-color: #f8f9fa;
    font-weight: 600;
}

.table tbody tr:hover {
    background-color: #f8f9fa;
}

/* Boutons d'action */
.btn-group .btn {
    margin-right: 5px;
}

/* Pagination */
.pagination {
    justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
    .gac-sidebar {
        position: static;
        margin-bottom: 20px;
    }

    .stats-card {
        margin-bottom: 15px;
    }
}
```

---

## 8. JavaScript

### 8.1 gac_common.js

**Fichier** : `HR_ONIAN/static/gestion_achats/js/gac_common.js`

```javascript
// Fonctions communes du module GAC

// Initialisation Select2 pour tous les selects
$(document).ready(function() {
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: '-- Sélectionner --'
    });
});

// Autocomplétion d'articles
function initArticleAutocomplete(selector) {
    $(selector).select2({
        ajax: {
            url: '/gestion-achats/api/articles/recherche/',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(article) {
                        return {
                            id: article.id,
                            text: article.reference + ' - ' + article.designation,
                            article: article
                        };
                    })
                };
            }
        },
        minimumInputLength: 2
    });
}

// Calcul automatique de montant
function calculerMontant(quantiteId, prixId, montantId) {
    const quantite = parseFloat($('#' + quantiteId).val()) || 0;
    const prix = parseFloat($('#' + prixId).val()) || 0;
    const montant = quantite * prix;

    $('#' + montantId).val(montant.toFixed(2) + ' €');
}

// Confirmation de suppression
function confirmerSuppression(message) {
    return confirm(message || 'Êtes-vous sûr de vouloir supprimer cet élément ?');
}
```

---

**Fin des spécifications des templates**

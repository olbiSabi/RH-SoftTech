/**
 * Fonctions JavaScript communes pour le module GAC
 * (Gestion des Achats & Commandes)
 */

// ============================================
// GESTION DU CSRF TOKEN POUR AJAX
// ============================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Configuration des requêtes AJAX avec le token CSRF
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// ============================================
// CONFIRMATIONS D'ACTIONS
// ============================================

/**
 * Affiche une modal de confirmation avant une action
 */
function confirmAction(message, onConfirm, title = 'Confirmation') {
    if (confirm(`${title}\n\n${message}`)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
        return true;
    }
    return false;
}

/**
 * Confirmation pour soumettre une demande
 */
function confirmSubmitDemande() {
    return confirmAction(
        'Voulez-vous vraiment soumettre cette demande pour validation ?\n\nUne fois soumise, vous ne pourrez plus la modifier.',
        null,
        'Soumettre la demande'
    );
}

/**
 * Confirmation pour valider une demande
 */
function confirmValidateDemande(niveau) {
    return confirmAction(
        `Confirmer la validation de cette demande (niveau ${niveau}) ?`,
        null,
        'Validation de demande'
    );
}

/**
 * Confirmation pour refuser une demande
 */
function confirmRejectDemande() {
    return confirmAction(
        'Êtes-vous sûr de vouloir refuser cette demande ?\n\nCette action est définitive.',
        null,
        'Refuser la demande'
    );
}

/**
 * Confirmation pour annuler une demande
 */
function confirmCancelDemande() {
    return confirmAction(
        'Voulez-vous vraiment annuler cette demande ?\n\nCette action est irréversible.',
        null,
        'Annuler la demande'
    );
}

/**
 * Confirmation pour émettre un bon de commande
 */
function confirmEmitBC() {
    return confirmAction(
        'Confirmer l\'émission de ce bon de commande ?',
        null,
        'Émettre le BC'
    );
}

/**
 * Confirmation pour envoyer un BC au fournisseur
 */
function confirmSendBC() {
    return confirmAction(
        'Envoyer ce bon de commande au fournisseur par email ?',
        null,
        'Envoyer le BC'
    );
}

/**
 * Confirmation pour supprimer une ligne
 */
function confirmDeleteLine() {
    return confirmAction(
        'Êtes-vous sûr de vouloir supprimer cette ligne ?',
        null,
        'Supprimer la ligne'
    );
}

// ============================================
// CALCULS AUTOMATIQUES DANS LES FORMULAIRES
// ============================================

/**
 * Calcule le montant TTC d'une ligne
 */
function calculerMontantLigne(quantite, prixUnitaire, tauxTVA) {
    const qty = parseFloat(quantite) || 0;
    const prix = parseFloat(prixUnitaire) || 0;
    const tva = parseFloat(tauxTVA) || 0;

    const montantHT = qty * prix;
    const montantTVA = montantHT * (tva / 100);
    const montantTTC = montantHT + montantTVA;

    return {
        montantHT: montantHT.toFixed(2),
        montantTVA: montantTVA.toFixed(2),
        montantTTC: montantTTC.toFixed(2)
    };
}

/**
 * Met à jour les montants d'une ligne de formulaire
 */
function updateLigneMontants(quantiteInput, prixInput, tvaInput) {
    const quantite = parseFloat(quantiteInput.value) || 0;
    const prix = parseFloat(prixInput.value) || 0;
    const tva = parseFloat(tvaInput.value) || 0;

    const montants = calculerMontantLigne(quantite, prix, tva);

    // Mettre à jour les champs d'affichage si présents
    const montantHTDisplay = document.getElementById('montant_ht_display');
    const montantTVADisplay = document.getElementById('montant_tva_display');
    const montantTTCDisplay = document.getElementById('montant_ttc_display');

    if (montantHTDisplay) montantHTDisplay.textContent = `${montants.montantHT} €`;
    if (montantTVADisplay) montantTVADisplay.textContent = `${montants.montantTVA} €`;
    if (montantTTCDisplay) montantTTCDisplay.textContent = `${montants.montantTTC} €`;
}

/**
 * Initialise les calculs automatiques sur un formulaire de ligne
 */
function initLigneCalculator() {
    const quantiteInput = document.getElementById('id_quantite');
    const prixInput = document.getElementById('id_prix_unitaire');
    const tvaInput = document.getElementById('id_taux_tva');

    if (quantiteInput && prixInput && tvaInput) {
        [quantiteInput, prixInput, tvaInput].forEach(input => {
            input.addEventListener('input', () => {
                updateLigneMontants(quantiteInput, prixInput, tvaInput);
            });
        });

        // Calcul initial
        updateLigneMontants(quantiteInput, prixInput, tvaInput);
    }
}

// ============================================
// FILTRAGE ET RECHERCHE
// ============================================

/**
 * Filtre une table selon un terme de recherche
 */
function filterTable(searchInput, tableId) {
    const filter = searchInput.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;

        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }

        row.style.display = found ? '' : 'none';
    }
}

/**
 * Initialise la recherche instantanée sur une table
 */
function initTableSearch(searchInputId, tableId) {
    const searchInput = document.getElementById(searchInputId);
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            filterTable(this, tableId);
        });
    }
}

// ============================================
// GESTION DES FORMULAIRES DYNAMIQUES
// ============================================

/**
 * Ajoute une ligne dans un formset Django
 */
function addFormsetRow(formsetPrefix, containerSelector, emptyFormSelector) {
    const container = document.querySelector(containerSelector);
    const emptyForm = document.querySelector(emptyFormSelector);

    if (!container || !emptyForm) {
        console.error('Container ou empty form non trouvé');
        return;
    }

    // Récupérer le nombre total de formulaires
    const totalForms = document.querySelector(`#id_${formsetPrefix}-TOTAL_FORMS`);
    const currentFormCount = parseInt(totalForms.value);

    // Cloner le formulaire vide et remplacer __prefix__
    const newForm = emptyForm.cloneNode(true);
    const formHtml = newForm.innerHTML.replace(/__prefix__/g, currentFormCount);

    // Créer un nouveau div pour la ligne
    const newRow = document.createElement('div');
    newRow.className = 'formset-row';
    newRow.innerHTML = formHtml;

    // Ajouter au container
    container.appendChild(newRow);

    // Incrémenter le compteur
    totalForms.value = currentFormCount + 1;

    return newRow;
}

/**
 * Supprime une ligne de formset
 */
function removeFormsetRow(button, formsetPrefix) {
    const row = button.closest('.formset-row');
    if (!row) return;

    // Marquer comme supprimé au lieu de vraiment supprimer
    const deleteCheckbox = row.querySelector(`input[name$='-DELETE']`);
    if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        row.style.display = 'none';
    } else {
        row.remove();
    }
}

// ============================================
// FORMATAGE DES MONTANTS
// ============================================

/**
 * Formate un nombre en montant EUR
 */
function formatMontant(montant, decimales = 2) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: decimales,
        maximumFractionDigits: decimales
    }).format(montant);
}

/**
 * Formate tous les éléments avec la classe .montant
 */
function formatAllMontants() {
    document.querySelectorAll('.montant').forEach(element => {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            element.textContent = formatMontant(value);
        }
    });
}

// ============================================
// GESTION DES ALERTES
// ============================================

/**
 * Affiche une alerte temporaire
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertContainer.appendChild(alert);

    // Auto-fermeture après le délai
    if (duration > 0) {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, duration);
    }

    return alert;
}

/**
 * Crée un conteneur pour les alertes s'il n'existe pas
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============================================
// VALIDATION DE FORMULAIRES
// ============================================

/**
 * Valide un numéro SIRET
 */
function validateSIRET(siret) {
    // Enlever les espaces
    siret = siret.replace(/\s/g, '');

    // Vérifier la longueur
    if (siret.length !== 14) {
        return false;
    }

    // Vérifier que ce sont bien des chiffres
    if (!/^\d+$/.test(siret)) {
        return false;
    }

    // Algorithme de Luhn
    let sum = 0;
    for (let i = 0; i < 14; i++) {
        let digit = parseInt(siret.charAt(i));
        if (i % 2 === 0) {
            digit *= 2;
            if (digit > 9) {
                digit -= 9;
            }
        }
        sum += digit;
    }

    return sum % 10 === 0;
}

/**
 * Valide un email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Ajoute la validation en temps réel sur un champ SIRET
 */
function initSIRETValidation(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value && !validateSIRET(value)) {
            this.classList.add('is-invalid');
            let feedback = this.nextElementSibling;
            if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                this.parentNode.appendChild(feedback);
            }
            feedback.textContent = 'Le numéro SIRET est invalide (14 chiffres requis)';
        } else {
            this.classList.remove('is-invalid');
        }
    });

    input.addEventListener('input', function() {
        this.classList.remove('is-invalid');
    });
}

// ============================================
// GESTION DU BUDGET
// ============================================

/**
 * Met à jour la barre de progression du budget
 */
function updateBudgetProgress(budgetId, montantConsomme, montantTotal) {
    const progressBar = document.querySelector(`#budget-${budgetId} .budget-progress-bar`);
    if (!progressBar) return;

    const pourcentage = (montantConsomme / montantTotal) * 100;
    progressBar.style.width = `${pourcentage}%`;
    progressBar.textContent = `${pourcentage.toFixed(1)}%`;

    // Changer la couleur selon le seuil
    progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
    if (pourcentage < 80) {
        progressBar.classList.add('bg-success');
    } else if (pourcentage < 95) {
        progressBar.classList.add('bg-warning');
    } else {
        progressBar.classList.add('bg-danger');
    }
}

// ============================================
// AJAX HELPERS
// ============================================

/**
 * Effectue une requête AJAX sécurisée avec gestion d'erreurs
 */
async function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    // Ajouter le token CSRF pour les requêtes non-GET
    if (!csrfSafeMethod(options.method || 'GET')) {
        defaultOptions.headers['X-CSRFToken'] = csrftoken;
    }

    const config = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    } catch (error) {
        console.error('Erreur AJAX:', error);
        showAlert(`Erreur: ${error.message}`, 'danger');
        throw error;
    }
}

// ============================================
// INITIALISATION AU CHARGEMENT DE LA PAGE
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Formater tous les montants
    formatAllMontants();

    // Initialiser le calculateur de ligne si présent
    initLigneCalculator();

    // Auto-fermeture des messages Django après 5 secondes
    const djangoMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    djangoMessages.forEach(alert => {
        if (!alert.classList.contains('alert-permanent')) {
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }, 5000);
        }
    });

    // Initialiser les tooltips Bootstrap si disponibles
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialiser les popovers Bootstrap si disponibles
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Ajouter la confirmation sur les boutons de suppression
    document.querySelectorAll('.btn-delete, .btn-danger[type="submit"]').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.hasAttribute('data-no-confirm')) {
                if (!confirm('Êtes-vous sûr de vouloir effectuer cette action ?')) {
                    e.preventDefault();
                    return false;
                }
            }
        });
    });

    console.log('GAC Common JS initialized');
});

// ============================================
// EXPORT DES FONCTIONS GLOBALES
// ============================================

// Exposer les fonctions principales dans le scope global
window.GAC = {
    // Confirmations
    confirmAction,
    confirmSubmitDemande,
    confirmValidateDemande,
    confirmRejectDemande,
    confirmCancelDemande,
    confirmEmitBC,
    confirmSendBC,
    confirmDeleteLine,

    // Calculs
    calculerMontantLigne,
    updateLigneMontants,

    // Formatage
    formatMontant,
    formatAllMontants,

    // Alertes
    showAlert,

    // Validation
    validateSIRET,
    validateEmail,
    initSIRETValidation,

    // Budget
    updateBudgetProgress,

    // AJAX
    ajaxRequest,

    // Formsets
    addFormsetRow,
    removeFormsetRow,

    // Recherche
    filterTable,
    initTableSearch
};

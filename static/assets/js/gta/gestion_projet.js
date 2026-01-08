// static/assets/js/gta/gestion_projet.js
/**
 * ============================================
 * GESTION DES PROJETS - SCRIPTS
 * ============================================
 */

(function() {
    'use strict';

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initProjetManagement();
    });

    /**
     * Initialisation principale
     */
    function initProjetManagement() {
        // Conversion automatique en majuscules pour le code projet
        initCodeProjetUppercase();

        // Validation du formulaire
        initFormValidation();

        // Confirmation de suppression
        initDeleteConfirmation();

        // Gestion des dates
        initDateValidation();

        // Gestion du budget
        initBudgetCalculation();

        // Filtres et recherche
        initFilters();

        // Tooltips
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();

        // Animations
        animateElements();

        // Calcul de durée entre dates
        initDurationCalculator();

        // Validation des champs numériques
        initNumericValidation();
    }

    // ==================== CODE PROJET MAJUSCULES ====================
    /**
     * Convertit automatiquement le code projet en majuscules
     */
    function initCodeProjetUppercase() {
        const codeProjetInput = document.getElementById('id_code_projet');
        if (codeProjetInput) {
            codeProjetInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase().trim();
            });

            // Appliquer au chargement
            if (codeProjetInput.value) {
                codeProjetInput.value = codeProjetInput.value.toUpperCase();
            }
        }
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire projet
     */
    function initFormValidation() {
        const form = document.getElementById('projetForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            // Validation code projet
            const codeProjet = document.getElementById('id_code_projet');
            if (codeProjet && !codeProjet.value.trim()) {
                isValid = false;
                markFieldInvalid(codeProjet, 'Le code projet est obligatoire');
                errors.push('Code projet manquant');
            }

            // Validation nom projet
            const nomProjet = document.getElementById('id_nom_projet');
            if (nomProjet && !nomProjet.value.trim()) {
                isValid = false;
                markFieldInvalid(nomProjet, 'Le nom du projet est obligatoire');
                errors.push('Nom du projet manquant');
            }

            // Validation client
            const client = document.getElementById('id_client');
            if (client && !client.value) {
                isValid = false;
                markFieldInvalid(client, 'Veuillez sélectionner un client');
                errors.push('Client non sélectionné');
            }

            // Validation dates
            const dateDebut = document.getElementById('id_date_debut');
            const dateFinPrevue = document.getElementById('id_date_fin_prevue');
            if (dateDebut && dateFinPrevue && dateDebut.value && dateFinPrevue.value) {
                if (new Date(dateFinPrevue.value) < new Date(dateDebut.value)) {
                    isValid = false;
                    markFieldInvalid(dateFinPrevue, 'La date de fin doit être après la date de début');
                    errors.push('Dates incohérentes');
                }
            }

            if (!isValid) {
                e.preventDefault();
                showNotification('Veuillez corriger les erreurs : ' + errors.join(', '), 'error');

                // Scroll vers le premier champ invalide
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
        });

        // Retirer l'erreur lors de la saisie
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    this.classList.remove('is-invalid');
                    const errorDiv = this.parentNode.querySelector('.text-danger');
                    if (errorDiv) errorDiv.remove();
                }
            });
        });
    }

    /**
     * Marque un champ comme invalide
     */
    function markFieldInvalid(field, message) {
        field.classList.add('is-invalid');

        // Supprimer l'erreur existante
        const existingError = field.parentNode.querySelector('.text-danger.small');
        if (existingError) existingError.remove();

        // Ajouter le message d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-danger small mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    // ==================== VALIDATION DES DATES ====================
    /**
     * Validation des dates du projet
     */
    function initDateValidation() {
        const dateDebut = document.getElementById('id_date_debut');
        const dateFinPrevue = document.getElementById('id_date_fin_prevue');
        const dateFinReelle = document.getElementById('id_date_fin_reelle');

        if (!dateDebut || !dateFinPrevue) return;

        // Validation date fin prévue
        dateFinPrevue.addEventListener('change', function() {
            if (dateDebut.value && this.value) {
                if (new Date(this.value) < new Date(dateDebut.value)) {
                    markFieldInvalid(this, 'La date de fin doit être postérieure à la date de début');
                } else {
                    this.classList.remove('is-invalid');
                    const errorDiv = this.parentNode.querySelector('.text-danger');
                    if (errorDiv) errorDiv.remove();
                }
            }
        });

        // Validation date fin réelle
        if (dateFinReelle) {
            dateFinReelle.addEventListener('change', function() {
                if (dateDebut.value && this.value) {
                    if (new Date(this.value) < new Date(dateDebut.value)) {
                        markFieldInvalid(this, 'La date de fin réelle doit être postérieure à la date de début');
                    }
                }
            });
        }
    }

    // ==================== CALCUL DE DURÉE ====================
    /**
     * Calcule et affiche la durée du projet
     */
    function initDurationCalculator() {
        const dateDebut = document.getElementById('id_date_debut');
        const dateFinPrevue = document.getElementById('id_date_fin_prevue');

        if (!dateDebut || !dateFinPrevue) return;

        function calculateDuration() {
            if (dateDebut.value && dateFinPrevue.value) {
                const debut = new Date(dateDebut.value);
                const fin = new Date(dateFinPrevue.value);
                const diffTime = Math.abs(fin - debut);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                // Afficher la durée
                let durationText = '';
                if (diffDays > 365) {
                    const years = Math.floor(diffDays / 365);
                    const months = Math.floor((diffDays % 365) / 30);
                    durationText = `${years} an(s) ${months} mois`;
                } else if (diffDays > 30) {
                    const months = Math.floor(diffDays / 30);
                    const days = diffDays % 30;
                    durationText = `${months} mois ${days} jour(s)`;
                } else {
                    durationText = `${diffDays} jour(s)`;
                }

                // Créer ou mettre à jour l'affichage
                let durationDisplay = document.getElementById('duration-display');
                if (!durationDisplay) {
                    durationDisplay = document.createElement('small');
                    durationDisplay.id = 'duration-display';
                    durationDisplay.className = 'text-muted d-block mt-1';
                    dateFinPrevue.parentNode.appendChild(durationDisplay);
                }
                durationDisplay.innerHTML = `<i class="fas fa-calendar-alt"></i> Durée: ${durationText}`;
            }
        }

        dateDebut.addEventListener('change', calculateDuration);
        dateFinPrevue.addEventListener('change', calculateDuration);

        // Calculer au chargement si les dates sont présentes
        if (dateDebut.value && dateFinPrevue.value) {
            calculateDuration();
        }
    }

    // ==================== GESTION DU BUDGET ====================
    /**
     * Calculs et alertes sur le budget
     */
    function initBudgetCalculation() {
        const budgetHeures = document.getElementById('id_budget_heures');
        const budgetMontant = document.getElementById('id_budget_montant');

        if (!budgetHeures && !budgetMontant) return;

        // Calculer le taux horaire moyen
        function calculateHourlyRate() {
            if (budgetHeures && budgetMontant && budgetHeures.value && budgetMontant.value) {
                const heures = parseFloat(budgetHeures.value);
                const montant = parseFloat(budgetMontant.value);

                if (heures > 0) {
                    const tauxHoraire = montant / heures;

                    let rateDisplay = document.getElementById('hourly-rate-display');
                    if (!rateDisplay) {
                        rateDisplay = document.createElement('small');
                        rateDisplay.id = 'hourly-rate-display';
                        rateDisplay.className = 'text-info d-block mt-1';
                        budgetMontant.parentNode.appendChild(rateDisplay);
                    }
                    rateDisplay.innerHTML = `<i class="fas fa-calculator"></i> Taux horaire moyen: ${tauxHoraire.toLocaleString('fr-FR', {minimumFractionDigits: 0, maximumFractionDigits: 0})} FCFA/h`;
                }
            }
        }

        if (budgetHeures) budgetHeures.addEventListener('input', calculateHourlyRate);
        if (budgetMontant) budgetMontant.addEventListener('input', calculateHourlyRate);

        // Calculer au chargement
        calculateHourlyRate();
    }

    // ==================== VALIDATION NUMÉRIQUE ====================
    /**
     * Validation des champs numériques
     */
    function initNumericValidation() {
        const numericInputs = document.querySelectorAll('input[type="number"]');

        numericInputs.forEach(function(input) {
            input.addEventListener('input', function() {
                // Supprimer les caractères non numériques
                this.value = this.value.replace(/[^0-9.,]/g, '');

                // Vérifier la valeur minimale
                const min = parseFloat(this.getAttribute('min'));
                if (!isNaN(min) && parseFloat(this.value) < min) {
                    markFieldInvalid(this, `La valeur doit être au moins ${min}`);
                }
            });
        });
    }

    // ==================== CONFIRMATION SUPPRESSION ====================
    /**
     * Confirmation avant suppression avec double vérification si tâches
     */
    function initDeleteConfirmation() {
        const deleteButton = document.querySelector('button[type="submit"].btn-danger');
        if (!deleteButton) return;

        deleteButton.addEventListener('click', function(e) {
            const tachesCount = this.dataset.tachesCount;

            if (tachesCount && parseInt(tachesCount) > 0) {
                e.preventDefault();

                const confirmMessage = `⚠️ ATTENTION !\n\nCe projet contient ${tachesCount} tâche(s) avec leurs imputations temps.\n\nToutes ces données seront définitivement supprimées.\n\nÊtes-vous ABSOLUMENT CERTAIN de vouloir continuer ?`;

                if (confirm(confirmMessage)) {
                    // Seconde confirmation
                    const doubleConfirm = confirm('Dernière confirmation : Voulez-vous vraiment supprimer ce projet et toutes ses données ?');
                    if (doubleConfirm) {
                        this.form.submit();
                    }
                }
            }
        });
    }

// ==================== FILTRES ====================
/**
 * Gestion des filtres
 */
function initFilters() {
    // Vérifier si on est sur la page liste des projets
    // en cherchant la table spécifique à la liste
    const projetListeTable = document.querySelector('.projet-table');

    if (projetListeTable) {
        // On est sur la page liste des projets
        const searchInput = document.querySelector('input[name="search"]');
        const filterSelects = document.querySelectorAll('select[name="statut"], select[name="client"], select[name="actif"]');

        // Auto-submit après sélection (UNIQUEMENT sur la page liste)
        filterSelects.forEach(function(select) {
            select.addEventListener('change', function() {
                // Vérifier qu'on est dans le formulaire de filtres (pas un autre)
                if (this.closest('form') && this.closest('form').method === 'get') {
                    this.form.submit();
                }
            });
        });

        // Focus sur recherche avec Ctrl+F (UNIQUEMENT sur la page liste)
        if (searchInput) {
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                    e.preventDefault();
                    searchInput.focus();
                    searchInput.select();
                }
            });
        }
    }
    // Ne rien faire sur les autres pages (comme le formulaire de création)
}

    // ==================== TOOLTIPS ====================
    /**
     * Initialise les tooltips Bootstrap
     */
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-toggle="tooltip"], [title]')
        );
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // ==================== AUTO-DISMISS ALERTS ====================
    /**
     * Ferme automatiquement les alertes après 5 secondes
     */
    function autoDismissAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 10000);
        });
    }

    // ==================== ANIMATIONS ====================
    /**
     * Animations d'entrée
     */
    function animateElements() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(function(card, index) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(function() {
                card.style.transition = 'all 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

    // ==================== NOTIFICATIONS ====================
    /**
     * Affiche une notification
     */
    function showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);

            setTimeout(function() {
                alertDiv.remove();
            }, 5000);
        }
    }

    // ==================== UTILITAIRES ====================
    /**
     * Formater un nombre avec séparateurs
     */
    window.formatNumber = function(number) {
        return number.toLocaleString('fr-FR');
    };

    /**
     * Copier dans le presse-papier
     */
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('Copié dans le presse-papier', 'success');
        }).catch(function(err) {
            console.error('Erreur de copie:', err);
            showNotification('Erreur lors de la copie', 'error');
        });
    };

})();

 // Empêcher la re-soumission du formulaire lors de l'actualisation
        if (window.history.replaceState) {
            window.history.replaceState(null, null, window.location.href);
        }
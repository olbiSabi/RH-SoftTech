// static/assets/js/gta/gestion_imputation.js

/**
 * ============================================
 * GESTION DES IMPUTATIONS - SCRIPTS
 * ============================================ */

(function() {
    'use strict';

    // ==================== VARIABLES GLOBALES ====================
    let timerInterval = null;
    let timerSeconds = 0;
    let selectedImputations = new Set();

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initImputationManagement();
    });

    /**
     * Initialisation principale
     */
    function initImputationManagement() {
        // Validation du formulaire
        initFormValidation();

        // Filtrage dynamique des tâches par projet
        initProjetTacheFilter();

        // Saisie rapide de durée
        initQuickDuration();

        // Résumé temps réel
        initLiveSummary();

        // Gestion de la période
        initPeriodeToggle();

        // Sélection multiple pour validation
        initBulkValidation();

        // Validation du motif de rejet
        initRejetValidation();

        // Export Excel
        initExportFunctions();

        // Filtres auto-submit
        initFilters();

        // Tooltips
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();

        // Animations
        animateElements();

        // Timer optionnel
        // initTimer();

        // Graphiques
        initCharts();
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire imputation
     */
    function initFormValidation() {
        const form = document.getElementById('imputationForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            // Validation date
            const dateInput = document.getElementById('id_date');
            if (dateInput && dateInput.value) {
                const selectedDate = new Date(dateInput.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (selectedDate > today) {
                    isValid = false;
                    markFieldInvalid(dateInput, 'La date ne peut pas être dans le futur');
                    errors.push('Date future');
                }
            } else if (dateInput) {
                isValid = false;
                markFieldInvalid(dateInput, 'La date est obligatoire');
                errors.push('Date manquante');
            }

            // Validation tâche
            const tache = document.getElementById('id_tache');
            if (tache && !tache.value) {
                isValid = false;
                markFieldInvalid(tache, 'Veuillez sélectionner une tâche');
                errors.push('Tâche manquante');
            }

            // Validation activité
            const activite = document.getElementById('id_activite');
            if (activite && !activite.value) {
                isValid = false;
                markFieldInvalid(activite, 'Veuillez sélectionner une activité');
                errors.push('Activité manquante');
            }

            // Validation durée
            const duree = document.getElementById('id_duree');
            if (duree && duree.value) {
                const dureeValue = parseFloat(duree.value);
                if (dureeValue <= 0) {
                    isValid = false;
                    markFieldInvalid(duree, 'La durée doit être supérieure à 0');
                    errors.push('Durée invalide');
                } else if (dureeValue > 24) {
                    isValid = false;
                    markFieldInvalid(duree, 'La durée ne peut pas dépasser 24 heures');
                    errors.push('Durée trop élevée');
                }
            } else if (duree) {
                isValid = false;
                markFieldInvalid(duree, 'La durée est obligatoire');
                errors.push('Durée manquante');
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

    // ==================== FILTRAGE PROJET-TÂCHE ====================
    /**
     * Filtre les tâches selon le projet sélectionné
     */
    function initProjetTacheFilter() {
        const projetSelect = document.getElementById('projet-select');
        const tacheSelect = document.getElementById('id_tache');

        if (!projetSelect || !tacheSelect) return;

        // Sauvegarder toutes les options
        const allTaches = Array.from(tacheSelect.options);

        projetSelect.addEventListener('change', function() {
            const selectedProjet = this.value;

            // Réinitialiser les tâches
            tacheSelect.innerHTML = '<option value="">Sélectionnez une tâche</option>';

            if (selectedProjet) {
                // Appel AJAX pour charger les tâches du projet
                fetch(`/gestion-temps/api/projet/${selectedProjet}/taches/`)
                    .then(response => response.json())
                    .then(data => {
                        data.taches.forEach(tache => {
                            const option = document.createElement('option');
                            option.value = tache.id;
                            option.textContent = tache.titre;
                            tacheSelect.appendChild(option);
                        });

                        if (data.taches.length === 0) {
                            showNotification('Aucune tâche disponible pour ce projet', 'warning');
                        }
                    })
                    .catch(error => {
                        console.error('Erreur:', error);
                        showNotification('Erreur lors du chargement des tâches', 'error');
                    });
            }
        });

        // Pré-sélection si paramètre GET
        const urlParams = new URLSearchParams(window.location.search);
        const tacheId = urlParams.get('tache');
        if (tacheId) {
            // Trouver le projet de cette tâche
            allTaches.forEach(option => {
                if (option.value === tacheId) {
                    // Déclencher le chargement des tâches puis sélectionner
                    setTimeout(() => {
                        tacheSelect.value = tacheId;
                    }, 500);
                }
            });
        }
    }

    // ==================== SAISIE RAPIDE DURÉE ====================
    /**
     * Boutons de saisie rapide pour la durée
     */
    function initQuickDuration() {
        window.setDuree = function(heures) {
            const dureeInput = document.getElementById('id_duree');
            if (dureeInput) {
                dureeInput.value = heures;
                dureeInput.dispatchEvent(new Event('input', { bubbles: true }));

                // Animation feedback
                dureeInput.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    dureeInput.style.transform = 'scale(1)';
                }, 200);
            }
        };
    }

    // ==================== RÉSUMÉ TEMPS RÉEL ====================
    /**
     * Affiche un résumé de l'imputation en temps réel
     */
    function initLiveSummary() {
        const form = document.getElementById('imputationForm');
        if (!form) return;

        const dateInput = document.getElementById('id_date');
        const tacheSelect = document.getElementById('id_tache');
        const activiteSelect = document.getElementById('id_activite');
        const dureeInput = document.getElementById('id_duree');
        const summaryDiv = document.getElementById('imputation-summary');
        const summaryContent = document.getElementById('summary-content');

        if (!summaryDiv || !summaryContent) return;

        function updateSummary() {
            const date = dateInput?.value;
            const tacheText = tacheSelect?.options[tacheSelect.selectedIndex]?.text;
            const activiteText = activiteSelect?.options[activiteSelect.selectedIndex]?.text;
            const duree = dureeInput?.value;

            if (date && tacheText && activiteText && duree) {
                const summaryHTML = `
                    <div class="summary-item">
                        <span class="summary-label">Date :</span>
                        <span class="summary-value">${new Date(date).toLocaleDateString('fr-FR')}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Tâche :</span>
                        <span class="summary-value">${tacheText}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Activité :</span>
                        <span class="summary-value">${activiteText}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Durée :</span>
                        <span class="summary-value summary-highlight">${duree} heure(s)</span>
                    </div>
                `;

                summaryContent.innerHTML = summaryHTML;
                summaryDiv.style.display = 'block';
            } else {
                summaryDiv.style.display = 'none';
            }
        }

        [dateInput, tacheSelect, activiteSelect, dureeInput].forEach(element => {
            if (element) {
                element.addEventListener('change', updateSummary);
                element.addEventListener('input', updateSummary);
            }
        });

        // Mise à jour initiale
        updateSummary();
    }

    // ==================== GESTION PÉRIODE ====================
    /**
     * Affiche/masque les champs de dates selon la période
     */
    function initPeriodeToggle() {
        const periodeSelect = document.getElementById('periode');
        const dateDebutGroup = document.getElementById('date-debut-group');
        const dateFinGroup = document.getElementById('date-fin-group');

        if (!periodeSelect) return;

        function updateDateFields() {
            const periode = periodeSelect.value;

            if (periode === 'personnalisee') {
                if (dateDebutGroup) dateDebutGroup.style.display = 'block';
                if (dateFinGroup) dateFinGroup.style.display = 'block';
            } else {
                if (dateDebutGroup) dateDebutGroup.style.display = 'none';
                if (dateFinGroup) dateFinGroup.style.display = 'none';
            }
        }

        periodeSelect.addEventListener('change', updateDateFields);

        // Mise à jour initiale
        updateDateFields();
    }

    // ==================== VALIDATION EN MASSE ====================
    /**
     * Sélection multiple pour validation en masse
     */
    function initBulkValidation() {
        const selectAll = document.getElementById('select-all');
        const checkboxes = document.querySelectorAll('.imputation-checkbox');

        if (!selectAll) return;

        // Sélectionner/désélectionner tout
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                updateRowSelection(checkbox);
            });
            updateSelectedCount();
        });

        // Sélection individuelle
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateRowSelection(this);
                updateSelectAllState();
                updateSelectedCount();
            });
        });

        function updateRowSelection(checkbox) {
            const row = checkbox.closest('tr');
            if (checkbox.checked) {
                row.classList.add('selected');
                selectedImputations.add(checkbox.value);
            } else {
                row.classList.remove('selected');
                selectedImputations.delete(checkbox.value);
            }
        }

        function updateSelectAllState() {
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            const someChecked = Array.from(checkboxes).some(cb => cb.checked);

            if (selectAll) {
                selectAll.checked = allChecked;
                selectAll.indeterminate = someChecked && !allChecked;
            }
        }

        function updateSelectedCount() {
            // Mettre à jour le compteur dans le header si présent
            const countDisplay = document.getElementById('selected-count');
            if (countDisplay) {
                countDisplay.textContent = selectedImputations.size;
            }
        }
    }

    /**
     * Valider les imputations sélectionnées
     */
    window.validateSelected = function() {
        if (selectedImputations.size === 0) {
            showNotification('Veuillez sélectionner au moins une imputation', 'warning');
            return;
        }

        if (!confirm(`Voulez-vous valider ${selectedImputations.size} imputation(s) ?`)) {
            return;
        }

        // Appel AJAX pour validation en masse
        showLoading();

        fetch('/gestion-temps/imputations/valider-masse/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                imputations: Array.from(selectedImputations)
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification(`${data.count} imputation(s) validée(s) avec succès`, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification('Erreur lors de la validation : ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Erreur:', error);
            showNotification('Erreur lors de la validation', 'error');
        });
    };

    // ==================== VALIDATION REJET ====================
    /**
     * Validation du formulaire de rejet
     */
    function initRejetValidation() {
        const motifInput = document.getElementById('motif_rejet');
        if (!motifInput) return;

        // Compteur de caractères
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        motifInput.parentNode.appendChild(counter);

        function updateCounter() {
            const length = motifInput.value.length;
            const minLength = 10;

            counter.textContent = `${length} caractère(s)`;

            if (length < minLength) {
                counter.classList.add('warning');
                counter.textContent += ` (minimum ${minLength})`;
            } else {
                counter.classList.remove('warning');
            }
        }

        motifInput.addEventListener('input', updateCounter);
        updateCounter();
    }

    // ==================== EXPORT EXCEL ====================
    /**
     * Export des données en Excel
     */
    function exportToExcel() {
    // Récupérer les paramètres de filtres
    const params = new URLSearchParams(window.location.search);

    // Construire l'URL d'export
    let exportUrl = '{% url "gestion_temps_activite:imputation_export_excel" %}';

    if (params.toString()) {
        exportUrl += '?' + params.toString();
    }

    // Ouvrir l'URL dans un nouvel onglet
    window.open(exportUrl, '_blank');
}

// ==================== FILTRES ====================
/**
 * Auto-submit des filtres (UNIQUEMENT sur les pages de liste)
 */

function initFilters() {
    // Identifier les formulaires de recherche spécifiques
    const searchForms = document.querySelectorAll('form[role="search"], form.filter-form, form[action*="liste"], form[method="get"]:not(#imputationForm):not(.form-create):not(.form-update)');

    // Si aucun formulaire de recherche n'est trouvé, on ne fait rien
    if (searchForms.length === 0) return;

    searchForms.forEach(form => {
        // Ne cibler que les formulaires qui ont des champs de filtre typiques
        const hasFilterFields = form.querySelector('select[name], input[type="date"][name], input[name="search"], input[name="q"]');

        if (hasFilterFields) {
            const filterSelects = form.querySelectorAll('select[name]:not([name="page"]), input[type="date"][name], select[name="valide"], select[name="facture"], select[name="statut"], select[name="type_client"]');

            filterSelects.forEach(select => {
                select.addEventListener('change', function() {
                    // Désactiver l'auto-submit si le champ est dans un formulaire non-filtre
                    if (this.closest('#imputationForm, .form-create, .form-update')) {
                        return;
                    }

                    // Debounce pour éviter trop de soumissions
                    clearTimeout(this.submitTimer);
                    this.submitTimer = setTimeout(() => {
                        // Si c'est un champ de pagination, ne pas soumettre
                        if (this.name === 'page') return;

                        form.submit();
                    }, 300);
                });
            });

            // Pour les champs de recherche textuelle, ajouter un délai plus long
            const searchInputs = form.querySelectorAll('input[name="search"], input[name="q"]');
            searchInputs.forEach(input => {
                let searchTimer;
                input.addEventListener('input', function() {
                    clearTimeout(searchTimer);
                    searchTimer = setTimeout(() => {
                        form.submit();
                    }, 800); // Délai plus long pour la recherche textuelle
                });
            });
        }
    });
}

    // ==================== GRAPHIQUES ====================
    /**
     * Initialisation des graphiques (Chart.js)
     */
    function initCharts() {
        // Graphique par projet
        const projetCanvas = document.getElementById('projetChart');
        if (projetCanvas && typeof projetData !== 'undefined') {
            new Chart(projetCanvas, {
                type: 'doughnut',
                data: {
                    labels: projetData.labels,
                    datasets: [{
                        data: projetData.values,
                        backgroundColor: [
                            '#4e73df',
                            '#1cc88a',
                            '#36b9cc',
                            '#f6c23e',
                            '#e74a3b',
                            '#858796'
                        ]
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Graphique par activité
        const activiteCanvas = document.getElementById('activiteChart');
        if (activiteCanvas && typeof activiteData !== 'undefined') {
            new Chart(activiteCanvas, {
                type: 'bar',
                data: {
                    labels: activiteData.labels,
                    datasets: [{
                        label: 'Heures',
                        data: activiteData.values,
                        backgroundColor: '#4e73df'
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }

    // ==================== TIMER (OPTIONNEL) ====================
    /**
     * Timer pour suivre le temps en direct
     */
    function initTimer() {
        // À implémenter si besoin
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
            }, 5000);
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
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

    // ==================== UTILITAIRES ====================
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
            window.scrollTo({ top: 0, behavior: 'smooth' });

            setTimeout(function() {
                alertDiv.remove();
            }, 5000);
        }
    }

    /**
     * Affiche un overlay de chargement
     */
    function showLoading() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }

    /**
     * Masque l'overlay de chargement
     */
    function hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    /**
     * Récupère le token CSRF
     */
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

})();


 // Empêcher la re-soumission du formulaire lors de l'actualisation
        if (window.history.replaceState) {
            window.history.replaceState(null, null, window.location.href);
        }
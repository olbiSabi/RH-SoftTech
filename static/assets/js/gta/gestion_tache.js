// static/assets/js/gta/gestion_tache.js

/**
 * ============================================
 * GESTION DES TÂCHES - SCRIPTS
 * ============================================ */

(function() {
    'use strict';

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initTacheManagement();
    });

    /**
     * Initialisation principale
     */
    function initTacheManagement() {
        // Validation du formulaire
        initFormValidation();

        // Aperçu de l'avancement en temps réel
        initAvancementPreview();

        // Validation des dates
        initDateValidation();

        // Calcul automatique d'avancement basé sur statut
        initStatutAutoAvancement();

        // Filtrage dynamique des tâches parentes
        initTacheParenteFilter();

        // Tooltips
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();
    }

    // ==================== FILTRAGE TÂCHE PARENTE ====================
    /**
     * Filtrage dynamique des tâches parentes avec AJAX
     */
    function initTacheParenteFilter() {
        const projetSelect = document.getElementById('id_projet');
        const tacheParenteSelect = document.getElementById('id_tache_parente');

        if (!projetSelect || !tacheParenteSelect) {
            console.log('Éléments de filtrage non trouvés');
            return;
        }

        console.log('Initialisation du filtrage des tâches parentes');

        // Fonction pour charger les tâches d'un projet
        function chargerTachesParProjet(projetId) {
            console.log('Chargement des tâches pour projet:', projetId);

            if (!projetId) {
                // Si pas de projet sélectionné, vider et désactiver
                tacheParenteSelect.innerHTML = '<option value="">---------</option>';
                tacheParenteSelect.disabled = true;

                // Mettre à jour le texte d'aide
                const helpText = document.getElementById('tache-parente-help');
                if (helpText) {
                    helpText.textContent = 'Sélectionnez d\'abord un projet pour voir les tâches disponibles';
                }
                return;
            }

            // Afficher un indicateur de chargement
            tacheParenteSelect.innerHTML = '<option value="">Chargement des tâches...</option>';
            tacheParenteSelect.disabled = true;

            // Obtenir l'ID de la tâche actuelle (si en modification)
            const form = document.getElementById('tacheForm');
            const tacheId = form ? form.dataset.tacheId || '' : '';

            // Construire l'URL de l'API
            let apiUrl = `/gestion-temps/api/projet/${projetId}/taches/`;

            // Si on modifie une tâche existante, exclure cette tâche
            if (tacheId) {
                apiUrl += `?exclure=${tacheId}`;
            }

            console.log('Appel API:', apiUrl);

            // Appel AJAX
            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Tâches reçues:', data);

                    // Réinitialiser le select
                    tacheParenteSelect.innerHTML = '<option value="">---------</option>';
                    tacheParenteSelect.disabled = false;

                    if (data && data.length > 0) {
                        // Récupérer la valeur actuellement sélectionnée (si modification)
                        const currentValue = tacheParenteSelect.dataset.currentValue || '';

                        data.forEach(tache => {
                            const option = document.createElement('option');
                            option.value = tache.id;

                            // Utiliser le format "code_tache - titre" ou juste "titre"
                            const displayText = tache.code_tache
                                ? `${tache.code_tache} - ${tache.titre}`
                                : tache.titre;

                            option.textContent = displayText;

                            // Pré-sélectionner si c'est la valeur actuelle
                            if (currentValue && tache.id.toString() === currentValue.toString()) {
                                option.selected = true;
                            }

                            tacheParenteSelect.appendChild(option);
                        });

                        // Mettre à jour le texte d'aide
                        const helpText = document.getElementById('tache-parente-help');
                        if (helpText) {
                            helpText.textContent = `Sélectionnez une tâche parente si cette tâche est une sous-tâche (${data.length} tâche(s) disponible(s))`;
                        }
                    } else {
                        // Aucune tâche dans ce projet
                        tacheParenteSelect.innerHTML = '<option value="">Aucune tâche disponible dans ce projet</option>';

                        const helpText = document.getElementById('tache-parente-help');
                        if (helpText) {
                            helpText.textContent = 'Aucune tâche disponible dans ce projet';
                        }
                    }
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des tâches:', error);
                    tacheParenteSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                    tacheParenteSelect.disabled = true;

                    // Afficher une notification d'erreur
                    showNotification('Impossible de charger les tâches du projet. Veuillez réessayer.', 'error');

                    const helpText = document.getElementById('tache-parente-help');
                    if (helpText) {
                        helpText.textContent = 'Erreur lors du chargement des tâches';
                    }
                });
        }

        // Événement sur le changement de projet
        projetSelect.addEventListener('change', function() {
            console.log('Projet changé:', this.value);
            chargerTachesParProjet(this.value);
        });

        // Charger initialement si un projet est déjà sélectionné
        if (projetSelect.value) {
            console.log('Projet initial sélectionné:', projetSelect.value);
            // Utiliser setTimeout pour s'assurer que le DOM est prêt
            setTimeout(function() {
                chargerTachesParProjet(projetSelect.value);
            }, 100);
        } else {
            // Si pas de projet sélectionné, désactiver le champ
            tacheParenteSelect.disabled = true;
        }
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire tâche
     */
    function initFormValidation() {
        const form = document.getElementById('tacheForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            // Validation titre
            const titre = document.getElementById('id_titre');
            if (titre && !titre.value.trim()) {
                isValid = false;
                markFieldInvalid(titre, 'Le titre est obligatoire');
                errors.push('Titre manquant');
            }

            // Validation projet
            const projet = document.getElementById('id_projet');
            if (projet && !projet.value) {
                isValid = false;
                markFieldInvalid(projet, 'Veuillez sélectionner un projet');
                errors.push('Projet non sélectionné');
            }

            // Validation avancement (0-100)
            const avancement = document.getElementById('id_avancement');
            if (avancement && avancement.value) {
                const value = parseInt(avancement.value);
                if (value < 0 || value > 100) {
                    isValid = false;
                    markFieldInvalid(avancement, 'L\'avancement doit être entre 0 et 100');
                    errors.push('Avancement invalide');
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

    // ==================== APERÇU AVANCEMENT ====================
    /**
     * Aperçu de l'avancement en temps réel
     */
    function initAvancementPreview() {
        const avancementInput = document.getElementById('id_avancement');
        const avancementPreview = document.getElementById('avancement-preview');
        const avancementText = document.getElementById('avancement-text');

        if (!avancementInput || !avancementPreview) return;

        function updateAvancementPreview() {
            let value = parseInt(avancementInput.value) || 0;

            // Limiter entre 0 et 100
            if (value < 0) value = 0;
            if (value > 100) value = 100;

            avancementInput.value = value;

            // Mettre à jour la barre de progression
            const progressBar = avancementPreview.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = value + '%';

                // Changer la couleur selon le niveau
                progressBar.className = 'progress-bar';
                if (value === 100) {
                    progressBar.classList.add('bg-success');
                } else if (value >= 50) {
                    progressBar.classList.add('bg-info');
                } else {
                    progressBar.classList.add('bg-warning');
                }

                if (avancementText) {
                    avancementText.textContent = value + '%';
                }
            }
        }

        avancementInput.addEventListener('input', updateAvancementPreview);

        // Mise à jour initiale
        updateAvancementPreview();
    }

    // ==================== STATUT AUTO-AVANCEMENT ====================
    /**
     * Suggestion d'avancement basé sur le statut
     */
    function initStatutAutoAvancement() {
        const statutSelect = document.getElementById('id_statut');
        const avancementInput = document.getElementById('id_avancement');

        if (!statutSelect || !avancementInput) return;

        statutSelect.addEventListener('change', function() {
            const currentAvancement = parseInt(avancementInput.value) || 0;
            const statut = this.value;

            let suggestedAvancement = currentAvancement;
            let shouldSuggest = false;

            // Suggestions d'avancement selon le statut
            switch(statut) {
                case 'A_FAIRE':
                    if (currentAvancement > 0) {
                        suggestedAvancement = 0;
                        shouldSuggest = true;
                    }
                    break;
                case 'EN_COURS':
                    if (currentAvancement === 0) {
                        suggestedAvancement = 25;
                        shouldSuggest = true;
                    }
                    break;
                case 'TERMINE':
                    if (currentAvancement < 100) {
                        suggestedAvancement = 100;
                        shouldSuggest = true;
                    }
                    break;
            }

            if (shouldSuggest) {
                const message = `Le statut "${this.options[this.selectedIndex].text}" suggère un avancement de ${suggestedAvancement}%. Voulez-vous l'appliquer ?`;
                if (confirm(message)) {
                    avancementInput.value = suggestedAvancement;
                    avancementInput.dispatchEvent(new Event('input'));
                }
            }
        });
    }

    // ==================== VALIDATION DATES ====================
    /**
     * Validation des dates de la tâche
     */
    function initDateValidation() {
        const dateDebutPrevue = document.getElementById('id_date_debut_prevue');
        const dateFinPrevue = document.getElementById('id_date_fin_prevue');

        // Validation date fin prévue
        if (dateFinPrevue && dateDebutPrevue) {
            dateFinPrevue.addEventListener('change', function() {
                if (dateDebutPrevue.value && this.value) {
                    if (new Date(this.value) < new Date(dateDebutPrevue.value)) {
                        markFieldInvalid(this, 'La date de fin doit être postérieure à la date de début');
                    } else {
                        this.classList.remove('is-invalid');
                        const errorDiv = this.parentNode.querySelector('.text-danger');
                        if (errorDiv) errorDiv.remove();
                    }
                }
            });
        }
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

})();


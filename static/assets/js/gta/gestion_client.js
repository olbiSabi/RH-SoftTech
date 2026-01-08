// static/assets/js/gta/gestion_client.js

/**
 * ============================================
 * GESTION DES CLIENTS - SCRIPTS
 * ============================================
 */

(function() {
    'use strict';

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initClientManagement();
    });

    /**
     * Initialisation principale
     */
    function initClientManagement() {
        // Conversion automatique en majuscules pour le code client
        initCodeClientUppercase();

        // Validation du formulaire
        initFormValidation();

        // Confirmation de suppression
        initDeleteConfirmation();

        // Filtres et recherche
        initFilters();

        // Tooltips Bootstrap
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();

        // Animations d'entrée
        animateElements();

        // Validation email en temps réel
        initEmailValidation();

        // Validation téléphone
        initPhoneValidation();

        // Compteur de caractères pour les notes
        initCharacterCounter();
    }

    // ==================== CONVERSION MAJUSCULES ====================
    /**
     * Convertit automatiquement le code client en majuscules
     */
    function initCodeClientUppercase() {
        const codeClientInput = document.getElementById('id_code_client');
        if (codeClientInput) {
            codeClientInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase().trim();
            });

            // Appliquer aussi au chargement si valeur existante
            if (codeClientInput.value) {
                codeClientInput.value = codeClientInput.value.toUpperCase();
            }
        }
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire client
     */
    function initFormValidation() {
        const form = document.querySelector('form');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    showFieldError(field, 'Ce champ est obligatoire');
                } else {
                    field.classList.remove('is-invalid');
                    hideFieldError(field);
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Veuillez remplir tous les champs obligatoires', 'error');
                // Scroll vers le premier champ invalide
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
        });

        // Retirer l'erreur quand l'utilisateur commence à taper
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    this.classList.remove('is-invalid');
                    hideFieldError(this);
                }
            });
        });
    }

    /**
     * Affiche une erreur sur un champ
     */
    function showFieldError(field, message) {
        // Supprimer l'erreur existante si présente
        hideFieldError(field);

        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-danger small field-error';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Cache l'erreur d'un champ
     */
    function hideFieldError(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    // ==================== VALIDATION EMAIL ====================
    /**
     * Validation email en temps réel
     */
    function initEmailValidation() {
        const emailInput = document.getElementById('id_email');
        if (!emailInput) return;

        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            if (email && !isValidEmail(email)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Format d\'email invalide');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }

    /**
     * Vérifie si un email est valide
     */
    function isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    // ==================== VALIDATION TÉLÉPHONE ====================
    /**
     * Validation téléphone
     */
    function initPhoneValidation() {
        const phoneInput = document.getElementById('id_telephone');
        if (!phoneInput) return;

        phoneInput.addEventListener('input', function() {
            // Autoriser uniquement chiffres, espaces, +, -, (, )
            this.value = this.value.replace(/[^0-9\s\+\-\(\)]/g, '');
        });

        phoneInput.addEventListener('blur', function() {
            const phone = this.value.trim();
            if (phone && phone.length < 8) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Numéro de téléphone trop court');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }

    // ==================== CONFIRMATION SUPPRESSION ====================
    /**
     * Confirmation avant suppression
     */
    function initDeleteConfirmation() {
        const deleteButton = document.querySelector('button[type="submit"].btn-danger');
        if (!deleteButton) return;

        deleteButton.addEventListener('click', function(e) {
            // Double confirmation si le client a des projets
            const projetsCount = this.dataset.projetsCount;
            if (projetsCount && parseInt(projetsCount) > 0) {
                const confirmMessage = `Ce client a ${projetsCount} projet(s). Êtes-vous ABSOLUMENT SÛR de vouloir supprimer ?`;
                if (!confirm(confirmMessage)) {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }

    // ==================== FILTRES ET RECHERCHE ====================
    /**
     * Gestion des filtres
     */
    function initFilters() {
    // Vérifier si on est sur la page liste des clients
    // en cherchant le formulaire de filtres spécifique
    const searchInput = document.querySelector('input[name="search"]');

    // Si on a un champ de recherche, on est probablement sur la page liste
    // Mais vérifions aussi qu'on n'est pas sur un formulaire de création/modification
    if (searchInput) {
        // Vérifier si on est dans un formulaire de filtres (GET) et non un formulaire de création/modification (POST)
        const searchForm = searchInput.closest('form');

        if (searchForm && searchForm.method === 'get') {
            // On est sur la page liste des clients avec filtres
            const filterSelects = searchForm.querySelectorAll('select[name="type_client"], select[name="actif"]');

            // Auto-submit après sélection d'un filtre
            filterSelects.forEach(function(select) {
                select.addEventListener('change', function() {
                    searchForm.submit();
                });
            });

            // Focus sur le champ de recherche avec Ctrl+F
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'f' && searchInput) {
                    e.preventDefault();
                    searchInput.focus();
                    searchInput.select();
                }
            });
        }
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
            }, 10000);
        });
    }

    // ==================== ANIMATIONS ====================
    /**
     * Ajoute des animations d'entrée
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

    // ==================== COMPTEUR DE CARACTÈRES ====================
    /**
     * Compteur de caractères pour le champ notes
     */
    function initCharacterCounter() {
        const notesTextarea = document.getElementById('id_notes');
        if (!notesTextarea) return;

        const maxLength = 500;
        const counter = document.createElement('small');
        counter.className = 'text-muted float-right';
        notesTextarea.parentNode.appendChild(counter);

        function updateCounter() {
            const remaining = maxLength - notesTextarea.value.length;
            counter.textContent = `${notesTextarea.value.length} / ${maxLength} caractères`;

            if (remaining < 50) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
        }

        notesTextarea.addEventListener('input', updateCounter);
        updateCounter(); // Initialiser
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

            // Auto-dismiss après 5 secondes
            setTimeout(function() {
                alertDiv.remove();
            }, 5000);
        }
    }

    // ==================== UTILITAIRES ====================
    /**
     * Confirmation générique
     */
    window.confirmAction = function(message) {
        return confirm(message);
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

    /**
     * Imprimer la page
     */
    window.printPage = function() {
        window.print();
    };

})();

 // Empêcher la re-soumission du formulaire lors de l'actualisation
        if (window.history.replaceState) {
            window.history.replaceState(null, null, window.location.href);
        }
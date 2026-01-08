// static/assets/js/gta/gestion_activite.js

/**
 * ============================================
 * GESTION DES ACTIVITÉS - SCRIPTS
 * ============================================ */

(function() {
    'use strict';

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initActiviteManagement();
    });

    /**
     * Initialisation principale
     */
    function initActiviteManagement() {
        // Conversion automatique en majuscules pour le code activité
        initCodeActiviteUppercase();

        // Validation du formulaire
        initFormValidation();

        // Gestion de la facturation
        initFacturationToggle();

        // Validation des dates
        initDateValidation();

        // Aperçu du statut en temps réel
        initStatusPreview();

        // Confirmation de suppression
        initDeleteConfirmation();

        // Filtres
        initFilters();

        // Tooltips
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();

        // Animations
        animateElements();

        // Validation taux horaire
        initTauxHoraireValidation();
    }

    // ==================== CODE ACTIVITÉ MAJUSCULES ====================
    /**
     * Convertit automatiquement le code activité en majuscules
     */
    function initCodeActiviteUppercase() {
        const codeActiviteInput = document.getElementById('id_code_activite');
        if (codeActiviteInput) {
            codeActiviteInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase().trim().replace(/\s+/g, '_');
            });

            // Appliquer au chargement
            if (codeActiviteInput.value) {
                codeActiviteInput.value = codeActiviteInput.value.toUpperCase();
            }
        }
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire activité
     */
    function initFormValidation() {
        const form = document.getElementById('activiteForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            // Validation code activité
            const codeActivite = document.getElementById('id_code_activite');
            if (codeActivite && !codeActivite.value.trim()) {
                isValid = false;
                markFieldInvalid(codeActivite, 'Le code activité est obligatoire');
                errors.push('Code activité manquant');
            } else if (codeActivite && codeActivite.value.length < 2) {
                isValid = false;
                markFieldInvalid(codeActivite, 'Le code doit contenir au moins 2 caractères');
                errors.push('Code activité trop court');
            }

            // Validation libellé
            const libelle = document.getElementById('id_libelle');
            if (libelle && !libelle.value.trim()) {
                isValid = false;
                markFieldInvalid(libelle, 'Le libellé est obligatoire');
                errors.push('Libellé manquant');
            }

            // Validation date de début
            const dateDebut = document.getElementById('id_date_debut');
            if (dateDebut && !dateDebut.value) {
                isValid = false;
                markFieldInvalid(dateDebut, 'La date de début est obligatoire');
                errors.push('Date de début manquante');
            }

            // Validation dates (fin après début)
            const dateFin = document.getElementById('id_date_fin');
            if (dateDebut && dateFin && dateDebut.value && dateFin.value) {
                if (new Date(dateFin.value) < new Date(dateDebut.value)) {
                    isValid = false;
                    markFieldInvalid(dateFin, 'La date de fin doit être après la date de début');
                    errors.push('Dates incohérentes');
                }
            }

            // Validation taux horaire si facturable
            const facturable = document.getElementById('id_facturable');
            const tauxHoraire = document.getElementById('id_taux_horaire_defaut');
            if (facturable && facturable.checked && tauxHoraire && !tauxHoraire.value) {
                const confirmProceed = confirm(
                    'Cette activité est facturable mais aucun taux horaire n\'est défini.\n\n' +
                    'Voulez-vous continuer sans définir de taux horaire ?'
                );
                if (!confirmProceed) {
                    isValid = false;
                    markFieldInvalid(tauxHoraire, 'Définissez un taux horaire ou décochez "Facturable"');
                    errors.push('Taux horaire manquant pour activité facturable');
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

    // ==================== GESTION FACTURATION ====================
    /**
     * Gestion du toggle facturable
     */
    function initFacturationToggle() {
        const facturableCheckbox = document.getElementById('id_facturable');
        const tauxHoraireGroup = document.getElementById('id_taux_horaire_defaut');

        if (!facturableCheckbox || !tauxHoraireGroup) return;

        function updateTauxHoraireState() {
            if (facturableCheckbox.checked) {
                tauxHoraireGroup.parentElement.classList.add('bg-light', 'border', 'p-2', 'rounded');
                tauxHoraireGroup.focus();
            } else {
                tauxHoraireGroup.parentElement.classList.remove('bg-light', 'border', 'p-2', 'rounded');
            }
        }

        facturableCheckbox.addEventListener('change', updateTauxHoraireState);

        // Appliquer l'état initial
        updateTauxHoraireState();
    }

    // ==================== VALIDATION DATES ====================
    /**
     * Validation des dates de validité
     */
    function initDateValidation() {
        const dateDebut = document.getElementById('id_date_debut');
        const dateFin = document.getElementById('id_date_fin');

        if (!dateDebut) return;

        // Validation date fin
        if (dateFin) {
            dateFin.addEventListener('change', function() {
                if (dateDebut.value && this.value) {
                    if (new Date(this.value) < new Date(dateDebut.value)) {
                        markFieldInvalid(this, 'La date de fin doit être postérieure à la date de début');
                        showNotification('La date de fin doit être après la date de début', 'error');
                    } else {
                        this.classList.remove('is-invalid');
                        const errorDiv = this.parentNode.querySelector('.text-danger');
                        if (errorDiv) errorDiv.remove();

                        // Calculer la durée
                        const debut = new Date(dateDebut.value);
                        const fin = new Date(this.value);
                        const diffTime = Math.abs(fin - debut);
                        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                        let durationText = '';
                        if (diffDays > 365) {
                            const years = Math.floor(diffDays / 365);
                            durationText = `Durée de validité: ${years} an(s)`;
                        } else if (diffDays > 30) {
                            const months = Math.floor(diffDays / 30);
                            durationText = `Durée de validité: ${months} mois`;
                        } else {
                            durationText = `Durée de validité: ${diffDays} jour(s)`;
                        }

                        showNotification(durationText, 'info');
                    }
                }
            });
        }

        // Avertissement si date de début dans le passé
        dateDebut.addEventListener('change', function() {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selectedDate = new Date(this.value);

            if (selectedDate < today) {
                showNotification(
                    'Attention : La date de début est dans le passé. L\'activité sera immédiatement disponible.',
                    'warning'
                );
            }
        });
    }

    // ==================== APERÇU DU STATUT ====================
    /**
     * Aperçu en temps réel du statut de l'activité
     */
    function initStatusPreview() {
        const dateDebut = document.getElementById('id_date_debut');
        const dateFin = document.getElementById('id_date_fin');
        const actifCheckbox = document.getElementById('id_actif');
        const statusPreview = document.getElementById('status-preview');
        const statusPreviewContent = document.getElementById('status-preview-content');

        if (!dateDebut || !statusPreview || !statusPreviewContent) return;

        function updateStatusPreview() {
            if (!dateDebut.value) {
                statusPreview.style.display = 'none';
                return;
            }

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const debut = new Date(dateDebut.value);
            const fin = dateFin && dateFin.value ? new Date(dateFin.value) : null;
            const isActif = actifCheckbox ? actifCheckbox.checked : true;

            let statusHTML = '';
            let statusClass = '';
            let statusText = '';
            let statusIcon = '';

            // Déterminer le statut
            if (!isActif) {
                statusClass = 'status-inactif';
                statusText = 'Inactif (manuel)';
                statusIcon = 'fas fa-ban';
            } else if (debut > today) {
                statusClass = 'status-a-venir';
                statusText = 'À venir';
                statusIcon = 'fas fa-calendar-plus';
            } else if (fin && fin < today) {
                statusClass = 'status-expire';
                statusText = 'Expiré';
                statusIcon = 'fas fa-calendar-times';
            } else if (fin && debut <= today && fin >= today) {
                statusClass = 'status-actif-limite';
                statusText = `Actif (jusqu'au ${fin.toLocaleDateString('fr-FR')})`;
                statusIcon = 'fas fa-clock';
            } else {
                statusClass = 'status-actif';
                statusText = 'Actif';
                statusIcon = 'fas fa-check-circle';
            }

            statusHTML = `
                <div class="d-flex align-items-center">
                    <span class="badge ${statusClass} status-preview-badge">
                        <i class="${statusIcon}"></i> ${statusText}
                    </span>
                </div>
                <div class="status-preview-details mt-2">
                    <small>
                        <i class="fas fa-calendar-alt"></i>
                        Début: ${debut.toLocaleDateString('fr-FR')}
                        ${fin ? ` | Fin: ${fin.toLocaleDateString('fr-FR')}` : ' | Fin: Illimitée'}
                    </small>
                </div>
            `;

            if (!isActif) {
                statusHTML += `
                    <div class="alert alert-warning mt-2 mb-0">
                        <small>
                            <i class="fas fa-exclamation-triangle"></i>
                            Cette activité est désactivée manuellement et ne pourra pas être utilisée.
                        </small>
                    </div>
                `;
            }

            statusPreviewContent.innerHTML = statusHTML;
            statusPreview.style.display = 'block';
        }

        // Écouter les changements
        if (dateDebut) dateDebut.addEventListener('change', updateStatusPreview);
        if (dateFin) dateFin.addEventListener('change', updateStatusPreview);
        if (actifCheckbox) actifCheckbox.addEventListener('change', updateStatusPreview);

        // Mise à jour initiale
        if (dateDebut.value) {
            updateStatusPreview();
        }
    }

    // ==================== VALIDATION TAUX HORAIRE ====================
    /**
     * Validation du taux horaire
     */
    function initTauxHoraireValidation() {
    const tauxHoraireInput = document.getElementById('id_taux_horaire_defaut');
    if (!tauxHoraireInput) return;

    tauxHoraireInput.addEventListener('input', function() {
        // Supprimer les caractères non numériques sauf le point et la virgule
        this.value = this.value.replace(/[^0-9.,]/g, '');

        // Remplacer la virgule par un point
        this.value = this.value.replace(',', '.');

        // Vérifier que la valeur est positive
        const value = parseFloat(this.value);
        if (!isNaN(value) && value < 0) {
            markFieldInvalid(this, 'Le taux horaire doit être positif');
        } else if (!isNaN(value) && value > 0) {
            this.classList.remove('is-invalid');
            const errorDiv = this.parentNode.querySelector('.text-danger');
            if (errorDiv) errorDiv.remove();
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
            const imputationsCount = this.dataset.imputationsCount;

            if (imputationsCount && parseInt(imputationsCount) > 0) {
                e.preventDefault();

                const confirmMessage =
                    `ATTENTION !\n\n` +
                    `Cette activité a été utilisée dans ${imputationsCount} imputation(s) de temps.\n\n` +
                    `Nous vous recommandons de désactiver l'activité plutôt que de la supprimer.\n\n` +
                    `Êtes-vous sûr de vouloir continuer ?`;

                if (confirm(confirmMessage)) {
                    // Seconde confirmation
                    const doubleConfirm = confirm(
                        'Dernière confirmation :\n\n' +
                        'La suppression peut affecter l\'intégrité des données historiques.\n\n' +
                        'Voulez-vous vraiment supprimer cette activité ?'
                    );
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
        const searchInput = document.querySelector('input[name="search"]');
        const filterSelects = document.querySelectorAll('select[name="facturable"], select[name="actif"]');

        // Auto-submit après sélection
        filterSelects.forEach(function(select) {
            select.addEventListener('change', function() {
                this.form.submit();
            });
        });

        // Focus sur recherche avec Ctrl+F
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
                card.style.transition = 'all 0.3s ease';
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
     * Copier dans le presse-papier
     */
    window.copyCodeActivite = function(code) {
        navigator.clipboard.writeText(code).then(function() {
            showNotification(`Code "${code}" copié dans le presse-papier`, 'success');
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
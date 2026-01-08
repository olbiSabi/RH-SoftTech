// static/assets/js/gta/gestion_document.js

/**
 * ============================================
 * GESTION DES DOCUMENTS - SCRIPTS
 * ============================================ */

(function() {
    'use strict';

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        initDocumentManagement();
    });

    /**
     * Initialisation principale
     */
    function initDocumentManagement() {
        // Gestion du type de rattachement
        initRattachementToggle();

        // Aperçu du fichier
        initFilePreview();

        // Validation du formulaire
        initFormValidation();

        // Barre de progression d'upload
        initUploadProgress();

        // Nom du fichier dans le label
        initFileInputLabel();

        // Drag & Drop (optionnel)
        initDragAndDrop();

        // Tooltips
        initTooltips();

        // Auto-dismiss des messages
        autoDismissAlerts();
    }

    // ==================== TOGGLE RATTACHEMENT ====================
    /**
     * Affiche/masque les sections selon le type de rattachement
     */
    function initRattachementToggle() {
        const typeRattachement = document.getElementById('id_type_rattachement');
        const projetSection = document.getElementById('projet-section');
        const tacheSection = document.getElementById('tache-section');
        const projetSelect = document.getElementById('id_projet');
        const tacheSelect = document.getElementById('id_tache');

        if (!typeRattachement) return;

        function updateRattachement() {
            const type = typeRattachement.value;

            if (type === 'PROJET') {
                projetSection.style.display = 'block';
                tacheSection.style.display = 'none';
                if (projetSelect) projetSelect.required = true;
                if (tacheSelect) {
                    tacheSelect.required = false;
                    tacheSelect.value = '';
                }
            } else if (type === 'TACHE') {
                projetSection.style.display = 'none';
                tacheSection.style.display = 'block';
                if (tacheSelect) tacheSelect.required = true;
                if (projetSelect) {
                    projetSelect.required = false;
                    projetSelect.value = '';
                }
            } else {
                projetSection.style.display = 'none';
                tacheSection.style.display = 'none';
                if (projetSelect) projetSelect.required = false;
                if (tacheSelect) tacheSelect.required = false;
            }
        }

        typeRattachement.addEventListener('change', updateRattachement);

        // Mise à jour initiale
        updateRattachement();
    }

    // ==================== APERÇU FICHIER ====================
    /**
     * Affiche un aperçu du fichier sélectionné
     */
    function initFilePreview() {
        const fileInput = document.getElementById('id_fichier');
        const filePreview = document.getElementById('file-preview');
        const filePreviewContent = document.getElementById('file-preview-content');

        if (!fileInput || !filePreview || !filePreviewContent) return;

        fileInput.addEventListener('change', function() {
            const file = this.files[0];

            if (file) {
                const fileName = file.name;
                const fileSize = formatFileSize(file.size);
                const fileType = file.type;
                const fileExtension = fileName.split('.').pop().toLowerCase();

                // Icône selon le type de fichier
                let iconClass = 'fas fa-file';
                let iconColor = '#858796';

                if (fileExtension === 'pdf') {
                    iconClass = 'fas fa-file-pdf';
                    iconColor = '#e74a3b';
                } else if (['doc', 'docx'].includes(fileExtension)) {
                    iconClass = 'fas fa-file-word';
                    iconColor = '#2e59d9';
                } else if (['xls', 'xlsx'].includes(fileExtension)) {
                    iconClass = 'fas fa-file-excel';
                    iconColor = '#1cc88a';
                } else if (['ppt', 'pptx'].includes(fileExtension)) {
                    iconClass = 'fas fa-file-powerpoint';
                    iconColor = '#f6c23e';
                } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
                    iconClass = 'fas fa-file-image';
                    iconColor = '#36b9cc';
                }

                // Couleur selon la taille
                let sizeClass = 'file-size-small';
                if (file.size > 5 * 1024 * 1024) {
                    sizeClass = 'file-size-large';
                } else if (file.size > 1 * 1024 * 1024) {
                    sizeClass = 'file-size-medium';
                }

                // Créer l'aperçu
                let previewHTML = `
                    <div class="file-preview-item">
                        <div class="file-preview-icon">
                            <i class="${iconClass}" style="color: ${iconColor};"></i>
                        </div>
                        <div class="file-preview-details">
                            <div class="file-preview-name">${fileName}</div>
                            <div class="file-preview-info">
                                Type: ${fileExtension.toUpperCase()} |
                                Taille: <span class="${sizeClass}">${fileSize}</span>
                            </div>
                        </div>
                    </div>
                `;

                // Aperçu d'image si applicable
                if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewHTML += `
                            <div class="mt-3 text-center">
                                <img src="${e.target.result}"
                                     alt="Aperçu"
                                     style="max-width: 100%; max-height: 200px;"
                                     class="img-thumbnail">
                            </div>
                        `;
                        filePreviewContent.innerHTML = previewHTML;
                    };
                    reader.readAsDataURL(file);
                } else {
                    filePreviewContent.innerHTML = previewHTML;
                }

                filePreview.style.display = 'block';

                // Validation de la taille
                if (file.size > 10 * 1024 * 1024) {
                    showNotification('Attention : Le fichier dépasse 10 MB', 'warning');
                }
            } else {
                filePreview.style.display = 'none';
            }
        });
    }

    // ==================== LABEL FICHIER ====================
    /**
     * Met à jour le label avec le nom du fichier
     */
    function initFileInputLabel() {
        const fileInput = document.getElementById('id_fichier');
        const fileLabel = document.getElementById('file-label');

        if (!fileInput || !fileLabel) return;

        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Choisir un fichier...';
            fileLabel.textContent = fileName;
        });
    }

    // ==================== VALIDATION FORMULAIRE ====================
    /**
     * Validation du formulaire document
     */
    function initFormValidation() {
        const form = document.getElementById('documentForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = [];

            // Validation nom document
            const nomDocument = document.getElementById('id_nom_document');
            if (nomDocument && !nomDocument.value.trim()) {
                isValid = false;
                markFieldInvalid(nomDocument, 'Le nom du document est obligatoire');
                errors.push('Nom du document manquant');
            }

            // Validation fichier
            const fichier = document.getElementById('id_fichier');
            if (fichier && !fichier.files.length) {
                isValid = false;
                markFieldInvalid(fichier.parentElement, 'Veuillez sélectionner un fichier');
                errors.push('Fichier manquant');
            }

            // Validation type rattachement
            const typeRattachement = document.getElementById('id_type_rattachement');
            if (typeRattachement && !typeRattachement.value) {
                isValid = false;
                markFieldInvalid(typeRattachement, 'Veuillez sélectionner un type de rattachement');
                errors.push('Type de rattachement manquant');
            }

            // Validation projet ou tâche
            const projet = document.getElementById('id_projet');
            const tache = document.getElementById('id_tache');

            if (typeRattachement && typeRattachement.value === 'PROJET' && projet && !projet.value) {
                isValid = false;
                markFieldInvalid(projet, 'Veuillez sélectionner un projet');
                errors.push('Projet manquant');
            }

            if (typeRattachement && typeRattachement.value === 'TACHE' && tache && !tache.value) {
                isValid = false;
                markFieldInvalid(tache, 'Veuillez sélectionner une tâche');
                errors.push('Tâche manquante');
            }

            if (!isValid) {
                e.preventDefault();
                showNotification('Veuillez corriger les erreurs : ' + errors.join(', '), 'error');

                // Scroll vers le premier champ invalide
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

    // ==================== BARRE DE PROGRESSION ====================
    /**
     * Simulation de barre de progression d'upload
     */
    function initUploadProgress() {
        const form = document.getElementById('documentForm');
        const submitBtn = document.getElementById('submit-btn');
        const uploadProgress = document.getElementById('upload-progress');
        const progressBar = document.getElementById('progress-bar');

        if (!form || !submitBtn || !uploadProgress || !progressBar) return;

        form.addEventListener('submit', function(e) {
            const fichier = document.getElementById('id_fichier');

            if (fichier && fichier.files.length > 0) {
                // Désactiver le bouton
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Upload en cours...';

                // Afficher la barre de progression
                uploadProgress.style.display = 'block';

                // Simuler la progression (en production, utiliser XMLHttpRequest pour vraie progression)
                let progress = 0;
                const interval = setInterval(function() {
                    progress += Math.random() * 15;
                    if (progress > 95) progress = 95;

                    progressBar.style.width = progress + '%';
                    progressBar.textContent = Math.round(progress) + '%';
                }, 200);

                // Nettoyer l'intervalle après 30 secondes (timeout)
                setTimeout(function() {
                    clearInterval(interval);
                }, 30000);
            }
        });
    }

    // ==================== DRAG & DROP ====================
    /**
     * Gestion du drag & drop de fichiers
     */
    function initDragAndDrop() {
        const fileInput = document.getElementById('id_fichier');
        const dropZone = document.querySelector('.custom-file');

        if (!fileInput || !dropZone) return;

        // Prévenir le comportement par défaut
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Highlight lors du drag over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.remove('dragover');
            }, false);
        });

        // Gestion du drop
        dropZone.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;

                // Déclencher l'événement change
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }, false);
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

    // ==================== UTILITAIRES ====================
    /**
     * Formate la taille de fichier
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

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


 // Empêcher la re-soumission du formulaire lors de l'actualisation
        if (window.history.replaceState) {
            window.history.replaceState(null, null, window.location.href);
        }
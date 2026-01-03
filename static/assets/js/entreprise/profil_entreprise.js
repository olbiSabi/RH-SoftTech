/**
 * ========================================
 * PROFIL ENTREPRISE - JAVASCRIPT
 * ========================================
 */

// ============================================
// GESTION DES MODALS
// ============================================

/**
 * Ouvre le modal de création
 */
function openCreateModal() {
    document.getElementById('modalTitle').textContent = "Créer le Profil de l'Entreprise";
    document.getElementById('entrepriseUuid').value = '';

    // Réinitialiser tous les champs
    document.getElementById('code').value = '';
    document.getElementById('nom').value = '';
    document.getElementById('sigle').value = '';
    document.getElementById('raison_sociale').value = '';
    document.getElementById('adresse').value = '';
    document.getElementById('ville').value = '';
    document.getElementById('pays').value = 'TOGO';
    document.getElementById('telephone').value = '';
    document.getElementById('email').value = '';
    document.getElementById('site_web').value = '';
    document.getElementById('rccm').value = '';
    document.getElementById('numero_impot').value = '';
    document.getElementById('numero_cnss').value = '';
    document.getElementById('configuration_conventionnelle').value = '';
    document.getElementById('date_creation').value = '';
    document.getElementById('date_application_convention').value = '';
    document.getElementById('logo').value = '';
    document.getElementById('description').value = '';
    document.getElementById('actif').checked = true;

    // Retourner au premier onglet
    const firstTab = new bootstrap.Tab(document.getElementById('general-tab'));
    firstTab.show();

    clearFormErrors();

    const modal = new bootstrap.Modal(document.getElementById('entrepriseModal'));
    modal.show();
}

/**
 * Ouvre le modal d'édition
 */
function openEditModal(uuid) {
    document.getElementById('modalTitle').textContent = "Modifier le Profil de l'Entreprise";
    clearFormErrors();
    loadEntrepriseData(uuid);

    const modal = new bootstrap.Modal(document.getElementById('entrepriseModal'));
    modal.show();
}

// ============================================
// CHARGEMENT DES DONNÉES
// ============================================

/**
 * Charge les données d'une entreprise
 */
function loadEntrepriseData(uuid) {
    fetch(`/entreprise/api/entreprise/${uuid}/`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                populateForm(result.data);
            } else {
                showErrorMessage('Erreur lors du chargement des données');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showErrorMessage('Erreur lors du chargement des données');
        });
}

/**
 * Remplit le formulaire avec les données
 */
function populateForm(data) {
    document.getElementById('entrepriseUuid').value = data.uuid;
    document.getElementById('code').value = data.code;
    document.getElementById('nom').value = data.nom;
    document.getElementById('sigle').value = data.sigle;
    document.getElementById('raison_sociale').value = data.raison_sociale;
    document.getElementById('adresse').value = data.adresse;
    document.getElementById('ville').value = data.ville;
    document.getElementById('pays').value = data.pays;
    document.getElementById('telephone').value = data.telephone;
    document.getElementById('email').value = data.email;
    document.getElementById('site_web').value = data.site_web;
    document.getElementById('rccm').value = data.rccm;
    document.getElementById('numero_impot').value = data.numero_impot;
    document.getElementById('numero_cnss').value = data.numero_cnss;
    document.getElementById('configuration_conventionnelle').value = data.configuration_conventionnelle || '';
    document.getElementById('date_creation').value = data.date_creation;
    document.getElementById('date_application_convention').value = data.date_application_convention;
    document.getElementById('description').value = data.description;
    document.getElementById('actif').checked = data.actif;
}

// ============================================
// SAUVEGARDE
// ============================================

/**
 * Sauvegarde une entreprise (création ou modification)
 */
function saveEntreprise() {
    clearFormErrors();

    const uuid = document.getElementById('entrepriseUuid').value;
    const isEdit = uuid !== '';

    const url = isEdit
        ? `/entreprise/api/entreprise/${uuid}/update/`
        : '/entreprise/api/entreprise/create/';

    const formData = new FormData();
    formData.append('code', document.getElementById('code').value.trim().toUpperCase());
    formData.append('nom', document.getElementById('nom').value.trim());
    formData.append('sigle', document.getElementById('sigle').value.trim().toUpperCase());
    formData.append('raison_sociale', document.getElementById('raison_sociale').value.trim());
    formData.append('adresse', document.getElementById('adresse').value.trim());
    formData.append('ville', document.getElementById('ville').value.trim());
    formData.append('pays', document.getElementById('pays').value.trim().toUpperCase());
    formData.append('telephone', document.getElementById('telephone').value.trim());
    formData.append('email', document.getElementById('email').value.trim());
    formData.append('site_web', document.getElementById('site_web').value.trim());
    formData.append('rccm', document.getElementById('rccm').value.trim());
    formData.append('numero_impot', document.getElementById('numero_impot').value.trim());
    formData.append('numero_cnss', document.getElementById('numero_cnss').value.trim());

    const convention = document.getElementById('configuration_conventionnelle').value;
    if (convention) {
        formData.append('configuration_conventionnelle', convention);
    }

    const dateCreation = document.getElementById('date_creation').value;
    if (dateCreation) {
        formData.append('date_creation', dateCreation);
    }

    const dateApplication = document.getElementById('date_application_convention').value;
    if (dateApplication) {
        formData.append('date_application_convention', dateApplication);
    }

    formData.append('description', document.getElementById('description').value.trim());

    if (document.getElementById('actif').checked) {
        formData.append('actif', 'on');
    }

    // Logo (fichier)
    const logoFile = document.getElementById('logo').files[0];
    if (logoFile) {
        formData.append('logo', logoFile);
    }

    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const modalElement = document.getElementById('entrepriseModal');
            document.activeElement.blur();
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();

            showSuccessMessage(result.message);

            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            if (result.errors) {
                displayFormErrors(result.errors);
            } else {
                showErrorMessage(result.error || 'Une erreur est survenue');
            }
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showErrorMessage('Erreur lors de la sauvegarde');
    });
}

// ============================================
// SUPPRESSION
// ============================================

/**
 * Supprime une entreprise
 */
function deleteEntreprise(uuid, nom) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Confirmer la suppression',
            html: `Êtes-vous sûr de vouloir supprimer le profil de l'entreprise <strong>"${nom}"</strong> ?<br><br>
                   <span class="text-danger">⚠️ Cette action est irréversible et supprimera toutes les données de l'entreprise.</span>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="fas fa-trash"></i> Oui, supprimer',
            cancelButtonText: '<i class="fas fa-times"></i> Annuler',
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                executeDelete(uuid);
            }
        });
    } else {
        if (confirm(`Êtes-vous sûr de vouloir supprimer le profil de l'entreprise "${nom}" ?\n\nCette action est irréversible.`)) {
            executeDelete(uuid);
        }
    }
}

/**
 * Exécute la suppression
 */
function executeDelete(uuid) {
    fetch(`/entreprise/api/entreprise/${uuid}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            document.activeElement.blur();
            showSuccessMessage(result.message);
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showErrorMessage(result.error || 'Erreur lors de la suppression');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showErrorMessage('Erreur lors de la suppression');
    });
}

// ============================================
// GESTION DES ERREURS
// ============================================

/**
 * Affiche les erreurs du formulaire
 */
function displayFormErrors(errors) {
    if (errors.__all__) {
        showErrorMessage(errors.__all__);
        return;
    }

    for (const [field, message] of Object.entries(errors)) {
        const input = document.getElementById(field);
        if (input) {
            input.classList.add('is-invalid');
            const feedback = input.parentElement.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.textContent = message;
            }
        }
    }
}

/**
 * Efface les erreurs du formulaire
 */
function clearFormErrors() {
    document.querySelectorAll('.is-invalid').forEach(element => {
        element.classList.remove('is-invalid');
    });
    document.querySelectorAll('.invalid-feedback').forEach(element => {
        element.textContent = '';
    });
}

// ============================================
// MESSAGES
// ============================================

/**
 * Affiche un message de succès
 */
function showSuccessMessage(message) {
    if (typeof toastr !== 'undefined') {
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: "toast-top-right",
            timeOut: 3000
        };
        toastr.success(message);
    } else if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: 'Succès',
            text: message,
            timer: 2000,
            showConfirmButton: false
        });
    } else {
        showBootstrapAlert(message, 'success');
    }
}

/**
 * Affiche un message d'erreur
 */
function showErrorMessage(message) {
    if (typeof toastr !== 'undefined') {
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: "toast-top-right",
            timeOut: 5000
        };
        toastr.error(message);
    } else if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Erreur',
            text: message,
            confirmButtonText: 'OK'
        });
    } else {
        showBootstrapAlert(message, 'danger');
    }
}

/**
 * Affiche une alerte Bootstrap (fallback)
 */
function showBootstrapAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <strong>${type === 'success' ? '<i class="fas fa-check-circle"></i> Succès' : '<i class="fas fa-exclamation-circle"></i> Erreur'}</strong><br>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ============================================
// UTILITAIRES
// ============================================

/**
 * Récupère le token CSRF
 */
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

// ============================================
// ÉVÉNEMENTS
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('entrepriseModal');
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', function() {
            clearFormErrors();
            document.getElementById('entrepriseUuid').value = '';
        });
    }

    const form = document.getElementById('entrepriseForm');
    if (form) {
        form.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                saveEntreprise();
            }
        });
    }

    // Forcer les majuscules sur certains champs
    const codeInput = document.getElementById('code');
    if (codeInput) {
        codeInput.addEventListener('input', function(e) {
            this.value = this.value.toUpperCase();
        });
    }

    const sigleInput = document.getElementById('sigle');
    if (sigleInput) {
        sigleInput.addEventListener('input', function(e) {
            this.value = this.value.toUpperCase();
        });
    }

    const paysInput = document.getElementById('pays');
    if (paysInput) {
        paysInput.addEventListener('input', function(e) {
            this.value = this.value.toUpperCase();
        });
    }
});
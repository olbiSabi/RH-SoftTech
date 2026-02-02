/**
 * ========================================
 * TYPES D'ABSENCE - GESTION JAVASCRIPT
 * ========================================
 */

// ============================================
// GESTION DES MODALS
// ============================================

/**
 * Ouvre le modal de création
 */
function openCreateModal() {
    document.getElementById('modalTitle').textContent = "Nouveau Type d'Absence";
    document.getElementById('typeAbsenceId').value = '';

    document.getElementById('code').value = '';
    document.getElementById('libelle').value = '';
    document.getElementById('categorie').value = 'CONGES_PAYES';
    document.getElementById('couleur').value = '#3498db';
    document.getElementById('ordre').value = 0;
    document.getElementById('paye').checked = true;
    document.getElementById('decompte_solde').checked = true;
    document.getElementById('justificatif_obligatoire').checked = false;
    document.getElementById('actif').checked = true;

    clearFormErrors();

    // Ouvrir la modal avec jQuery (Bootstrap 4)
    $('#typeAbsenceModal').modal('show');
}

/**
 * Ouvre le modal d'édition
 */
function openEditModal(id) {
    document.getElementById('modalTitle').textContent = "Modifier le Type d'Absence";
    clearFormErrors();
    loadTypeAbsenceData(id);

    // Ouvrir la modal avec jQuery (Bootstrap 4)
    $('#typeAbsenceModal').modal('show');
}

// ============================================
// CHARGEMENT DES DONNÉES
// ============================================

/**
 * Charge les données d'un type d'absence
 */
function loadTypeAbsenceData(id) {
    fetch(`/absence/api/type-absence/${id}/`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                populateForm(result.data);
            } else {
                showErrorMessage('Erreur lors du chargement des données');
            }
        })
        .catch(error => {
            showErrorMessage('Erreur lors du chargement des données');
        });
}

/**
 * Remplit le formulaire avec les données
 */
function populateForm(data) {
    document.getElementById('typeAbsenceId').value = data.id;
    document.getElementById('code').value = data.code;
    document.getElementById('libelle').value = data.libelle;
    document.getElementById('categorie').value = data.categorie;
    document.getElementById('couleur').value = data.couleur;
    document.getElementById('ordre').value = data.ordre;
    document.getElementById('paye').checked = data.paye;
    document.getElementById('decompte_solde').checked = data.decompte_solde;
    document.getElementById('justificatif_obligatoire').checked = data.justificatif_obligatoire;
    document.getElementById('actif').checked = data.actif;
}

// ============================================
// SAUVEGARDE
// ============================================

/**
 * Sauvegarde un type d'absence (création ou modification)
 */
function saveTypeAbsence() {
    clearFormErrors();

    const categorieSelect = document.getElementById('categorie');
    let categorieValue = categorieSelect.value;

    if (!categorieValue || categorieValue === '') {
        if (categorieSelect.selectedIndex > 0) {
            categorieValue = categorieSelect.options[categorieSelect.selectedIndex].value;
        }
    }

    if (!categorieValue || categorieValue === '') {
        categorieValue = 'CONGES_PAYES';
    }

    const id = document.getElementById('typeAbsenceId').value;
    const isEdit = id !== '';

    const url = isEdit
        ? `/absence/api/type-absence/${id}/update/`
        : '/absence/api/type-absence/create/';

    const formData = new FormData();
    formData.append('code', document.getElementById('code').value.trim().toUpperCase());
    formData.append('libelle', document.getElementById('libelle').value.trim());
    formData.append('categorie', categorieValue);
    formData.append('couleur', document.getElementById('couleur').value);
    formData.append('ordre', document.getElementById('ordre').value);

    if (document.getElementById('paye').checked) {
        formData.append('paye', 'on');
    }
    if (document.getElementById('decompte_solde').checked) {
        formData.append('decompte_solde', 'on');
    }
    if (document.getElementById('justificatif_obligatoire').checked) {
        formData.append('justificatif_obligatoire', 'on');
    }
    if (document.getElementById('actif').checked) {
        formData.append('actif', 'on');
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
            // Fermer la modal avec jQuery (Bootstrap 4)
            $('#typeAbsenceModal').modal('hide');

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
        showErrorMessage('Erreur lors de la sauvegarde');
    });
}

// ============================================
// SUPPRESSION
// ============================================

/**
 * Supprime un type d'absence
 */
function deleteTypeAbsence(id, code) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Confirmer la suppression',
            html: `Êtes-vous sûr de vouloir supprimer le type d'absence <strong>"${code}"</strong> ?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="fas fa-trash"></i> Oui, supprimer',
            cancelButtonText: '<i class="fas fa-times"></i> Annuler',
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                executeDelete(id);
            }
        });
    } else {
        if (confirm(`Êtes-vous sûr de vouloir supprimer le type d'absence "${code}" ?`)) {
            executeDelete(id);
        }
    }
}

/**
 * Supprime un type d'absence sans confirmation (appelé par le modal)
 */
function deleteTypeAbsenceConfirmed(id) {
    executeDelete(id);
}

/**
 * Exécute la suppression
 */
function executeDelete(id) {
    fetch(`/absence/api/type-absence/${id}/delete/`, {
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
        showErrorMessage('Erreur lors de la suppression');
    });
}

// ============================================
// ACTIVATION/DÉSACTIVATION
// ============================================

/**
 * Active/Désactive un type d'absence
 */
function toggleTypeAbsence(id) {
    fetch(`/absence/api/type-absence/${id}/toggle/`, {
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
            showErrorMessage(result.error || 'Erreur lors de la modification');
        }
    })
    .catch(error => {
        showErrorMessage('Erreur lors de la modification');
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
        <button type="button" class="close" data-dismiss="alert">
            <span aria-hidden="true">&times;</span>
        </button>
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

$(document).ready(function() {
    const modalElement = document.getElementById('typeAbsenceModal');
    if (modalElement) {
        // Utiliser l'événement jQuery pour Bootstrap 4
        $(modalElement).on('hidden.bs.modal', function() {
            clearFormErrors();
            document.getElementById('typeAbsenceId').value = '';
        });
    }

    const form = document.getElementById('typeAbsenceForm');
    if (form) {
        form.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                saveTypeAbsence();
            }
        });
    }

    const codeInput = document.getElementById('code');
    if (codeInput) {
        codeInput.addEventListener('input', function(e) {
            this.value = this.value.toUpperCase();
        });
    }
});
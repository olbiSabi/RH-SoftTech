/**
 * ========================================
 * JOURS FÉRIÉS - GESTION JAVASCRIPT
 * ========================================
 */

// ============================================
// GESTION DES MODALS
// ============================================

/**
 * Ouvre le modal de création
 */
function openCreateModal() {
    resetForm();
    document.getElementById('modalTitle').textContent = 'Nouveau Jour Férié';
    document.getElementById('jourFerieId').value = '';

    // Utiliser jQuery pour ouvrir la modal (Bootstrap 4)
    $('#jourFerieModal').modal('show');
}

/**
 * Ouvre le modal d'édition
 */
function openEditModal(id) {
    resetForm();
    document.getElementById('modalTitle').textContent = 'Modifier le Jour Férié';
    loadJourFerieData(id);

    // Utiliser jQuery pour ouvrir la modal (Bootstrap 4)
    $('#jourFerieModal').modal('show');
}

/**
 * Ouvre le modal de duplication d'année
 */
function openDuplicateModal() {
    document.getElementById('duplicateForm').reset();

    // Utiliser jQuery pour ouvrir la modal (Bootstrap 4)
    $('#duplicateModal').modal('show');
}

// ============================================
// CHARGEMENT DES DONNÉES
// ============================================

/**
 * Charge les données d'un jour férié
 */
function loadJourFerieData(id) {
    fetch(`/absence/api/jour-ferie/${id}/`)
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
    document.getElementById('jourFerieId').value = data.id;
    document.getElementById('nom').value = data.nom;
    document.getElementById('date').value = data.date;
    document.getElementById('type_ferie').value = data.type_ferie;
    document.getElementById('recurrent').checked = data.recurrent;
    document.getElementById('actif').checked = data.actif;
    document.getElementById('description').value = data.description || '';
}

// ============================================
// SAUVEGARDE
// ============================================

/**
 * Sauvegarde un jour férié (création ou modification)
 */
function saveJourFerie() {
    clearFormErrors();

    const id = document.getElementById('jourFerieId').value;
    const isEdit = id !== '';

    const url = isEdit
        ? `/absence/api/jour-ferie/${id}/update/`
        : '/absence/api/jour-ferie/create/';

    const formData = new FormData();
    formData.append('nom', document.getElementById('nom').value.trim());
    formData.append('date', document.getElementById('date').value);
    formData.append('type_ferie', document.getElementById('type_ferie').value);
    formData.append('recurrent', document.getElementById('recurrent').checked);
    formData.append('actif', document.getElementById('actif').checked);
    formData.append('description', document.getElementById('description').value.trim());
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
            $('#jourFerieModal').modal('hide');

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
 * Supprime un jour férié
 */
function deleteJourFerie(id, nom) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Confirmer la suppression',
            html: `Êtes-vous sûr de vouloir supprimer le jour férié <strong>"${nom}"</strong> ?`,
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
        if (confirm(`Êtes-vous sûr de vouloir supprimer le jour férié "${nom}" ?`)) {
            executeDelete(id);
        }
    }
}

/**
 * Exécute la suppression
 */
function executeDelete(id) {
    fetch(`/absence/api/jour-ferie/${id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
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
 * Active/Désactive un jour férié
 */
function toggleJourFerie(id) {
    fetch(`/absence/api/jour-ferie/${id}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
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
// DUPLICATION D'ANNÉE
// ============================================

/**
 * Duplique les jours fériés d'une année vers une autre
 */
function duplicateJoursFeries() {
    const anneeSource = document.getElementById('annee_source').value;
    const anneeCible = document.getElementById('annee_cible').value;

    if (!anneeSource || !anneeCible) {
        showErrorMessage('Veuillez sélectionner les années source et cible');
        return;
    }

    if (anneeSource === anneeCible) {
        showErrorMessage('Les années source et cible doivent être différentes');
        return;
    }

    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Confirmer la duplication',
            html: `Dupliquer les jours fériés récurrents de <strong>${anneeSource}</strong> vers <strong>${anneeCible}</strong> ?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#17a2b8',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="fas fa-copy"></i> Oui, dupliquer',
            cancelButtonText: '<i class="fas fa-times"></i> Annuler',
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                executeDuplicate(anneeSource, anneeCible);
            }
        });
    } else {
        if (confirm(`Dupliquer les jours fériés de ${anneeSource} vers ${anneeCible} ?`)) {
            executeDuplicate(anneeSource, anneeCible);
        }
    }
}

/**
 * Exécute la duplication
 */
function executeDuplicate(anneeSource, anneeCible) {
    fetch('/absence/api/jour-ferie/dupliquer/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            annee_source: parseInt(anneeSource),
            annee_cible: parseInt(anneeCible)
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Fermer la modal avec jQuery (Bootstrap 4)
            $('#duplicateModal').modal('hide');

            showSuccessMessage(result.message);
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showErrorMessage(result.error || 'Erreur lors de la duplication');
        }
    })
    .catch(error => {
        showErrorMessage('Erreur lors de la duplication');
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

/**
 * Réinitialise le formulaire
 */
function resetForm() {
    document.getElementById('jourFerieForm').reset();
    clearFormErrors();
    document.getElementById('jourFerieId').value = '';

    document.getElementById('type_ferie').value = 'LEGAL';
    document.getElementById('recurrent').checked = true;
    document.getElementById('actif').checked = true;
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
    const modalElement = document.getElementById('jourFerieModal');
    if (modalElement) {
        // Utiliser jQuery pour l'événement Bootstrap 4
        $(modalElement).on('hidden.bs.modal', function() {
            resetForm();
        });
    }

    const form = document.getElementById('jourFerieForm');
    if (form) {
        form.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                saveJourFerie();
            }
        });
    }
});
// assets/js/absence/conventions.js

/**
 * Gestion des conventions collectives
 */

window.showSuccessMessage = function() { return; };

// ===== VARIABLES GLOBALES =====
let isEditMode = false;
let currentConventionId = null;

// ===== INITIALISATION =====
$(document).ready(function() {
    initEventHandlers();
});

// ===== GESTION DES ÉVÉNEMENTS =====
function initEventHandlers() {
    $('#conventionForm').on('submit', function(e) {
        e.preventDefault();
        saveConvention();
    });

    const modalElement = document.getElementById('conventionModal');
    if (modalElement) {
        // Utiliser jQuery pour l'événement Bootstrap 4
        $(modalElement).on('hidden.bs.modal', function () {
            if (!isEditMode) {
                resetForm();
            }
        });
    }
}

// ===== OUVERTURE MODALS =====

function openCreateModal() {
    isEditMode = false;
    currentConventionId = null;

    resetForm();

    $('#conventionModalTitle').html('<i class="fas fa-plus"></i> Nouvelle Convention');
    $('#submitBtn').html('<i class="fas fa-save"></i> Créer');

    // Utiliser jQuery pour ouvrir la modal (Bootstrap 4)
    $('#conventionModal').modal('show');
}

function openEditModal(conventionId) {
    isEditMode = true;
    currentConventionId = conventionId;

    clearFormErrors();

    $('#conventionModalTitle').html('<i class="fas fa-edit"></i> Modifier la Convention');
    $('#submitBtn').html('<i class="fas fa-save"></i> Modifier');

    loadConventionData(conventionId);

    // Utiliser jQuery pour ouvrir la modal (Bootstrap 4)
    $('#conventionModal').modal('show');
}

// ===== CHARGEMENT DES DONNÉES =====

function loadConventionData(conventionId) {
    $.ajax({
        url: `/absence/api/convention/${conventionId}/`,
        type: 'GET',
        success: function(data) {
            populateForm(data);
        },
        error: function(xhr) {
            showErrorMessage('Erreur lors du chargement des données');
        }
    });
}

function populateForm(data) {
    $('#convention_id').val(data.id);
    $('#nom').val(data.nom);
    $('#code').val(data.code);
    $('#annee_reference').val(data.annee_reference);
    $('#date_debut').val(data.date_debut);
    $('#date_fin').val(data.date_fin);
    $('#actif').prop('checked', data.actif);
    $('#jours_acquis_par_mois').val(data.jours_acquis_par_mois);
    $('#duree_conges_principale').val(data.duree_conges_principale);
    $('#methode_calcul').val(data.methode_calcul);

    const anneeReference = parseInt(data.annee_reference);

    if (data.periode_prise_debut) {
        const dateDebut = new Date(data.periode_prise_debut);
        const anneeDebut = dateDebut.getFullYear();

        $('#periode_prise_debut_jour').val(dateDebut.getDate());
        $('#periode_prise_debut_mois').val(String(dateDebut.getMonth() + 1).padStart(2, '0'));

        if (anneeDebut === anneeReference) {
            $('#periode_prise_debut_annee').val('N');
        } else if (anneeDebut === anneeReference + 1) {
            $('#periode_prise_debut_annee').val('N+1');
        }
    }

    if (data.periode_prise_fin) {
        const dateFin = new Date(data.periode_prise_fin);
        const anneeFin = dateFin.getFullYear();

        $('#periode_prise_fin_jour').val(dateFin.getDate());
        $('#periode_prise_fin_mois').val(String(dateFin.getMonth() + 1).padStart(2, '0'));

        if (anneeFin === anneeReference) {
            $('#periode_prise_fin_annee').val('N');
        } else if (anneeFin === anneeReference + 1) {
            $('#periode_prise_fin_annee').val('N+1');
        }
    }

    setTimeout(() => {
        const typeConvention = data.type_convention;

        $('#type_convention').val(typeConvention);

        $('#type_convention option').each(function() {
            if ($(this).val() === typeConvention) {
                $(this).prop('selected', true);
            } else {
                $(this).prop('selected', false);
            }
        });

        $('#type_convention').trigger('change');
    }, 200);
}

// ===== SAUVEGARDE =====

function saveConvention() {
    $('#submitBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Enregistrement...');

    const formData = new FormData($('#conventionForm')[0]);
    const annee = parseInt($('#annee_reference').val());

    const jourDebut = $('#periode_prise_debut_jour').val();
    const moisDebut = $('#periode_prise_debut_mois').val();
    const anneeDebutType = $('#periode_prise_debut_annee').val();
    const anneeDebut = anneeDebutType === 'N+1' ? annee + 1 : annee;
    const periodeDebut = `${anneeDebut}-${moisDebut}-${String(jourDebut).padStart(2, '0')}`;

    const jourFin = $('#periode_prise_fin_jour').val();
    const moisFin = $('#periode_prise_fin_mois').val();
    const anneeFinType = $('#periode_prise_fin_annee').val();
    const anneeFin = anneeFinType === 'N+1' ? annee + 1 : annee;
    const periodeFin = `${anneeFin}-${moisFin}-${String(jourFin).padStart(2, '0')}`;

    formData.set('periode_prise_debut', periodeDebut);
    formData.set('periode_prise_fin', periodeFin);

    if (!formData.has('type_convention')) {
        formData.set('type_convention', $('#type_convention').val() || 'ENTREPRISE');
    }

    const url = isEditMode
        ? `/absence/api/convention/${currentConventionId}/update/`
        : '/absence/api/convention/create/';

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // Fermer la modal avec jQuery (Bootstrap 4)
            $('#conventionModal').modal('hide');
            window.location.reload();
        },
        error: function(xhr) {
            $('#submitBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');

            if (xhr.responseJSON && xhr.responseJSON.errors) {
                displayFormErrors(xhr.responseJSON.errors);
            } else {
                showErrorMessage(xhr.responseJSON?.error || 'Une erreur est survenue');
            }
        }
    });
}

// ===== SUPPRESSION =====

// Fonction appelée par la modale après confirmation
function deleteConventionConfirmed(conventionId) {
    $.ajax({
        url: `/absence/api/convention/${conventionId}/delete/`,
        type: 'POST',
        data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            window.location.reload();
        },
        error: function(xhr) {
            showErrorMessage(xhr.responseJSON?.error || 'Erreur lors de la suppression');
        }
    });
}

// Note: La fonction deleteConvention() est maintenant définie dans le template
// pour ouvrir la modale de confirmation personnalisée

// ===== ACTIVATION/DÉSACTIVATION =====

function toggleConvention(conventionId) {
    $.ajax({
        url: `/absence/api/convention/${conventionId}/toggle/`,
        type: 'POST',
        data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            window.location.reload();
        },
        error: function(xhr) {
            showErrorMessage(xhr.responseJSON?.error || 'Erreur lors du changement de statut');
        }
    });
}

// ===== GESTION DES ERREURS =====

function displayFormErrors(errors) {
    clearFormErrors();

    if (errors.__all__) {
        const errorHtml = errors.__all__.map(err => `<li>${err}</li>`).join('');
        $('#errorList').html(errorHtml);
        $('#formErrors').show();
    }

    Object.keys(errors).forEach(field => {
        if (field !== '__all__') {
            const $input = $(`#${field}`);
            const errorMessage = Array.isArray(errors[field]) ? errors[field][0] : errors[field];

            $input.addClass('is-invalid');
            $input.siblings('.invalid-feedback').text(errorMessage);
        }
    });
}

function clearFormErrors() {
    $('#formErrors').hide();
    $('#errorList').empty();
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').text('');
}

// ===== RÉINITIALISATION =====

function resetForm() {
    $('#conventionForm')[0].reset();
    $('#convention_id').val('');
    $('#actif').prop('checked', true);
    $('#type_convention').val('ENTREPRISE');
    $('#jours_acquis_par_mois').val('2.5');
    $('#duree_conges_principale').val('12');
    $('#methode_calcul').val('MOIS_TRAVAILLES');

    $('#periode_prise_debut_jour').val('');
    $('#periode_prise_debut_mois').val('');
    $('#periode_prise_debut_annee').val('N');
    $('#periode_prise_fin_jour').val('');
    $('#periode_prise_fin_mois').val('');
    $('#periode_prise_fin_annee').val('N+1');

    clearFormErrors();
    $('#submitBtn').prop('disabled', false);
}

// ===== MESSAGES (ERREURS UNIQUEMENT) =====

function showErrorMessage(message) {
    if (typeof toastr !== 'undefined') {
        toastr.error(message, 'Erreur', {
            closeButton: true,
            progressBar: true,
            timeOut: 5000
        });
    } else {
        alert('Erreur: ' + message);
    }
}
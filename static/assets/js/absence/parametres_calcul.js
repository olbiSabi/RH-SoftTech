// static/assets/js/absence/parametres_calcul.js

/**
 * Gestion des paramètres de calcul des congés
 */

// ✅ BLOQUER showSuccessMessage
window.showSuccessMessage = function() { return; };

// ===== VARIABLES GLOBALES =====
let isEditMode = false;
let currentParametreId = null;

// ===== INITIALISATION =====
$(document).ready(function() {
    initEventHandlers();
    toggleReportFields(); // Initialiser l'affichage des champs report
});

// ===== GESTION DES ÉVÉNEMENTS =====
function initEventHandlers() {
    // Soumission du formulaire
    $('#parametreForm').on('submit', function(e) {
        e.preventDefault();
        saveParametre();
    });

    // Toggle des champs report
    $('#report_autorise').on('change', function() {
        toggleReportFields();
    });

    // Réinitialiser le formulaire à la fermeture du modal
    const modalElement = document.getElementById('parametreModal');
    if (modalElement) {
        // Utiliser jQuery pour l'événement Bootstrap 4
        $(modalElement).on('hidden.bs.modal', function() {
            if (!isEditMode) {
                resetForm();
            }
        });
    }
}

// ===== TOGGLE CHAMPS REPORT =====
function toggleReportFields() {
    const isChecked = $('#report_autorise').is(':checked');

    if (isChecked) {
        $('#report_fields').addClass('show');
        $('#jours_report_max').prop('required', true);
        $('#delai_prise_report').prop('required', true);
    } else {
        $('#report_fields').removeClass('show');
        $('#jours_report_max').prop('required', false);
        $('#delai_prise_report').prop('required', false);
    }
}

// ===== OUVERTURE MODALS =====

/**
 * Ouvrir le modal en mode création
 */
function openCreateModal() {
    isEditMode = false;
    currentParametreId = null;

    // Réinitialiser le formulaire
    resetForm();

    // Mettre à jour le titre
    $('#parametreModalTitle').html('<i class="fas fa-plus"></i> Nouveau Paramètre');
    $('#submitBtn').html('<i class="fas fa-save"></i> Créer');

    // Afficher le modal avec jQuery (Bootstrap 4)
    $('#parametreModal').modal('show');
}

/**
 * Ouvrir le modal en mode édition
 */
function openEditModal(parametreId) {
    isEditMode = true;
    currentParametreId = parametreId;

    // Effacer les erreurs
    clearFormErrors();

    // Mettre à jour le titre
    $('#parametreModalTitle').html('<i class="fas fa-edit"></i> Modifier le Paramètre');
    $('#submitBtn').html('<i class="fas fa-save"></i> Modifier');

    // Charger les données
    loadParametreData(parametreId);

    // Afficher le modal avec jQuery (Bootstrap 4)
    $('#parametreModal').modal('show');
}

// ===== CHARGEMENT DES DONNÉES =====

/**
 * Charger les données d'un paramètre
 */
function loadParametreData(parametreId) {
    $.ajax({
        url: `/absence/api/parametre-calcul/${parametreId}/`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                populateForm(response.data);
            } else {
                showErrorMessage('Erreur lors du chargement des données');
            }
        },
        error: function(xhr) {
            showErrorMessage('Erreur lors du chargement des données');
        }
    });
}

/**
 * Remplir le formulaire avec les données
 */
function populateForm(data) {
    $('#parametre_id').val(data.id);
    $('#configuration').val(data.configuration);
    $('#mois_acquisition_min').val(data.mois_acquisition_min);
    $('#plafond_jours_an').val(data.plafond_jours_an);
    $('#report_autorise').prop('checked', data.report_autorise);
    $('#jours_report_max').val(data.jours_report_max);
    $('#delai_prise_report').val(data.delai_prise_report);
    $('#prise_compte_temps_partiel').prop('checked', data.prise_compte_temps_partiel);

    // Ancienneté
    $('#anciennete_5_ans').val(data.anciennete_5_ans);
    $('#anciennete_10_ans').val(data.anciennete_10_ans);
    $('#anciennete_15_ans').val(data.anciennete_15_ans);
    $('#anciennete_20_ans').val(data.anciennete_20_ans);

    // Afficher/masquer les champs report
    toggleReportFields();
}

// ===== SAUVEGARDE =====

/**
 * Sauvegarder un paramètre (création ou modification)
 */
function saveParametre() {
    // Désactiver le bouton
    $('#submitBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Enregistrement...');

    // Préparer les données
    const formData = new FormData($('#parametreForm')[0]);

    // Convertir les checkboxes en valeurs on/off pour Django
    formData.set('report_autorise', $('#report_autorise').is(':checked') ? 'on' : '');
    formData.set('prise_compte_temps_partiel', $('#prise_compte_temps_partiel').is(':checked') ? 'on' : '');

    // Déterminer l'URL
    const url = isEditMode
        ? `/absence/api/parametre-calcul/${currentParametreId}/update/`
        : '/absence/api/parametre-calcul/create/';

    // Envoyer la requête
    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                // Fermer le modal avec jQuery (Bootstrap 4)
                $('#parametreModal').modal('hide');

                // Recharger la page
                window.location.reload();
            } else {
                // Afficher les erreurs
                if (response.errors) {
                    displayFormErrors(response.errors);
                } else {
                    showErrorMessage(response.error || 'Une erreur est survenue');
                }

                // Réactiver le bouton
                $('#submitBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');
            }
        },
        error: function(xhr) {
            // Réactiver le bouton
            $('#submitBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');

            // Afficher les erreurs
            if (xhr.responseJSON && xhr.responseJSON.errors) {
                displayFormErrors(xhr.responseJSON.errors);
            } else {
                showErrorMessage(xhr.responseJSON?.error || 'Une erreur est survenue');
            }
        }
    });
}

// ===== SUPPRESSION =====

/**
 * Supprimer un paramètre
 */
function deleteParametre(parametreId, conventionNom) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer les paramètres de la convention "${conventionNom}" ?\n\nCette action est irréversible.`)) {
        return;
    }

    $.ajax({
        url: `/absence/api/parametre-calcul/${parametreId}/delete/`,
        type: 'POST',
        data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                window.location.reload();
            } else {
                showErrorMessage(response.error || 'Erreur lors de la suppression');
            }
        },
        error: function(xhr) {
            showErrorMessage(xhr.responseJSON?.error || 'Erreur lors de la suppression');
        }
    });
}

// ===== GESTION DES ERREURS =====

/**
 * Afficher les erreurs du formulaire
 */
function displayFormErrors(errors) {
    // Réinitialiser les erreurs
    clearFormErrors();

    // Erreurs globales
    if (errors.__all__ || errors.non_field_errors) {
        const globalErrors = errors.__all__ || errors.non_field_errors;
        const errorHtml = (Array.isArray(globalErrors) ? globalErrors : [globalErrors])
            .map(err => `<li>${err}</li>`).join('');
        $('#errorList').html(errorHtml);
        $('#formErrors').show();
    }

    // Erreurs par champ
    Object.keys(errors).forEach(field => {
        if (field !== '__all__' && field !== 'non_field_errors') {
            const $input = $(`#${field}`);
            const errorMessage = Array.isArray(errors[field]) ? errors[field][0] : errors[field];

            $input.addClass('is-invalid');
            $input.siblings('.invalid-feedback').text(errorMessage);
        }
    });
}

/**
 * Effacer les erreurs du formulaire
 */
function clearFormErrors() {
    $('#formErrors').hide();
    $('#errorList').empty();
    $('.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').text('');
}

// ===== RÉINITIALISATION =====

/**
 * Réinitialiser le formulaire
 */
function resetForm() {
    $('#parametreForm')[0].reset();
    $('#parametre_id').val('');

    // Valeurs par défaut
    $('#mois_acquisition_min').val(1);
    $('#plafond_jours_an').val(30);
    $('#report_autorise').prop('checked', true);
    $('#jours_report_max').val(15);
    $('#delai_prise_report').val(365);
    $('#prise_compte_temps_partiel').prop('checked', true);

    // Ancienneté à 0
    $('#anciennete_5_ans').val(0);
    $('#anciennete_10_ans').val(0);
    $('#anciennete_15_ans').val(0);
    $('#anciennete_20_ans').val(0);

    // Effacer les erreurs
    clearFormErrors();

    // Réactiver le bouton
    $('#submitBtn').prop('disabled', false);

    // Afficher les champs report
    toggleReportFields();
}

// ===== MESSAGES (ERREURS UNIQUEMENT) =====

/**
 * Afficher un message d'erreur
 */
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
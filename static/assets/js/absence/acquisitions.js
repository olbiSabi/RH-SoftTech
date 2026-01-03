// static/assets/js/absence/acquisitions.js

/**
 * Gestion des acquisitions de congés
 */

// ✅ BLOQUER showSuccessMessage
window.showSuccessMessage = function() { return; };

// ===== VARIABLES GLOBALES =====
let currentAcquisitionId = null;
let currentAcquisitionData = null;

// ===== INITIALISATION =====
$(document).ready(function() {
    initEventHandlers();
});

// ===== GESTION DES ÉVÉNEMENTS =====
function initEventHandlers() {
    // Soumission du formulaire de calcul
    $('#calculForm').on('submit', function(e) {
        e.preventDefault();
        calculerAcquisitions();
    });

    // Soumission du formulaire d'édition
    $('#editForm').on('submit', function(e) {
        e.preventDefault();
        saveEdit();
    });

    // Mise à jour du preview des jours restants
    $('#edit_jours_report_anterieur').on('input', function() {
        updateJoursRestantsPreview();
    });

    // Réinitialiser à la fermeture des modals
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        detailModal.addEventListener('hidden.bs.modal', function () {
            $('#detailContent').html('<div class="text-center py-4"><i class="fas fa-spinner fa-spin fa-2x"></i></div>');
        });
    }

    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.addEventListener('hidden.bs.modal', function () {
            resetEditForm();
        });
    }
}

// ===== CALCUL DES ACQUISITIONS EN MASSE =====

/**
 * Calculer les acquisitions pour une année
 */
function calculerAcquisitions() {
    const form = $('#calculForm');
    const submitBtn = form.find('button[type="submit"]');

    // Confirmation
    const annee = $('#id_annee_reference').val();
    const recalculer = $('#id_recalculer_existantes').is(':checked');

    let message = `Calculer les acquisitions pour l'année ${annee} ?`;
    if (recalculer) {
        message += "\n\n⚠️ Les acquisitions existantes seront recalculées.";
    }

    if (!confirm(message)) {
        return;
    }

    // Désactiver le bouton
    submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Calcul en cours...');

    // Envoyer la requête
    $.ajax({
        url: '/absence/api/acquisitions/calculer/',
        type: 'POST',
        data: form.serialize(),
        success: function(response) {
            if (response.success) {
                // Afficher les résultats
                showCalculResults(response.resultats);

                // Recharger la page après 3 secondes
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
            } else {
                showErrorMessage(response.error || 'Erreur lors du calcul');
                submitBtn.prop('disabled', false).html('<i class="fas fa-calculator"></i> Calculer');
            }
        },
        error: function(xhr) {
            submitBtn.prop('disabled', false).html('<i class="fas fa-calculator"></i> Calculer');

            if (xhr.responseJSON && xhr.responseJSON.errors) {
                let errorMsg = 'Erreurs de validation :\n';
                Object.keys(xhr.responseJSON.errors).forEach(field => {
                    errorMsg += `- ${xhr.responseJSON.errors[field]}\n`;
                });
                showErrorMessage(errorMsg);
            } else {
                showErrorMessage(xhr.responseJSON?.error || 'Erreur lors du calcul');
            }
        }
    });
}

/**
 * Afficher les résultats du calcul
 */
function showCalculResults(resultats) {
    let message = `✅ Calcul terminé !\n\n`;
    message += `• Total traité : ${resultats.total}\n`;
    message += `• Créées : ${resultats.crees}\n`;
    message += `• Mises à jour : ${resultats.mis_a_jour}\n`;
    message += `• Ignorées : ${resultats.ignores}\n`;

    if (resultats.erreurs > 0) {
        message += `\n⚠️ Erreurs : ${resultats.erreurs}\n`;

        if (resultats.details_erreurs && resultats.details_erreurs.length > 0) {
            message += `\nDétails des erreurs :\n`;
            resultats.details_erreurs.forEach(err => {
                message += `- ${err.employe} : ${err.erreur}\n`;
            });
        }
    }

    alert(message);
}

// ===== MODAL DÉTAILS =====

/**
 * Ouvrir le modal de détails
 */
function openDetailModal(acquisitionId) {
    currentAcquisitionId = acquisitionId;

    // Charger les données
    loadAcquisitionDetails(acquisitionId);

    // Afficher le modal
    const modal = new bootstrap.Modal(document.getElementById('detailModal'));
    modal.show();
}

/**
 * Charger les détails d'une acquisition
 */
function loadAcquisitionDetails(acquisitionId) {
    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                displayAcquisitionDetails(response.data);
            } else {
                $('#detailContent').html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> ${response.error}
                    </div>
                `);
            }
        },
        error: function(xhr) {
            $('#detailContent').html(`
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> Erreur lors du chargement
                </div>
            `);
        }
    });
}

/**
 * Afficher les détails dans le modal
 */
function displayAcquisitionDetails(data) {
    const html = `
        <div class="row">
            <div class="col-md-12">
                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong><i class="fas fa-user"></i> Informations Employé</strong>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <div class="detail-label">Employé</div>
                            <div class="detail-value">${data.employe_nom}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Année de référence</div>
                            <div class="detail-value">${data.annee_reference}</div>
                        </div>
                    </div>
                </div>

                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong><i class="fas fa-calendar-check"></i> Solde de Congés</strong>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <div class="detail-label">Jours Acquis</div>
                            <div class="detail-value highlight">
                                <span class="badge badge-lg badge-success">${data.jours_acquis} jours</span>
                            </div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Jours Pris</div>
                            <div class="detail-value">
                                <span class="badge badge-lg badge-warning">${data.jours_pris} jours</span>
                            </div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Jours Restants</div>
                            <div class="detail-value highlight">
                                <span class="badge badge-lg badge-primary">${data.jours_restants} jours</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong><i class="fas fa-redo"></i> Reports</strong>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <div class="detail-label">Report Antérieur</div>
                            <div class="detail-value">
                                <span class="badge badge-lg badge-info">${data.jours_report_anterieur} jours</span>
                            </div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Nouveau Report</div>
                            <div class="detail-value">
                                <span class="badge badge-lg badge-secondary">${data.jours_report_nouveau} jours</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header bg-light">
                        <strong><i class="fas fa-clock"></i> Dates</strong>
                    </div>
                    <div class="card-body">
                        <div class="detail-row">
                            <div class="detail-label">Date de calcul</div>
                            <div class="detail-value">${data.date_calcul}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Dernière mise à jour</div>
                            <div class="detail-value">${data.date_maj}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    $('#detailContent').html(html);
}

// ===== MODAL ÉDITION =====

/**
 * Ouvrir le modal d'édition
 */
function openEditModal(acquisitionId) {
    currentAcquisitionId = acquisitionId;

    // Charger les données
    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                currentAcquisitionData = response.data;
                populateEditForm(response.data);

                // Afficher le modal
                const modal = new bootstrap.Modal(document.getElementById('editModal'));
                modal.show();
            } else {
                showErrorMessage(response.error);
            }
        },
        error: function(xhr) {
            showErrorMessage('Erreur lors du chargement des données');
        }
    });
}

/**
 * Remplir le formulaire d'édition
 */
function populateEditForm(data) {
    $('#edit_acquisition_id').val(data.id);
    $('#edit_employe_nom').val(data.employe_nom);
    $('#edit_annee').val(data.annee_reference);
    $('#edit_jours_report_anterieur').val(data.jours_report_anterieur);

    // Calculer le preview des jours restants
    updateJoursRestantsPreview();
}

/**
 * Mettre à jour le preview des jours restants
 */
function updateJoursRestantsPreview() {
    if (!currentAcquisitionData) return;

    const reportAnterieur = parseFloat($('#edit_jours_report_anterieur').val() || 0);
    const joursAcquis = parseFloat(currentAcquisitionData.jours_acquis);
    const joursPris = parseFloat(currentAcquisitionData.jours_pris);

    const joursRestants = joursAcquis + reportAnterieur - joursPris;

    $('#edit_jours_restants_preview').val(joursRestants.toFixed(2) + ' jours');
}

/**
 * Sauvegarder la modification
 */
function saveEdit() {
    const acquisitionId = $('#edit_acquisition_id').val();
    const submitBtn = $('#submitEditBtn');

    // Désactiver le bouton
    submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Enregistrement...');

    // Préparer les données
    const formData = new FormData($('#editForm')[0]);

    // Envoyer la requête
    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/update/`,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                // Fermer le modal
                const modalElement = document.getElementById('editModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }

                // Recharger la page
                window.location.reload();
            } else {
                showErrorMessage(response.error || 'Erreur lors de la mise à jour');
                submitBtn.prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');
            }
        },
        error: function(xhr) {
            submitBtn.prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');
            showErrorMessage(xhr.responseJSON?.error || 'Erreur lors de la mise à jour');
        }
    });
}

/**
 * Réinitialiser le formulaire d'édition
 */
function resetEditForm() {
    $('#editForm')[0].reset();
    $('#edit_acquisition_id').val('');
    currentAcquisitionData = null;
    $('#submitEditBtn').prop('disabled', false).html('<i class="fas fa-save"></i> Enregistrer');
}

// ===== RECALCUL D'UNE ACQUISITION =====

/**
 * Recalculer une acquisition spécifique
 */
function recalculerAcquisition(acquisitionId) {
    if (!confirm('Recalculer cette acquisition ?\n\nLes jours acquis seront recalculés selon la convention applicable.')) {
        return;
    }

    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/recalculer/`,
        type: 'POST',
        data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                // Recharger la page
                window.location.reload();
            } else {
                showErrorMessage(response.error || 'Erreur lors du recalcul');
            }
        },
        error: function(xhr) {
            showErrorMessage(xhr.responseJSON?.error || 'Erreur lors du recalcul');
        }
    });
}

// ===== SUPPRESSION =====

/**
 * Supprimer une acquisition
 */
function deleteAcquisition(acquisitionId, employeNom, annee) {
    if (!confirm(`Supprimer l'acquisition de ${employeNom} pour ${annee} ?\n\nCette action est irréversible.`)) {
        return;
    }

    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/delete/`,
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

// ===== EXPORT EXCEL =====

/**
 * Exporter le tableau vers Excel
 */
function exportToExcel() {
    // Récupérer le tableau
    const table = document.getElementById('acquisitionsTable');

    if (!table) {
        showErrorMessage('Aucune donnée à exporter');
        return;
    }

    // Vérifier s'il y a des données
    const rows = table.querySelectorAll('tbody tr');
    if (rows.length === 0 || rows[0].cells.length === 1) {
        showErrorMessage('Aucune donnée à exporter');
        return;
    }

    // Créer une copie du tableau pour l'export (sans la colonne Actions)
    const exportTable = table.cloneNode(true);

    // Supprimer la colonne Actions (dernière colonne)
    const headerRows = exportTable.querySelectorAll('thead tr');
    headerRows.forEach(row => {
        if (row.cells.length > 0) {
            row.deleteCell(row.cells.length - 1);
        }
    });

    const bodyRows = exportTable.querySelectorAll('tbody tr');
    bodyRows.forEach(row => {
        if (row.cells.length > 1) {
            row.deleteCell(row.cells.length - 1);
        }
    });

    // Convertir en HTML
    const html = exportTable.outerHTML;

    // Créer un blob Excel
    const blob = new Blob([html], {
        type: 'application/vnd.ms-excel'
    });

    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // Nom du fichier avec date
    const annee = $('#filterForm select[name="annee"]').val() || new Date().getFullYear();
    const date = new Date().toISOString().split('T')[0];
    a.download = `acquisitions_conges_${annee}_${date}.xls`;

    // Déclencher le téléchargement
    document.body.appendChild(a);
    a.click();

    // Nettoyer
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
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

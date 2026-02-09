// static/assets/js/absence/acquisitions.js


/**
 * Gestion des acquisitions de congés
 */

// ✅ BLOQUER showSuccessMessage
window.showSuccessMessage = function() { return; };

// ===== VARIABLES GLOBALES =====
let currentAcquisitionId = null;
let currentAcquisitionData = null;

// ===== FONCTION HELPER CSRF TOKEN =====
/**
 * Récupérer le CSRF token depuis les cookies
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
        // Utiliser jQuery pour l'événement Bootstrap 4
        $(detailModal).on('hidden.bs.modal', function() {
            $('#detailContent').html('<div class="text-center py-4"><i class="fas fa-spinner fa-spin fa-2x"></i></div>');
        });
    }

    const editModal = document.getElementById('editModal');
    if (editModal) {
        // Utiliser jQuery pour l'événement Bootstrap 4
        $(editModal).on('hidden.bs.modal', function() {
            resetEditForm();
        });
    }
}

// ===== CALCUL DES ACQUISITIONS EN MASSE =====

/**
 * Calculer les acquisitions pour une année
 */
function calculerAcquisitions() {
    const annee = $('#id_annee_reference').val();
    const recalculer = $('#id_recalculer_existantes').is(':checked');

    // Ouvrir le modal personnalisé
    if (typeof ouvrirModalCalcul === 'function') {
        ouvrirModalCalcul(annee, recalculer);
    } else {
        // Fallback si le modal n'est pas disponible
        let message = `Calculer les acquisitions pour l'année ${annee} ?`;
        if (recalculer) {
            message += "\n\n⚠️ Les acquisitions existantes seront recalculées.";
        }
        if (!confirm(message)) {
            return;
        }
        calculerAcquisitionsConfirmed();
    }
}

/**
 * Calculer les acquisitions sans confirmation (appelé par le modal)
 */
function calculerAcquisitionsConfirmed() {
    const form = $('#calculForm');
    const submitBtn = form.find('button[type="submit"]');

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

    // Afficher le modal avec jQuery (Bootstrap 4)
    $('#detailModal').modal('show');
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

                // Afficher le modal avec jQuery (Bootstrap 4)
                $('#editModal').modal('show');
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
                // Fermer le modal avec jQuery (Bootstrap 4)
                $('#editModal').modal('hide');

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
    console.log('🔄 recalculerAcquisition appelé avec ID:', acquisitionId);
    
    // Ouvrir le modal personnalisé
    if (typeof ouvrirModalRecalcul === 'function') {
        console.log('✅ ouvrirModalRecalcul trouvé, ouverture du modal');
        ouvrirModalRecalcul(acquisitionId);
    } else {
        console.log('❌ ouvrirModalRecalcul NON trouvé, utilisation du fallback');
        // Fallback avec SweetAlert ou confirm
        if (typeof Swal === 'undefined') {
            console.log('❌ Swal NON trouvé, utilisation de confirm');
            if (!confirm('Recalculer cette acquisition ?\n\nLes jours acquis seront recalculés selon la convention applicable.')) {
                return;
            }
            executeRecalcul(acquisitionId);
        } else {
            console.log('✅ Swal trouvé, ouverture SweetAlert');
            Swal.fire({
                title: 'Recalculer cette acquisition ?',
                text: 'Les jours acquis seront recalculés selon la convention applicable',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#28a745',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Oui, recalculer',
                cancelButtonText: 'Annuler'
            }).then((result) => {
                if (result.isConfirmed) {
                    executeRecalcul(acquisitionId);
                }
            });
        }
    }
}

/**
 * Exécuter le recalcul (fonction helper)
 */
function executeRecalcul(acquisitionId) {
    console.log('🚀 executeRecalcul appelé avec ID:', acquisitionId);
    
    // Afficher un loader
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Recalcul en cours...',
            text: 'Veuillez patienter...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
    } else {
        console.log('⚠️ Swal non disponible, utilisation loader simple');
    }

    console.log('📡 Envoi requête AJAX vers:', `/absence/api/acquisition/${acquisitionId}/recalculer/`);
    console.log('🍪 CSRF Token:', getCookie('csrftoken'));

    $.ajax({
        url: `/absence/api/acquisition/${acquisitionId}/recalculer/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        data: {
            csrfmiddlewaretoken: getCookie('csrftoken')
        },
        beforeSend: function(xhr) {
            console.log('📤 beforeSend appelé');
        },
        success: function(response) {
            console.log('✅ Succès AJAX:', response);
            if (typeof Swal !== 'undefined') {
                Swal.close();
            }

            if (response.success) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: 'Succès !',
                        html: `
                            <p>${response.message}</p>
                            <div class="mt-3 text-left">
                                <strong>Jours acquis :</strong> ${response.jours_acquis}<br>
                                <strong>Jours restants :</strong> ${response.jours_restants}
                                ${response.mois_travailles ? `<br><strong>Mois travaillés :</strong> ${response.mois_travailles}` : ''}
                            </div>
                        `,
                        timer: 3000,
                        timerProgressBar: true,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    alert('Acquisition recalculée avec succès');
                    window.location.reload();
                }
            } else {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erreur',
                        text: response.error || 'Erreur lors du recalcul'
                    });
                } else {
                    alert('Erreur: ' + (response.error || 'Erreur lors du recalcul'));
                }
            }
        },
        error: function(xhr) {
            console.error('❌ ERREUR AJAX - Détails complets:');
            console.error('Status:', xhr.status);
            console.error('Status Text:', xhr.statusText);
            console.error('Response Text:', xhr.responseText);
            console.error('Response JSON:', xhr.responseJSON);
            console.error('Full XHR:', xhr);
            
            if (typeof Swal !== 'undefined') {
                Swal.close();
            }

            // Log détaillé dans la console
            console.error('❌ ERREUR RECALCUL - Détails complets:');
            console.error('Status:', xhr.status);
            console.error('Status Text:', xhr.statusText);
            console.error('Response Text:', xhr.responseText);
            console.error('Response JSON:', xhr.responseJSON);
            console.error('Full XHR:', xhr);

            let errorMsg = 'Erreur lors du recalcul';
            let errorDetails = '';

            if (xhr.responseJSON) {
                errorMsg = xhr.responseJSON.error || errorMsg;
            } else if (xhr.responseText) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.error || errorMsg;
                } catch (e) {
                    errorDetails = xhr.responseText.substring(0, 200); // Limiter la taille
                }
            }

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'error',
                    title: 'Erreur de recalcul',
                    html: `
                        <p><strong>${errorMsg}</strong></p>
                        ${errorDetails ? `<hr><small class="text-muted">Détails: ${errorDetails}</small>` : ''}
                        <hr>
                        <small class="text-muted">
                            Code HTTP: ${xhr.status}<br>
                            Consultez la console (F12) pour plus de détails
                        </small>
                    `,
                    width: 600
                });
            } else {
                alert(`Erreur: ${errorMsg}\n\nCode HTTP: ${xhr.status}\n\nConsultez la console (F12) pour plus de détails`);
            }
        }
    });
}


// ===== SUPPRESSION =====

/**
 * Supprimer une acquisition
 */
function deleteAcquisition(acquisitionId, employeNom, annee) {
    // Ouvrir le modal personnalisé
    if (typeof ouvrirModalSuppressionAcquisition === 'function') {
        ouvrirModalSuppressionAcquisition(acquisitionId, employeNom, annee);
    } else {
        // Fallback si le modal n'est pas disponible
        if (!confirm(`Supprimer l'acquisition de ${employeNom} pour ${annee} ?\n\nCette action est irréversible.`)) {
            return;
        }
        deleteAcquisitionConfirmed(acquisitionId);
    }
}

/**
 * Supprimer une acquisition sans confirmation (appelé par le modal)
 */
function deleteAcquisitionConfirmed(acquisitionId) {
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






// ========================================
// SOLUTION ALTERNATIVE - Force la récupération
// ========================================

$('#simulationForm').on('submit', function(e) {
    e.preventDefault();

    // ✅ MÉTHODE ALTERNATIVE : Récupérer via l'option sélectionnée
    let employeId = '';

    // Méthode 1 : Via l'option sélectionnée
    const selectedOption = $('#sim_employe option:selected');
    employeId = selectedOption.val() || selectedOption.attr('value');

    console.log('Méthode 1 (option:selected):', employeId);

    // Si toujours vide, essayer via selectedIndex
    if (!employeId || employeId === '') {
        const selectElement = document.getElementById('sim_employe');
        const selectedIndex = selectElement.selectedIndex;
        if (selectedIndex > 0) {  // > 0 pour ignorer "-- Sélectionner --"
            employeId = selectElement.options[selectedIndex].value ||
                       selectElement.options[selectedIndex].getAttribute('value');
            console.log('Méthode 2 (selectedIndex):', employeId);
        }
    }

    // Si toujours vide, essayer via data-id
    if (!employeId || employeId === '') {
        employeId = $('#sim_employe option:selected').data('id');
        console.log('Méthode 3 (data-id):', employeId);
    }

    // Récupérer année et date (ceux-ci fonctionnent)
    const annee = $.trim($('#sim_annee').val());
    const date = $.trim($('#sim_date').val());

    console.log('Valeurs récupérées:', {
        employeId: employeId,
        annee: annee,
        date: date
    });

    // Validation
    if (!employeId || employeId === '' || employeId === '0') {
        showMessage('Veuillez sélectionner un employé', 'error');

        // Debug : Afficher le HTML du select
        console.error('DEBUG - HTML du select:', $('#sim_employe')[0].outerHTML);
        console.error('DEBUG - Options:');
        $('#sim_employe option').each(function() {
            console.log('  -', $(this).text(), '| value=', $(this).attr('value'));
        });

        return;
    }

    if (!annee || annee === '') {
        showMessage('Veuillez sélectionner une année', 'error');
        return;
    }

    if (!date || date === '') {
        showMessage('Veuillez sélectionner une date', 'error');
        return;
    }

    // Loader
    const submitBtn = $(this).find('button[type="submit"]');
    const originalText = submitBtn.html();
    submitBtn.prop('disabled', true);
    submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Calcul en cours...');

    // AJAX
    $.ajax({
        url: '/absence/api/calculer-acquis-a-date/',
        method: 'GET',
        data: {
            employe_id: employeId,
            annee: annee,
            date: date
        },
        success: function(response) {
            console.log('Réponse API:', response);

            submitBtn.prop('disabled', false);
            submitBtn.html(originalText);

            if (response.success) {
                $('#result_employe').text(response.data.employe);
                $('#result_date').text(response.data.date_reference);
                $('#result_mois').text(response.data.mois_travailles);
                $('#result_jours').text(response.data.jours_acquis + ' jours');

                if (response.data.detail) {
                    afficherDetailMois(response.data.detail);
                }

                $('#simulationResult').slideDown();
                showMessage('Simulation effectuée avec succès', 'success');
            } else {
                showMessage(response.error, 'error');
            }
        },
        error: function(xhr) {
            console.error('Erreur AJAX:', xhr);

            submitBtn.prop('disabled', false);
            submitBtn.html(originalText);

            const error = xhr.responseJSON?.error || 'Erreur lors du calcul';
            showMessage(error, 'error');
        }
    });
});

// ========================================
// FONCTION : Afficher message
// ========================================
function showMessage(message, type) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const messageHtml = `
        <div class="custom-message ${type}" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-left: 4px solid ${colors[type]};
            z-index: 9999;
            max-width: 400px;
            animation: slideInRight 0.3s ease;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas ${icons[type]}" style="color: ${colors[type]}; font-size: 20px;"></i>
                <span style="flex: 1; color: #333; font-size: 14px;">${message}</span>
                <button onclick="$(this).closest('.custom-message').remove();" style="
                    background: none;
                    border: none;
                    color: #999;
                    cursor: pointer;
                    font-size: 18px;
                    padding: 0;
                ">&times;</button>
            </div>
        </div>
    `;

    $('body').append(messageHtml);

    setTimeout(function() {
        $('.custom-message').fadeOut(300, function() {
            $(this).remove();
        });
    }, 3000);
}

// ========================================
// FONCTION : Afficher détail mois
// ========================================
function afficherDetailMois(detail) {
    let container = $('#detail_mois_container');

    if (container.length === 0) {
        $('#simulationResult .table').after('<div id="detail_mois_container"></div>');
        container = $('#detail_mois_container');
    }

    let html = `
        <div class="mt-3 pt-3" style="border-top: 1px solid #e0e0e0;">
            <h6 class="mb-3">
                <i class="fas fa-calendar-alt"></i> Détail par mois
            </h6>
            <div class="row">
    `;

    for (const [mois, info] of Object.entries(detail)) {
        const badgeClass = info.actif ? 'badge-success' : 'badge-secondary';
        const icon = info.actif ? 'fa-check' : 'fa-times';
        const joursText = parseFloat(info.jours).toFixed(2);

        html += `
            <div class="col-6 col-md-3 mb-2">
                <div class="badge ${badgeClass} d-block p-2" style="font-size: 0.9em;">
                    <i class="fas ${icon}"></i>
                    ${mois.charAt(0).toUpperCase() + mois.slice(1)} : <strong>${joursText}</strong> j
                </div>
            </div>
        `;
    }

    html += '</div></div>';
    container.html(html);
}

// ========================================
// CSS Animation
// ========================================
if (!$('head').find('#custom-message-styles').length) {
    $('head').append(`
        <style id="custom-message-styles">
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        </style>
    `);
}
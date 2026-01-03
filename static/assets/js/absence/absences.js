// static/assets/js/absence/absences_simple.js

console.log('✅ Fichier absences_simple.js chargé');

$(document).ready(function() {
    console.log('✅ Document ready');

    // ========================================
    // DÉTAILS
    // ========================================
    $(document).on('click', '.btn-detail', function(e) {
        e.preventDefault();
        const absenceId = $(this).data('absence-id');
        console.log('🔍 Clic détails, ID:', absenceId);

        // Réinitialiser le contenu
        $('#detailContent').html(`
            <div class="text-center py-4">
                <div class="spinner-border text-primary"></div>
                <p class="mt-2">Chargement...</p>
            </div>
        `);

        // Ouvrir la modal
        $('#detailModal').modal('show');

        // Charger les données
        $.ajax({
            url: `/absence/api/absence/${absenceId}/`,
            type: 'GET',
            success: function(data) {
                console.log('✅ Données reçues:', data);
                if (data.success) {
                    afficherDetails(data.data);
                } else {
                    $('#detailContent').html(`<div class="alert alert-danger">${data.error}</div>`);
                }
            },
            error: function(xhr) {
                console.error('❌ Erreur:', xhr);
                $('#detailContent').html(`<div class="alert alert-danger">Erreur de chargement</div>`);
            }
        });
    });

// ========================================
// ANNULER - VERSION AVEC RECHARGEMENT
// ========================================
$(document).on('click', '.btn-annuler', function(e) {
    e.preventDefault();

    if (!confirm('Annuler cette absence ?\n\nCette action est irréversible.')) return;

    const absenceId = $(this).data('absence-id');
    const $button = $(this);
    const $row = $button.closest('tr');

    console.log('⚠️ Annulation ID:', absenceId);

    $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');

    $.ajax({
        url: `/absence/api/absence/${absenceId}/annuler/`,
        type: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
        success: function(response) {
            console.log('✅ Réponse serveur:', response);

            if (response.success) {
                // ✅ SOLUTION SIMPLE : Recharger la page après 1 seconde
                toastr.success(response.message || 'Absence annulée avec succès');

                setTimeout(function() {
                    console.log('🔄 Rechargement de la page...');
                    window.location.reload();
                }, 1000);

            } else {
                console.error('❌ Erreur:', response.error);
                toastr.error(response.error || 'Erreur lors de l\'annulation');
                $button.prop('disabled', false).html('<i class="fas fa-ban"></i>');
            }
        },
        error: function(xhr) {
            console.error('❌ Erreur AJAX:', xhr);
            const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
            toastr.error(errorMsg);
            $button.prop('disabled', false).html('<i class="fas fa-ban"></i>');
        }
    });
});

// ========================================
// SUPPRIMER
// ========================================
$(document).on('click', '.btn-supprimer', function(e) {
    e.preventDefault();

    const typeAbsence = $(this).data('type-absence');
    if (!confirm(`Supprimer "${typeAbsence}" ?\n\nIrréversible.`)) return;

    const absenceId = $(this).data('absence-id');
    const $button = $(this);
    const $row = $button.closest('tr');

    console.log('🗑️ Suppression ID:', absenceId);
    console.log('🗑️ Ligne trouvée:', $row.length);

    $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');

    $.ajax({
        url: `/absence/api/absence/${absenceId}/delete/`,
        type: 'POST',
        headers: {'X-CSRFToken': getCsrfToken()},
        success: function(response) {
            console.log('✅ Réponse serveur:', response);

            if (response.success) {
                console.log('✅ Suppression réussie, animation de la ligne...');

                // ✅ ANIMATION + SUPPRESSION DE LA LIGNE
                $row.fadeOut(400, function() {
                    console.log('🗑️ Ligne supprimée du DOM');
                    $(this).remove();

                    // Vérifier s'il reste des lignes
                    const $tbody = $('#absencesTable tbody');
                    const $remainingRows = $tbody.find('tr:not(.empty-message)');

                    console.log('📊 Lignes restantes:', $remainingRows.length);

                    if ($remainingRows.length === 0) {
                        console.log('📭 Tableau vide, affichage du message');
                        $tbody.html(`
                            <tr class="empty-message">
                                <td colspan="8" class="text-center text-muted py-4">
                                    <i class="fas fa-inbox fa-3x mb-3 d-block"></i>
                                    Aucune absence trouvée
                                </td>
                            </tr>
                        `);
                    }
                });

                toastr.success(response.message || 'Supprimée avec succès');
            } else {
                console.error('❌ Erreur:', response.error);
                toastr.error(response.error || 'Erreur lors de la suppression');
                $button.prop('disabled', false).html('<i class="fas fa-trash"></i>');
            }
        },
        error: function(xhr) {
            console.error('❌ Erreur AJAX:', xhr);
            console.error('❌ Status:', xhr.status);
            console.error('❌ Response:', xhr.responseJSON);

            const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
            toastr.error(errorMsg);
            $button.prop('disabled', false).html('<i class="fas fa-trash"></i>');
        }
    });
});

    // ========================================
    // FERMETURE MODAL
    // ========================================
    $('#detailModal').on('hidden.bs.modal', function() {
        console.log('✅ Modal fermée');
        $('#detailContent').html(`
            <div class="text-center py-4">
                <div class="spinner-border text-primary"></div>
                <p class="mt-2">Chargement...</p>
            </div>
        `);
    });

    // Test fermeture manuelle
    $(document).on('click', '#detailModal [data-dismiss="modal"]', function() {
        console.log('🔴 Clic sur bouton fermer');
        $('#detailModal').modal('hide');
    });
});

// ========================================
// FONCTIONS UTILITAIRES
// ========================================
function afficherDetails(absence) {
    console.log('📄 Affichage détails:', absence);

    let statutBadge = '';
    if (absence.statut === 'VALIDE') {
        statutBadge = '<span class="badge badge-success"><i class="fas fa-check"></i> Validée</span>';
    } else if (absence.statut === 'REJETE') {
        statutBadge = '<span class="badge badge-danger"><i class="fas fa-times"></i> Rejetée</span>';
    } else if (absence.statut && absence.statut.includes('ATTENTE')) {
        statutBadge = `<span class="badge badge-warning"><i class="fas fa-clock"></i> ${absence.statut_display || 'En attente'}</span>`;
    } else if (absence.statut === 'ANNULE') {
        statutBadge = '<span class="badge badge-dark"><i class="fas fa-ban"></i> Annulée</span>';
    } else {
        statutBadge = `<span class="badge badge-secondary">${absence.statut_display || absence.statut}</span>`;
    }

    const html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <h6><i class="fas fa-user"></i> Employé</h6>
                <p class="font-weight-bold">${absence.employe || 'N/A'}</p>
            </div>
            <div class="col-md-6 text-right">
                <h6><i class="fas fa-info-circle"></i> Statut</h6>
                ${statutBadge}
            </div>
        </div>
        <hr>
        <div class="row mb-3">
            <div class="col-md-6">
                <h6><i class="fas fa-calendar-alt"></i> Type</h6>
                <p>${absence.type_absence || 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-clock"></i> Période</h6>
                <p>${absence.periode || 'Journée complète'}</p>
            </div>
        </div>
        <div class="row mb-3">
            <div class="col-md-4">
                <h6>Début</h6>
                <p><strong>${formatDate(absence.date_debut)}</strong></p>
            </div>
            <div class="col-md-4">
                <h6>Fin</h6>
                <p><strong>${formatDate(absence.date_fin)}</strong></p>
            </div>
            <div class="col-md-4">
                <h6>Durée</h6>
                <p><strong>${absence.jours_ouvrables || 0} jour(s)</strong></p>
            </div>
        </div>
        ${absence.motif ? `
        <div class="row mb-3">
            <div class="col-12">
                <h6><i class="fas fa-comment"></i> Motif</h6>
                <div class="alert alert-light">${absence.motif}</div>
            </div>
        </div>` : ''}
        ${absence.justificatif_url ? `
        <div class="row">
            <div class="col-12">
                <h6><i class="fas fa-paperclip"></i> Justificatif</h6>
                <a href="${absence.justificatif_url}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-download"></i> Télécharger
                </a>
            </div>
        </div>` : ''}
    `;

    $('#detailContent').html(html);
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        return new Date(dateStr).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch {
        return dateStr;
    }
}
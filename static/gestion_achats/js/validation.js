/**
 * JavaScript pour les workflows de validation - Module GAC
 *
 * Fonctionnalités :
 * - Validation des demandes d'achat (N1, N2)
 * - Refus de demandes
 * - Annulation de demandes
 * - Conversion en bon de commande
 */

(function($) {
    'use strict';

    // ========================================
    // VALIDATION N1
    // ========================================

    /**
     * Valider une demande (niveau 1)
     */
    function validerN1(demandeUuid) {
        const commentaire = $('#commentaire-validation-n1').val();

        if (!confirm('Voulez-vous valider cette demande d\'achat ?')) {
            return;
        }

        // Afficher le loader
        $('#btn-valider-n1').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Validation en cours...');

        $.ajax({
            url: `/gestion-achats/demandes/${demandeUuid}/validate-n1/`,
            type: 'POST',
            data: {
                'commentaire': commentaire,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Demande validée avec succès (Niveau 1)');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur lors de la validation');
                    $('#btn-valider-n1').prop('disabled', false).html('<i class="fas fa-check"></i> Valider');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-valider-n1').prop('disabled', false).html('<i class="fas fa-check"></i> Valider');
            }
        });
    }

    // ========================================
    // VALIDATION N2
    // ========================================

    /**
     * Valider une demande (niveau 2)
     */
    function validerN2(demandeUuid) {
        const commentaire = $('#commentaire-validation-n2').val();

        if (!confirm('Voulez-vous valider définitivement cette demande d\'achat ?')) {
            return;
        }

        // Afficher le loader
        $('#btn-valider-n2').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Validation en cours...');

        $.ajax({
            url: `/gestion-achats/demandes/${demandeUuid}/validate-n2/`,
            type: 'POST',
            data: {
                'commentaire': commentaire,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Demande validée avec succès (Niveau 2)');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur lors de la validation');
                    $('#btn-valider-n2').prop('disabled', false).html('<i class="fas fa-check-double"></i> Valider');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-valider-n2').prop('disabled', false).html('<i class="fas fa-check-double"></i> Valider');
            }
        });
    }

    // ========================================
    // REFUS DE DEMANDE
    // ========================================

    /**
     * Refuser une demande
     */
    function refuserDemande(demandeUuid) {
        const motif = $('#motif-refus').val();

        if (!motif || motif.trim() === '') {
            toastr.error('Veuillez saisir un motif de refus');
            return;
        }

        if (!confirm('Voulez-vous vraiment refuser cette demande ?')) {
            return;
        }

        // Afficher le loader
        $('#btn-refuser').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Refus en cours...');

        $.ajax({
            url: `/gestion-achats/demandes/${demandeUuid}/refuse/`,
            type: 'POST',
            data: {
                'motif': motif,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.warning('Demande refusée');
                    $('#modalRefus').modal('hide');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur');
                    $('#btn-refuser').prop('disabled', false).html('<i class="fas fa-times"></i> Refuser');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-refuser').prop('disabled', false).html('<i class="fas fa-times"></i> Refuser');
            }
        });
    }

    // ========================================
    // ANNULATION DE DEMANDE
    // ========================================

    /**
     * Annuler une demande
     */
    function annulerDemande(demandeUuid) {
        const motif = $('#motif-annulation').val();

        if (!motif || motif.trim() === '') {
            toastr.error('Veuillez saisir un motif d\'annulation');
            return;
        }

        if (!confirm('Voulez-vous vraiment annuler cette demande ?')) {
            return;
        }

        // Afficher le loader
        $('#btn-annuler').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Annulation en cours...');

        $.ajax({
            url: `/gestion-achats/demandes/${demandeUuid}/cancel/`,
            type: 'POST',
            data: {
                'motif': motif,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.info('Demande annulée');
                    $('#modalAnnulation').modal('hide');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur');
                    $('#btn-annuler').prop('disabled', false).html('<i class="fas fa-ban"></i> Annuler');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-annuler').prop('disabled', false).html('<i class="fas fa-ban"></i> Annuler');
            }
        });
    }

    // ========================================
    // CONVERSION EN BON DE COMMANDE
    // ========================================

    /**
     * Convertir une demande en bon de commande
     */
    function convertirEnBC(demandeUuid) {
        if (!confirm('Voulez-vous convertir cette demande en bon de commande ?')) {
            return;
        }

        window.location.href = `/gestion-achats/bons-commande/create-from-demande/${demandeUuid}/`;
    }

    // ========================================
    // SOUMISSION DE DEMANDE
    // ========================================

    /**
     * Soumettre une demande pour validation
     */
    function soumettreDemande(demandeUuid) {
        if (!confirm('Voulez-vous soumettre cette demande pour validation ?')) {
            return;
        }

        // Afficher le loader
        $('#btn-soumettre').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Soumission en cours...');

        $.ajax({
            url: `/gestion-achats/demandes/${demandeUuid}/submit/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Demande soumise avec succès');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur');
                    $('#btn-soumettre').prop('disabled', false).html('<i class="fas fa-paper-plane"></i> Soumettre');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-soumettre').prop('disabled', false).html('<i class="fas fa-paper-plane"></i> Soumettre');
            }
        });
    }

    // ========================================
    // AFFICHAGE DES BADGES DE STATUT
    // ========================================

    /**
     * Mettre à jour l'affichage des badges de statut
     */
    function updateStatutBadges() {
        $('.statut-badge').each(function() {
            const statut = $(this).data('statut');

            $(this).removeClass('badge-secondary badge-info badge-primary badge-success badge-danger badge-warning');

            switch (statut) {
                case 'BROUILLON':
                    $(this).addClass('badge-secondary');
                    break;
                case 'SOUMISE':
                    $(this).addClass('badge-info');
                    break;
                case 'VALIDEE_N1':
                    $(this).addClass('badge-primary');
                    break;
                case 'VALIDEE_N2':
                case 'CONVERTIE_BC':
                    $(this).addClass('badge-success');
                    break;
                case 'REFUSEE':
                    $(this).addClass('badge-danger');
                    break;
                case 'ANNULEE':
                    $(this).addClass('badge-warning');
                    break;
            }
        });
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    $(document).ready(function() {

        // Bouton validation N1
        $('#btn-valider-n1').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            validerN1(demandeUuid);
        });

        // Bouton validation N2
        $('#btn-valider-n2').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            validerN2(demandeUuid);
        });

        // Bouton refuser
        $('#btn-refuser').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            refuserDemande(demandeUuid);
        });

        // Bouton annuler
        $('#btn-annuler').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            annulerDemande(demandeUuid);
        });

        // Bouton convertir en BC
        $('#btn-convertir-bc').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            convertirEnBC(demandeUuid);
        });

        // Bouton soumettre
        $('#btn-soumettre').on('click', function(e) {
            e.preventDefault();
            const demandeUuid = $(this).data('demande-uuid');
            soumettreDemande(demandeUuid);
        });

        // Initialiser les badges de statut
        updateStatutBadges();

        // Initialiser tooltips
        $('[data-toggle="tooltip"]').tooltip();

    });

    // Exposer les fonctions globalement pour utilisation depuis templates
    window.GACValidation = {
        validerN1: validerN1,
        validerN2: validerN2,
        refuserDemande: refuserDemande,
        annulerDemande: annulerDemande,
        convertirEnBC: convertirEnBC,
        soumettreDemande: soumettreDemande
    };

})(jQuery);

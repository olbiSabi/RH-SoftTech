/**
 * JavaScript pour la gestion des bons de commande - Module GAC
 *
 * Fonctionnalités :
 * - Génération de PDF
 * - Envoi par email
 * - Gestion des confirmations fournisseur
 * - Suivi des réceptions
 */

(function($) {
    'use strict';

    // ========================================
    // GÉNÉRATION PDF
    // ========================================

    /**
     * Télécharger le PDF du bon de commande
     */
    function telechargerPDF(bcUuid) {
        const url = `/gestion-achats/bons-commande/${bcUuid}/pdf/`;

        // Ouvrir dans un nouvel onglet
        window.open(url, '_blank');
    }

    // ========================================
    // ENVOI EMAIL
    // ========================================

    /**
     * Envoyer le bon de commande par email
     */
    function envoyerBC(bcUuid) {
        const email = $('#email-envoi').val();
        const message = $('#message-envoi').val();

        if (!email) {
            toastr.error('Veuillez saisir une adresse email');
            return;
        }

        // Afficher le loader
        $('#btn-envoyer-bc').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Envoi en cours...');

        $.ajax({
            url: `/gestion-achats/bons-commande/${bcUuid}/send/`,
            type: 'POST',
            data: {
                'email': email,
                'message': message,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Bon de commande envoyé avec succès');
                    $('#modalEnvoi').modal('hide');
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    toastr.error(response.error || 'Erreur lors de l\'envoi');
                    $('#btn-envoyer-bc').prop('disabled', false).html('<i class="fas fa-paper-plane"></i> Envoyer');
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Erreur serveur';
                toastr.error(errorMsg);
                $('#btn-envoyer-bc').prop('disabled', false).html('<i class="fas fa-paper-plane"></i> Envoyer');
            }
        });
    }

    // ========================================
    // CONFIRMATION FOURNISSEUR
    // ========================================

    /**
     * Enregistrer la confirmation fournisseur
     */
    function confirmerBC(bcUuid) {
        const numeroConfirmation = $('#numero-confirmation').val();
        const dateLivraison = $('#date-livraison-confirmee').val();

        if (!numeroConfirmation) {
            toastr.error('Veuillez saisir le numéro de confirmation');
            return;
        }

        $.ajax({
            url: `/gestion-achats/bons-commande/${bcUuid}/confirmer/`,
            type: 'POST',
            data: {
                'numero_confirmation': numeroConfirmation,
                'date_livraison_confirmee': dateLivraison,
                'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    toastr.success('Confirmation enregistrée avec succès');
                    location.reload();
                } else {
                    toastr.error(response.error || 'Erreur');
                }
            },
            error: function() {
                toastr.error('Erreur lors de l\'enregistrement');
            }
        });
    }

    // ========================================
    // SUIVI DES RÉCEPTIONS
    // ========================================

    /**
     * Afficher les détails de réception d'une ligne
     */
    function afficherReceptions(ligneUuid) {
        $.ajax({
            url: `/gestion-achats/api/ligne-bc/${ligneUuid}/receptions/`,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    const receptions = response.receptions;

                    let html = '<table class="table table-sm">';
                    html += '<thead><tr><th>Date</th><th>Réception</th><th>Qté reçue</th><th>Qté acceptée</th><th>Statut</th></tr></thead>';
                    html += '<tbody>';

                    receptions.forEach(function(reception) {
                        html += '<tr>';
                        html += `<td>${reception.date}</td>`;
                        html += `<td><a href="/gestion-achats/receptions/${reception.uuid}/">${reception.numero}</a></td>`;
                        html += `<td>${reception.quantite_recue}</td>`;
                        html += `<td>${reception.quantite_acceptee}</td>`;
                        html += `<td><span class="badge badge-${reception.badge_class}">${reception.statut}</span></td>`;
                        html += '</tr>';
                    });

                    html += '</tbody></table>';

                    $('#receptions-content').html(html);
                    $('#modalReceptions').modal('show');
                } else {
                    toastr.error('Erreur lors du chargement');
                }
            },
            error: function() {
                toastr.error('Erreur lors du chargement des réceptions');
            }
        });
    }

    // ========================================
    // VISUALISATION DES MONTANTS
    // ========================================

    /**
     * Mettre à jour les barres de progression de réception
     */
    function updateProgressBars() {
        $('.progress-reception').each(function() {
            const $bar = $(this).find('.progress-bar');
            const quantiteCommandee = parseFloat($(this).data('commandee'));
            const quantiteRecue = parseFloat($(this).data('recue'));

            const pourcentage = (quantiteRecue / quantiteCommandee) * 100;

            $bar.css('width', pourcentage + '%');
            $bar.attr('aria-valuenow', pourcentage);
            $bar.text(pourcentage.toFixed(0) + '%');

            // Couleur selon le pourcentage
            if (pourcentage >= 100) {
                $bar.removeClass('bg-warning bg-info').addClass('bg-success');
            } else if (pourcentage >= 50) {
                $bar.removeClass('bg-success bg-info').addClass('bg-warning');
            } else {
                $bar.removeClass('bg-success bg-warning').addClass('bg-info');
            }
        });
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    $(document).ready(function() {

        // Bouton télécharger PDF
        $('#btn-telecharger-pdf').on('click', function(e) {
            e.preventDefault();
            const bcUuid = $(this).data('bc-uuid');
            telechargerPDF(bcUuid);
        });

        // Bouton envoyer BC
        $('#btn-envoyer-bc').on('click', function(e) {
            e.preventDefault();
            const bcUuid = $(this).data('bc-uuid');
            envoyerBC(bcUuid);
        });

        // Bouton confirmer BC
        $('#btn-confirmer-bc').on('click', function(e) {
            e.preventDefault();
            const bcUuid = $(this).data('bc-uuid');
            confirmerBC(bcUuid);
        });

        // Bouton afficher réceptions d'une ligne
        $('.btn-afficher-receptions').on('click', function(e) {
            e.preventDefault();
            const ligneUuid = $(this).data('ligne-uuid');
            afficherReceptions(ligneUuid);
        });

        // Initialiser les barres de progression
        updateProgressBars();

        // Recharger l'email du fournisseur dans le modal d'envoi
        $('#modalEnvoi').on('show.bs.modal', function() {
            const emailFournisseur = $(this).data('email-fournisseur');
            if (emailFournisseur) {
                $('#email-envoi').val(emailFournisseur);
            }
        });

        // Initialiser tooltips
        $('[data-toggle="tooltip"]').tooltip();

        // Initialiser les datepickers
        if ($.fn.datepicker) {
            $('.datepicker').datepicker({
                format: 'yyyy-mm-dd',
                language: 'fr',
                autoclose: true,
                todayHighlight: true
            });
        }

    });

})(jQuery);

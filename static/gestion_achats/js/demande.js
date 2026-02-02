/**
 * JavaScript pour la gestion des demandes d'achat - Module GAC
 *
 * Fonctionnalités :
 * - Gestion dynamique des lignes de demande
 * - Calcul automatique des totaux
 * - Validation côté client
 * - Recherche d'articles
 */

(function($) {
    'use strict';

    // ========================================
    // VARIABLES GLOBALES
    // ========================================

    let ligneCounter = 0;

    // ========================================
    // GESTION DES LIGNES DE DEMANDE
    // ========================================

    /**
     * Ajouter une ligne de demande
     */
    function ajouterLigne() {
        ligneCounter++;

        const $lignesTable = $('#lignes-demande tbody');

        const ligneHTML = `
            <tr id="ligne-${ligneCounter}" data-ligne-id="${ligneCounter}">
                <td>
                    <select name="article_${ligneCounter}" id="article_${ligneCounter}"
                            class="form-control article-select" required>
                        <option value="">Sélectionner un article...</option>
                    </select>
                </td>
                <td>
                    <input type="number" name="quantite_${ligneCounter}" id="quantite_${ligneCounter}"
                           class="form-control quantite-input" min="0.01" step="0.01" required>
                </td>
                <td>
                    <input type="number" name="prix_unitaire_${ligneCounter}" id="prix_unitaire_${ligneCounter}"
                           class="form-control prix-input" min="0" step="0.01" readonly>
                </td>
                <td>
                    <input type="number" name="taux_tva_${ligneCounter}" id="taux_tva_${ligneCounter}"
                           class="form-control tva-input" min="0" max="100" step="0.01" readonly>
                </td>
                <td>
                    <span class="montant-ht" id="montant_ht_${ligneCounter}">0.00 €</span>
                </td>
                <td>
                    <span class="montant-ttc" id="montant_ttc_${ligneCounter}">0.00 €</span>
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger btn-supprimer-ligne"
                            data-ligne-id="${ligneCounter}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;

        $lignesTable.append(ligneHTML);

        // Charger les articles dans le select
        chargerArticles(ligneCounter);

        // Recalculer les totaux
        calculerTotaux();
    }

    /**
     * Supprimer une ligne de demande
     */
    function supprimerLigne(ligneId) {
        $(`#ligne-${ligneId}`).remove();
        calculerTotaux();
    }

    /**
     * Charger la liste des articles dans un select
     */
    function chargerArticles(ligneId) {
        const $select = $(`#article_${ligneId}`);

        $.ajax({
            url: '/gestion-achats/api/articles/recherche/',
            type: 'GET',
            data: { limit: 100 },
            success: function(response) {
                if (response.success) {
                    response.articles.forEach(function(article) {
                        $select.append(
                            `<option value="${article.uuid}"
                                     data-prix="${article.prix_unitaire}"
                                     data-tva="${article.taux_tva}">
                                ${article.reference} - ${article.designation}
                            </option>`
                        );
                    });
                }
            },
            error: function() {
                toastr.error('Erreur lors du chargement des articles');
            }
        });
    }

    // ========================================
    // CALCULS
    // ========================================

    /**
     * Calculer le montant d'une ligne
     */
    function calculerLigne(ligneId) {
        const quantite = parseFloat($(`#quantite_${ligneId}`).val()) || 0;
        const prixUnitaire = parseFloat($(`#prix_unitaire_${ligneId}`).val()) || 0;
        const tauxTva = parseFloat($(`#taux_tva_${ligneId}`).val()) || 0;

        const montantHT = quantite * prixUnitaire;
        const montantTVA = montantHT * (tauxTva / 100);
        const montantTTC = montantHT + montantTVA;

        $(`#montant_ht_${ligneId}`).text(montantHT.toFixed(2) + ' €');
        $(`#montant_ttc_${ligneId}`).text(montantTTC.toFixed(2) + ' €');

        return { montantHT, montantTVA, montantTTC };
    }

    /**
     * Calculer les totaux de la demande
     */
    function calculerTotaux() {
        let totalHT = 0;
        let totalTVA = 0;
        let totalTTC = 0;

        $('#lignes-demande tbody tr').each(function() {
            const ligneId = $(this).data('ligne-id');
            const montants = calculerLigne(ligneId);

            totalHT += montants.montantHT;
            totalTVA += montants.montantTVA;
            totalTTC += montants.montantTTC;
        });

        $('#total-ht').text(totalHT.toFixed(2) + ' €');
        $('#total-tva').text(totalTVA.toFixed(2) + ' €');
        $('#total-ttc').text(totalTTC.toFixed(2) + ' €');
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    $(document).ready(function() {

        // Bouton ajouter une ligne
        $('#btn-ajouter-ligne').on('click', function(e) {
            e.preventDefault();
            ajouterLigne();
        });

        // Bouton supprimer une ligne
        $(document).on('click', '.btn-supprimer-ligne', function(e) {
            e.preventDefault();
            const ligneId = $(this).data('ligne-id');
            supprimerLigne(ligneId);
        });

        // Sélection d'un article
        $(document).on('change', '.article-select', function() {
            const ligneId = $(this).closest('tr').data('ligne-id');
            const $option = $(this).find('option:selected');

            const prix = $option.data('prix');
            const tva = $option.data('tva');

            $(`#prix_unitaire_${ligneId}`).val(prix);
            $(`#taux_tva_${ligneId}`).val(tva);

            calculerLigne(ligneId);
            calculerTotaux();
        });

        // Changement de quantité
        $(document).on('input', '.quantite-input', function() {
            const ligneId = $(this).closest('tr').data('ligne-id');
            calculerLigne(ligneId);
            calculerTotaux();
        });

        // Changement de prix unitaire (si éditable)
        $(document).on('input', '.prix-input', function() {
            const ligneId = $(this).closest('tr').data('ligne-id');
            calculerLigne(ligneId);
            calculerTotaux();
        });

        // Validation du formulaire
        $('#form-demande').on('submit', function(e) {
            // Vérifier qu'il y a au moins une ligne
            const nbLignes = $('#lignes-demande tbody tr').length;
            if (nbLignes === 0) {
                e.preventDefault();
                toastr.error('Vous devez ajouter au moins une ligne à la demande');
                return false;
            }

            return true;
        });

        // Initialiser tooltips
        $('[data-toggle="tooltip"]').tooltip();

    });

})(jQuery);

/**
 * JavaScript pour la gestion des budgets - Module GAC
 *
 * Fonctionnalités :
 * - Affichage temps réel des alertes budgétaires
 * - Calcul et visualisation des consommations
 * - Graphiques de suivi budgétaire
 * - Notifications d'alerte
 */

(function($) {
    'use strict';

    // ========================================
    // VARIABLES GLOBALES
    // ========================================

    let alertesPollingInterval = null;

    // ========================================
    // VISUALISATION DES BUDGETS
    // ========================================

    /**
     * Mettre à jour les barres de progression budgétaire
     */
    function updateProgressBars() {
        $('.budget-progress').each(function() {
            const $bar = $(this).find('.progress-bar');
            const montantInitial = parseFloat($(this).data('initial'));
            const montantConsomme = parseFloat($(this).data('consomme'));
            const seuil1 = parseFloat($(this).data('seuil1') || 70);
            const seuil2 = parseFloat($(this).data('seuil2') || 90);

            const pourcentage = (montantConsomme / montantInitial) * 100;

            $bar.css('width', pourcentage + '%');
            $bar.attr('aria-valuenow', pourcentage);
            $bar.text(pourcentage.toFixed(1) + '%');

            // Couleur selon le pourcentage et les seuils
            $bar.removeClass('bg-success bg-info bg-warning bg-danger');

            if (pourcentage >= seuil2) {
                $bar.addClass('bg-danger');
            } else if (pourcentage >= seuil1) {
                $bar.addClass('bg-warning');
            } else if (pourcentage >= 50) {
                $bar.addClass('bg-info');
            } else {
                $bar.addClass('bg-success');
            }

            // Ajouter une classe d'alerte si dépassement
            if (pourcentage >= seuil2) {
                $(this).closest('.budget-card').addClass('border-danger');
            } else if (pourcentage >= seuil1) {
                $(this).closest('.budget-card').addClass('border-warning');
            }
        });
    }

    /**
     * Formater un montant en euros
     */
    function formatMontant(montant) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(montant);
    }

    /**
     * Mettre à jour l'affichage des montants
     */
    function updateMontants() {
        $('.montant-display').each(function() {
            const montant = parseFloat($(this).data('montant'));
            $(this).text(formatMontant(montant));
        });
    }

    // ========================================
    // ALERTES BUDGÉTAIRES
    // ========================================

    /**
     * Récupérer les budgets en alerte
     */
    function chargerBudgetsEnAlerte() {
        $.ajax({
            url: '/gestion-achats/api/budgets/alertes/',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    afficherAlertes(response.budgets);
                }
            },
            error: function() {
                console.error('Erreur lors du chargement des alertes budgétaires');
            }
        });
    }

    /**
     * Afficher les alertes budgétaires
     */
    function afficherAlertes(budgets) {
        const $container = $('#alertes-budgets');

        if (!$container.length) {
            return;
        }

        $container.empty();

        if (budgets.length === 0) {
            $container.html('<p class="text-muted">Aucune alerte budgétaire</p>');
            return;
        }

        budgets.forEach(function(budget) {
            const alertClass = budget.taux_consommation >= 90 ? 'alert-danger' : 'alert-warning';
            const icon = budget.taux_consommation >= 90 ? 'fa-exclamation-triangle' : 'fa-exclamation-circle';

            const html = `
                <div class="alert ${alertClass} d-flex align-items-center" role="alert">
                    <i class="fas ${icon} mr-3"></i>
                    <div class="flex-grow-1">
                        <strong>${budget.code} - ${budget.libelle}</strong><br>
                        <small>Consommation : ${budget.taux_consommation.toFixed(1)}%</small>
                        <small class="ml-3">Disponible : ${formatMontant(budget.montant_disponible)}</small>
                    </div>
                    <a href="/gestion-achats/budgets/${budget.uuid}/" class="btn btn-sm btn-outline-dark">
                        <i class="fas fa-eye"></i> Voir
                    </a>
                </div>
            `;

            $container.append(html);
        });

        // Afficher une notification si nouvelle alerte
        if (budgets.length > 0 && typeof toastr !== 'undefined') {
            const nbAlertes = budgets.length;
            toastr.warning(
                `${nbAlertes} budget${nbAlertes > 1 ? 's' : ''} en alerte`,
                'Alerte budgétaire',
                { timeOut: 0, extendedTimeOut: 0, closeButton: true }
            );
        }
    }

    /**
     * Démarrer le polling des alertes
     */
    function startAlertesPolling(intervalMs) {
        intervalMs = intervalMs || 300000; // 5 minutes par défaut

        // Charger immédiatement
        chargerBudgetsEnAlerte();

        // Puis polling régulier
        alertesPollingInterval = setInterval(function() {
            chargerBudgetsEnAlerte();
        }, intervalMs);
    }

    /**
     * Arrêter le polling des alertes
     */
    function stopAlertesPolling() {
        if (alertesPollingInterval) {
            clearInterval(alertesPollingInterval);
            alertesPollingInterval = null;
        }
    }

    // ========================================
    // GRAPHIQUES
    // ========================================

    /**
     * Créer un graphique de consommation budgétaire
     */
    function creerGraphiqueConsommation(canvasId, data) {
        const ctx = document.getElementById(canvasId);

        if (!ctx || typeof Chart === 'undefined') {
            return;
        }

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Engagé', 'Commandé', 'Consommé', 'Disponible'],
                datasets: [{
                    data: [
                        data.montant_engage,
                        data.montant_commande,
                        data.montant_consomme,
                        data.montant_disponible
                    ],
                    backgroundColor: [
                        '#ffc107', // Engagé - jaune
                        '#17a2b8', // Commandé - cyan
                        '#dc3545', // Consommé - rouge
                        '#28a745'  // Disponible - vert
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    position: 'bottom'
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            const label = data.labels[tooltipItem.index] || '';
                            const value = data.datasets[0].data[tooltipItem.index];
                            return label + ': ' + formatMontant(value);
                        }
                    }
                }
            }
        });
    }

    /**
     * Créer un graphique d'évolution temporelle
     */
    function creerGraphiqueEvolution(canvasId, data) {
        const ctx = document.getElementById(canvasId);

        if (!ctx || typeof Chart === 'undefined') {
            return;
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Montant consommé',
                    data: data.values,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatMontant(value);
                            }
                        }
                    }
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem) {
                            return formatMontant(tooltipItem.yLabel);
                        }
                    }
                }
            }
        });
    }

    // ========================================
    // FILTRES ET RECHERCHE
    // ========================================

    /**
     * Filtrer les budgets par exercice
     */
    function filtrerParExercice(exercice) {
        const url = new URL(window.location);
        url.searchParams.set('exercice', exercice);
        window.location.href = url.toString();
    }

    /**
     * Rechercher un budget
     */
    function rechercherBudget(query) {
        const url = new URL(window.location);
        url.searchParams.set('search', query);
        window.location.href = url.toString();
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    $(document).ready(function() {

        // Initialiser les barres de progression
        updateProgressBars();

        // Formater les montants
        updateMontants();

        // Démarrer le polling des alertes sur la page dashboard
        if ($('#alertes-budgets').length) {
            startAlertesPolling();
        }

        // Filtrer par exercice
        $('#filtre-exercice').on('change', function() {
            const exercice = $(this).val();
            filtrerParExercice(exercice);
        });

        // Recherche
        $('#btn-rechercher-budget').on('click', function(e) {
            e.preventDefault();
            const query = $('#search-budget').val();
            rechercherBudget(query);
        });

        // Recherche au clavier (Entrée)
        $('#search-budget').on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                const query = $(this).val();
                rechercherBudget(query);
            }
        });

        // Créer les graphiques si présents
        if ($('#graphique-consommation').length) {
            const data = $('#graphique-consommation').data('budget-data');
            if (data) {
                creerGraphiqueConsommation('graphique-consommation', data);
            }
        }

        if ($('#graphique-evolution').length) {
            const data = $('#graphique-evolution').data('evolution-data');
            if (data) {
                creerGraphiqueEvolution('graphique-evolution', data);
            }
        }

        // Initialiser tooltips
        $('[data-toggle="tooltip"]').tooltip();

        // Nettoyer le polling à la fermeture de la page
        $(window).on('beforeunload', function() {
            stopAlertesPolling();
        });

    });

    // Exposer les fonctions globalement
    window.GACBudget = {
        updateProgressBars: updateProgressBars,
        chargerBudgetsEnAlerte: chargerBudgetsEnAlerte,
        startAlertesPolling: startAlertesPolling,
        stopAlertesPolling: stopAlertesPolling,
        formatMontant: formatMontant
    };

})(jQuery);

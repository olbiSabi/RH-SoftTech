// static/assets/js/gta/modal-commentaires.js - VERSION BOOTSTRAP 4

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initModalesCommentaires();
    });

    function initModalesCommentaires() {
        console.log('Initialisation des modales commentaires (Bootstrap 4)...');

        // Gestionnaire de soumission pour modification
        const formModifier = document.getElementById('formModifierCommentaire');
        if (formModifier) {
            formModifier.addEventListener('submit', function(e) {
                e.preventDefault();
                soumettreModificationCommentaire();
            });
        }

        // Gestionnaire de soumission pour suppression
        const formSupprimer = document.getElementById('formSupprimerCommentaire');
        if (formSupprimer) {
            formSupprimer.addEventListener('submit', function(e) {
                e.preventDefault();
                soumettreSuppressionCommentaire();
            });
        }

        // Compteur de caractères
        const textarea = document.getElementById('commentaire_contenu_modifier');
        if (textarea) {
            textarea.addEventListener('input', function() {
                const restants = 1000 - this.value.length;
                document.getElementById('caracteres_restants').textContent = restants;
            });
        }
    }

    // ==================== MODAL MODIFICATION ====================

    window.ouvrirModalModifier = function(commentaireId, contenu) {
        console.log('Ouverture modal modification:', commentaireId);

        // Remplir le formulaire
        document.getElementById('commentaire_id_modifier').value = commentaireId;
        document.getElementById('commentaire_contenu_modifier').value = contenu;

        // Mettre à jour le compteur
        const restants = 1000 - contenu.length;
        document.getElementById('caracteres_restants').textContent = restants;

        // Ouvrir la modale (Bootstrap 4 avec jQuery)
        $('#modalModifierCommentaire').modal('show');
    };

    function soumettreModificationCommentaire() {
    const commentaireId = document.getElementById('commentaire_id_modifier').value;
    const contenu = document.getElementById('commentaire_contenu_modifier').value.trim();

    if (!contenu || contenu.length < 2) {
        alert('Le commentaire doit contenir au moins 2 caractères.');
        return;
    }

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    formData.append('contenu', contenu);

    fetch(`/gestion-temps/commentaires/${commentaireId}/modifier/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#modalModifierCommentaire').modal('hide');

            window.location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Une erreur est survenue'));
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('❌ Erreur lors de la modification du commentaire.');
    });
}

    // ==================== MODAL SUPPRESSION ====================

    window.ouvrirModalSupprimer = function(commentaireId, contenu, nbReponses) {
        console.log('Ouverture modal suppression:', commentaireId);

        document.getElementById('commentaire_id_supprimer').value = commentaireId;

        let apercu = contenu.length > 200 ? contenu.substring(0, 200) + '...' : contenu;
        document.getElementById('commentaire_apercu_suppression').textContent = apercu;

        const avertissement = document.getElementById('avertissement_reponses');
        if (nbReponses > 0) {
            avertissement.style.display = 'block';
        } else {
            avertissement.style.display = 'none';
        }

        // Ouvrir la modale (Bootstrap 4 avec jQuery)
        $('#modalSupprimerCommentaire').modal('show');
    };

    function soumettreSuppressionCommentaire() {
    const commentaireId = document.getElementById('commentaire_id_supprimer').value;

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCsrfToken());

    fetch(`/gestion-temps/commentaires/${commentaireId}/supprimer/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#modalSupprimerCommentaire').modal('hide');

            window.location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Une erreur est survenue'));
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('❌ Erreur lors de la suppression du commentaire.');
    });
}

    // ==================== UTILITAIRES ====================

    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    function afficherMessage(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

})();
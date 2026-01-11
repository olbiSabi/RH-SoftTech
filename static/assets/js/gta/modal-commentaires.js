// static/assets/js/gta/modal-commentaires.js - VERSION BOOTSTRAP 4
// 🔍 DEBUG : Vérifier que le modal est présent au chargement
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        console.log('=== VÉRIFICATION DES MODALES ===');
        console.log('Modal Répondre:', document.getElementById('modalRepondreCommentaire'));
        console.log('Input Parent:', document.getElementById('commentaire_parent_id'));
        console.log('Auteur:', document.getElementById('auteur_commentaire_parent'));
        console.log('Textarea:', document.getElementById('reponse_contenu'));
        console.log('Counter:', document.getElementById('reponse_caracteres_restants'));
    }, 1000);
});


(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initModalesCommentaires();
    });

    function initModalesCommentaires() {
    console.log('Initialisation des modales commentaires (Bootstrap 4)...');

    // Vérifier que les modales existent
    const modalModifier = document.getElementById('modalModifierCommentaire');
    const modalSupprimer = document.getElementById('modalSupprimerCommentaire');
    const modalRepondre = document.getElementById('modalRepondreCommentaire');

    if (!modalModifier) {
        console.error('❌ Modal modalModifierCommentaire non trouvée !');
    }
    if (!modalSupprimer) {
        console.error('❌ Modal modalSupprimerCommentaire non trouvée !');
    }
    if (!modalRepondre) {
        console.error('❌ Modal modalRepondreCommentaire non trouvée !');
    }

    // ✅ AJOUT : S'assurer que le modal reste attaché au body
    if (modalRepondre) {
        $('#modalRepondreCommentaire').on('hidden.bs.modal', function () {
            console.log('Modal réponse fermé - prêt pour réouverture');
        });
    }

    // Gestionnaire modification
    const formModifier = document.getElementById('formModifierCommentaire');
    if (formModifier) {
        formModifier.addEventListener('submit', function(e) {
            e.preventDefault();
            soumettreModificationCommentaire();
        });
    }

    // Gestionnaire suppression
    const formSupprimer = document.getElementById('formSupprimerCommentaire');
    if (formSupprimer) {
        formSupprimer.addEventListener('submit', function(e) {
            e.preventDefault();
            soumettreSuppressionCommentaire();
        });
    }

    // Gestionnaire réponse
    const formRepondre = document.getElementById('formRepondreCommentaire');
    if (formRepondre) {
        formRepondre.addEventListener('submit', function(e) {
            e.preventDefault();
            soumettreReponseCommentaire();
        });
    }

    // Compteur de caractères pour modification
    const textarea = document.getElementById('commentaire_contenu_modifier');
    if (textarea) {
        textarea.addEventListener('input', function() {
            const restants = 1000 - this.value.length;
            const counterElement = document.getElementById('caracteres_restants');
            if (counterElement) {
                counterElement.textContent = restants;
            }
        });
    }

    // Compteur de caractères pour réponse
    const textareaReponse = document.getElementById('reponse_contenu');
    if (textareaReponse) {
        textareaReponse.addEventListener('input', function() {
            const restants = 1000 - this.value.length;
            const counterElement = document.getElementById('reponse_caracteres_restants');
            if (counterElement) {
                counterElement.textContent = restants;
            }
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

    // ==================== MODAL RÉPONSE ====================

    // ==================== MODAL RÉPONSE ====================

    // ==================== MODAL RÉPONSE ====================

    window.ouvrirModalRepondre = function(commentaireId, auteurNom) {
    console.log('Ouverture modal réponse pour commentaire:', commentaireId);

    const idInput = document.getElementById('commentaire_parent_id');
    const textarea = document.getElementById('reponse_contenu');
    const counterElement = document.getElementById('reponse_caracteres_restants');
    const modalBody = document.querySelector('#modalRepondreCommentaire .modal-body');

    if (!idInput || !textarea || !modalBody) {
        console.error('❌ Éléments critiques du modal non trouvés !');
        alert('Erreur : Le formulaire de réponse n\'est pas disponible. Veuillez recharger la page.');
        return;
    }

    // ✅ SOLUTION ROBUSTE : Toujours recréer l'alerte avec l'auteur
    const alertDiv = modalBody.querySelector('.alert-light');
    if (alertDiv) {
        alertDiv.innerHTML = `
            <i class="fas fa-info-circle"></i>
            Vous répondez au commentaire de <strong>${auteurNom}</strong>
        `;
    }

    // Remplir le formulaire
    idInput.value = commentaireId;
    textarea.value = '';

    if (counterElement) {
        counterElement.textContent = '1000';
    }

    // Ouvrir la modale (Bootstrap 4)
    $('#modalRepondreCommentaire').modal('show');
};

    function soumettreReponseCommentaire() {
    const commentaireParentId = document.getElementById('commentaire_parent_id').value;
    const contenu = document.getElementById('reponse_contenu').value.trim();

    if (!contenu || contenu.length < 2) {
        alert('La réponse doit contenir au moins 2 caractères.');
        return;
    }

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    formData.append('contenu', contenu);

    fetch(`/gestion-temps/commentaires/${commentaireParentId}/repondre/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Fermer la modale (Bootstrap 4)
            $('#modalRepondreCommentaire').modal('hide');

            // Recharger la page
            window.location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Une erreur est survenue'));
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('❌ Erreur lors de l\'envoi de la réponse.');
    });
}

})();
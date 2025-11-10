let contratModal;
        let deleteModal;

        document.addEventListener('DOMContentLoaded', function() {
            contratModal = new bootstrap.Modal(document.getElementById('contratModal'));
            deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));

            // Soumettre le formulaire
            document.getElementById('contratForm').addEventListener('submit', function(e) {
                e.preventDefault();
                saveContrat();
            });
        });

        // Ouvrir le modal (création ou modification)
        function openContratModal(id = null, type = '', dateDebut = '', dateFin = '') {
            const form = document.getElementById('contratForm');
            const modalTitle = document.getElementById('modalTitle');
            const errorMessage = document.getElementById('errorMessage');

            // Réinitialiser le formulaire
            form.reset();
            errorMessage.classList.add('d-none');

            if (id) {
                // Mode modification
                modalTitle.textContent = 'Modifier le contrat';
                document.getElementById('contratId').value = id;
                document.getElementById('typeContrat').value = type;
                document.getElementById('dateDebut').value = dateDebut;
                document.getElementById('dateFin').value = dateFin;
            } else {
                // Mode création
                modalTitle.textContent = 'Ajouter un contrat';
                document.getElementById('contratId').value = '';
            }

            contratModal.show();
        }

        // Confirmer la suppression
        function confirmDeleteContrat(id, type, dateDebut) {
            document.getElementById('deleteContratId').value = id;
            document.getElementById('deleteMessage').textContent =
                `Voulez-vous vraiment supprimer le contrat ${type} du ${dateDebut} ?`;
            deleteModal.show();
        }

        // Supprimer le contrat
        function deleteContrat() {
            const contratId = document.getElementById('deleteContratId').value;

            fetch(`/employe/contrat/${contratId}/supprimer-ajax/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    deleteModal.hide();
                    window.location.reload();
                } else {
                    alert('Erreur : ' + (data.error || 'Impossible de supprimer le contrat'));
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Erreur de connexion au serveur');
            });
        }

        // Enregistrer le contrat (AJAX)
        function saveContrat() {
            const form = document.getElementById('contratForm');
            const formData = new FormData(form);
            const contratId = document.getElementById('contratId').value;
            const errorMessage = document.getElementById('errorMessage');

            // Validation des dates
            const dateDebut = document.getElementById('dateDebut').value;
            const dateFin = document.getElementById('dateFin').value;

            if (dateFin && dateFin <= dateDebut) {
                errorMessage.textContent = 'La date de fin doit être supérieure à la date de début';
                errorMessage.classList.remove('d-none');
                return;
            }

            // URL selon création ou modification
            const url = contratId ?
                `/employe/contrat/${contratId}/modifier-ajax/` :
                '/employe/contrat/nouveau-ajax/';

            // Envoi AJAX
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    contratModal.hide();
                    window.location.reload();
                } else {
                    errorMessage.textContent = data.error || 'Une erreur est survenue';
                    errorMessage.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                errorMessage.textContent = 'Erreur de connexion au serveur';
                errorMessage.classList.remove('d-none');
            });
        }


<!-- ========================================== -->
<!-- JAVASCRIPT POUR TOUS LES MODALS -->
<!-- ========================================== -->

// ===== VARIABLES GLOBALES =====
let affectationModal, deleteAffectationModal;
let telephoneModal, deleteTelephoneModal;
let emailModal, deleteEmailModal;
let adresseModal, deleteAdresseModal;

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser tous les modals
    affectationModal = new bootstrap.Modal(document.getElementById('affectationModal'));
    deleteAffectationModal = new bootstrap.Modal(document.getElementById('deleteAffectationModal'));
    telephoneModal = new bootstrap.Modal(document.getElementById('telephoneModal'));
    deleteTelephoneModal = new bootstrap.Modal(document.getElementById('deleteTelephoneModal'));
    emailModal = new bootstrap.Modal(document.getElementById('emailModal'));
    deleteEmailModal = new bootstrap.Modal(document.getElementById('deleteEmailModal'));
    adresseModal = new bootstrap.Modal(document.getElementById('adresseModal'));
    deleteAdresseModal = new bootstrap.Modal(document.getElementById('deleteAdresseModal'));

    // Soumettre les formulaires
    document.getElementById('affectationForm').addEventListener('submit', e => { e.preventDefault(); saveAffectation(); });
    document.getElementById('telephoneForm').addEventListener('submit', e => { e.preventDefault(); saveTelephone(); });
    document.getElementById('emailForm').addEventListener('submit', e => { e.preventDefault(); saveEmail(); });
    document.getElementById('adresseForm').addEventListener('submit', e => { e.preventDefault(); saveAdresse(); });
});


// ===== FONCTIONS AFFECTATION =====
function openAffectationModal(id = null, posteId = '', dateDebut = '', dateFin = '') {
    document.getElementById('affectationForm').reset();
    document.getElementById('affectationError').classList.add('d-none');
    document.getElementById('affectationModalTitle').textContent = id ? 'Modifier l\'affectation' : 'Ajouter une affectation';

    if (id) {
        document.getElementById('affectationId').value = id;
        document.getElementById('affectationPoste').value = posteId;
        document.getElementById('affectationDateDebut').value = dateDebut;
        document.getElementById('affectationDateFin').value = dateFin;
    }

    affectationModal.show();
}

function saveAffectation() {
    const formData = new FormData(document.getElementById('affectationForm'));
    const affectationId = document.getElementById('affectationId').value;
    const url = affectationId ?
        `/employe/affectation/${affectationId}/modifier-ajax/` :
        '/employe/affectation/nouveau-ajax/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            affectationModal.hide();
            window.location.reload();
        } else {
            document.getElementById('affectationError').textContent = data.error;
            document.getElementById('affectationError').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('affectationError').textContent = 'Erreur de connexion au serveur';
        document.getElementById('affectationError').classList.remove('d-none');
    });
}

function confirmDeleteAffectation(id, poste) {
    document.getElementById('deleteAffectationId').value = id;
    document.getElementById('deleteAffectationMessage').textContent = `Supprimer l'affectation "${poste}" ?`;
    deleteAffectationModal.show();
}

function deleteAffectation() {
    const id = document.getElementById('deleteAffectationId').value;
    fetch(`/employe/affectation/${id}/supprimer-ajax/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            deleteAffectationModal.hide();
            window.location.reload();
        } else {
            alert('Erreur : ' + data.error);
        }
    });
}


// ===== FONCTIONS TÉLÉPHONE =====
function openTelephoneModal(id = null, numero = '', dateDebut = '', dateFin = '') {
    document.getElementById('telephoneForm').reset();
    document.getElementById('telephoneError').classList.add('d-none');
    document.getElementById('telephoneModalTitle').textContent = id ? 'Modifier le téléphone' : 'Ajouter un téléphone';

    if (id) {
        document.getElementById('telephoneId').value = id;
        document.getElementById('telephoneNumero').value = numero;
        document.getElementById('telephoneDateDebut').value = dateDebut;
        document.getElementById('telephoneDateFin').value = dateFin;
    }

    telephoneModal.show();
}

function saveTelephone() {
    const formData = new FormData(document.getElementById('telephoneForm'));
    const telephoneId = document.getElementById('telephoneId').value;
    const url = telephoneId ?
        `/employe/telephone/${telephoneId}/modifier-ajax/` :
        '/employe/telephone/nouveau-ajax/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            telephoneModal.hide();
            window.location.reload();
        } else {
            document.getElementById('telephoneError').textContent = data.error;
            document.getElementById('telephoneError').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('telephoneError').textContent = 'Erreur de connexion au serveur';
        document.getElementById('telephoneError').classList.remove('d-none');
    });
}

function confirmDeleteTelephone(id, numero) {
    document.getElementById('deleteTelephoneId').value = id;
    document.getElementById('deleteTelephoneMessage').textContent = `Supprimer le numéro "${numero}" ?`;
    deleteTelephoneModal.show();
}

function deleteTelephone() {
    const id = document.getElementById('deleteTelephoneId').value;
    fetch(`/employe/telephone/${id}/supprimer-ajax/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            deleteTelephoneModal.hide();
            window.location.reload();
        } else {
            alert('Erreur : ' + data.error);
        }
    });
}


// ===== FONCTIONS EMAIL =====
function openEmailModal(id = null, email = '', dateDebut = '', dateFin = '') {
    document.getElementById('emailForm').reset();
    document.getElementById('emailError').classList.add('d-none');
    document.getElementById('emailModalTitle').textContent = id ? 'Modifier l\'email' : 'Ajouter un email';

    if (id) {
        document.getElementById('emailId').value = id;
        document.getElementById('emailAdresse').value = email;
        document.getElementById('emailDateDebut').value = dateDebut;
        document.getElementById('emailDateFin').value = dateFin;
    }

    emailModal.show();
}

function saveEmail() {
    const formData = new FormData(document.getElementById('emailForm'));
    const emailId = document.getElementById('emailId').value;
    const url = emailId ?
        `/employe/email/${emailId}/modifier-ajax/` :
        '/employe/email/nouveau-ajax/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            emailModal.hide();
            window.location.reload();
        } else {
            document.getElementById('emailError').textContent = data.error;
            document.getElementById('emailError').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('emailError').textContent = 'Erreur de connexion au serveur';
        document.getElementById('emailError').classList.remove('d-none');
    });
}

function confirmDeleteEmail(id, email) {
    document.getElementById('deleteEmailId').value = id;
    document.getElementById('deleteEmailMessage').textContent = `Supprimer l'email "${email}" ?`;
    deleteEmailModal.show();
}

function deleteEmail() {
    const id = document.getElementById('deleteEmailId').value;
    fetch(`/employe/email/${id}/supprimer-ajax/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            deleteEmailModal.hide();
            window.location.reload();
        } else {
            alert('Erreur : ' + data.error);
        }
    });
}


// ===== FONCTIONS ADRESSE =====
function openAdresseModal(id = null, rue = '', ville = '', pays = '', codePostal = '', type = '', dateDebut = '', dateFin = '') {
    document.getElementById('adresseForm').reset();
    document.getElementById('adresseError').classList.add('d-none');
    document.getElementById('adresseModalTitle').textContent = id ? 'Modifier l\'adresse' : 'Ajouter une adresse';

    if (id) {
        document.getElementById('adresseId').value = id;
        document.getElementById('adresseRue').value = rue;
        document.getElementById('adresseVille').value = ville;
        document.getElementById('adressePays').value = pays;
        document.getElementById('adresseCodePostal').value = codePostal;
        document.getElementById('adresseType').value = type;
        document.getElementById('adresseDateDebut').value = dateDebut;
        document.getElementById('adresseDateFin').value = dateFin;
    }

    adresseModal.show();
}

function saveAdresse() {
    const formData = new FormData(document.getElementById('adresseForm'));
    const adresseId = document.getElementById('adresseId').value;
    const url = adresseId ?
        `/employe/adresse/${adresseId}/modifier-ajax/` :
        '/employe/adresse/nouveau-ajax/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            adresseModal.hide();
            window.location.reload();
        } else {
            document.getElementById('adresseError').textContent = data.error;
            document.getElementById('adresseError').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('adresseError').textContent = 'Erreur de connexion au serveur';
        document.getElementById('adresseError').classList.remove('d-none');
    });
}

function confirmDeleteAdresse(id, ville, type) {
    document.getElementById('deleteAdresseId').value = id;
    document.getElementById('deleteAdresseMessage').textContent = `Supprimer l'adresse de ${ville} (${type}) ?`;
    deleteAdresseModal.show();
}

function deleteAdresse() {
    const id = document.getElementById('deleteAdresseId').value;
    fetch(`/employe/adresse/${id}/supprimer-ajax/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            deleteAdresseModal.hide();
            window.location.reload();
        } else {
            alert('Erreur : ' + data.error);
        }
    });
}
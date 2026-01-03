// ========================================
// Gestion de la photo de profil + Modals
// ========================================

// ===== VARIABLES GLOBALES =====
let contratModal, deleteModal;
let affectationModal, deleteAffectationModal;
let telephoneModal, deleteTelephoneModal;
let emailModal, deleteEmailModal;
let adresseModal, deleteAdresseModal;
let documentModal, deleteDocumentModal;
let photoModal;

// ========================================
// INITIALISATION AU CHARGEMENT DU DOM
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser tous les modals
    try {
        contratModal = new bootstrap.Modal(document.getElementById('contratModal'));
        deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        affectationModal = new bootstrap.Modal(document.getElementById('affectationModal'));
        deleteAffectationModal = new bootstrap.Modal(document.getElementById('deleteAffectationModal'));
        telephoneModal = new bootstrap.Modal(document.getElementById('telephoneModal'));
        deleteTelephoneModal = new bootstrap.Modal(document.getElementById('deleteTelephoneModal'));
        emailModal = new bootstrap.Modal(document.getElementById('emailModal'));
        deleteEmailModal = new bootstrap.Modal(document.getElementById('deleteEmailModal'));
        adresseModal = new bootstrap.Modal(document.getElementById('adresseModal'));
        deleteAdresseModal = new bootstrap.Modal(document.getElementById('deleteAdresseModal'));
        documentModal = new bootstrap.Modal(document.getElementById('documentModal'));
        deleteDocumentModal = new bootstrap.Modal(document.getElementById('deleteDocumentModal'));
    } catch(e) {
        console.error('Erreur lors de l\'initialisation des modals:', e);
    }

    // Initialiser le modal photo
    const photoModalElement = document.getElementById('photoModal');
    if (photoModalElement) {
        photoModal = new bootstrap.Modal(photoModalElement);
    }

    // Soumettre les formulaires
    document.getElementById('contratForm').addEventListener('submit', e => { e.preventDefault(); saveContrat(); });
    document.getElementById('affectationForm').addEventListener('submit', e => { e.preventDefault(); saveAffectation(); });
    document.getElementById('telephoneForm').addEventListener('submit', e => { e.preventDefault(); saveTelephone(); });
    document.getElementById('emailForm').addEventListener('submit', e => { e.preventDefault(); saveEmail(); });
    document.getElementById('adresseForm').addEventListener('submit', e => { e.preventDefault(); saveAdresse(); });
    document.getElementById('documentForm').addEventListener('submit', e => { e.preventDefault(); saveDocument(); });

    // Gestion formulaire photo
    const photoForm = document.getElementById('photoForm');
    if (photoForm) {
        photoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            savePhoto();
        });
    }

    // Aperçu de la photo avant upload
    const photoFileInput = document.getElementById('photoFile');
    if (photoFileInput) {
        photoFileInput.addEventListener('change', handlePhotoPreview);
    }

    // Auto-fermer les messages de succès
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-success');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// ========================================
// FONCTIONS PHOTO DE PROFIL
// ========================================

/**
 * Gère l'aperçu de la photo avant l'upload
 */
function handlePhotoPreview(e) {
    const file = e.target.files[0];

    if (!file) {
        return;
    }

    // Vérifier la taille du fichier (5 MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        showPhotoError('La taille du fichier ne doit pas dépasser 5 MB');
        e.target.value = '';
        return;
    }

    // Vérifier le type de fichier
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showPhotoError('Format non valide. Utilisez JPG, PNG ou GIF');
        e.target.value = '';
        return;
    }

    // Afficher l'aperçu
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImage = document.getElementById('previewImage');
        const photoPreview = document.getElementById('photoPreview');

        if (previewImage && photoPreview) {
            previewImage.src = e.target.result;
            photoPreview.classList.remove('d-none');
        }
    };
    reader.onerror = function() {
        showPhotoError('Erreur lors de la lecture du fichier');
    };
    reader.readAsDataURL(file);
}

/**
 * Ouvre le modal pour modifier la photo
 */
function openPhotoModal() {
    const photoForm = document.getElementById('photoForm');
    const photoPreview = document.getElementById('photoPreview');
    const photoError = document.getElementById('photoError');

    // Réinitialiser le formulaire
    if (photoForm) {
        photoForm.reset();
    }

    // Cacher l'aperçu et les erreurs
    if (photoPreview) {
        photoPreview.classList.add('d-none');
    }
    if (photoError) {
        photoError.classList.add('d-none');
    }

    // Afficher le modal
    if (photoModal) {
        photoModal.show();
    }
}

/**
 * Sauvegarde la photo via AJAX
 */
function savePhoto() {
    const form = document.getElementById('photoForm');
    const photoFileInput = document.getElementById('photoFile');
    const submitButton = form.querySelector('button[type="submit"]');

    // Vérification : Fichier sélectionné ?
    if (!photoFileInput.files || photoFileInput.files.length === 0) {
        showPhotoError('Veuillez sélectionner une photo avant d\'enregistrer');
        return false;
    }

    const photoFile = photoFileInput.files[0];

    // Vérification : Fichier valide ?
    if (!photoFile) {
        showPhotoError('Le fichier sélectionné est invalide');
        return false;
    }

    // Créer le FormData
    const formData = new FormData(form);

    // Désactiver le bouton pendant l'upload
    if (submitButton) {
        submitButton.disabled = true;
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Envoi en cours...';

        fetch('/employe/photo/modifier-ajax/', {
            method: 'POST',
            body: formData,
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;

            if (data.success) {
                photoModal.hide();
                showSuccessMessage('Photo de profil mise à jour avec succès');

                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showPhotoError(data.error || 'Une erreur est survenue lors de l\'upload');
            }
        })
        .catch(error => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            console.error('Erreur réseau:', error);
            showPhotoError('Erreur de connexion au serveur. Veuillez réessayer.');
        });
    }

    return false;
}

/**
 * Affiche un message d'erreur dans le modal photo
 */
function showPhotoError(message) {
    const photoError = document.getElementById('photoError');
    if (photoError) {
        photoError.textContent = message;
        photoError.classList.remove('d-none');
        photoError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Affiche un message de succès temporaire
 */
function showSuccessMessage(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        <strong>${message}</strong>
    `;

    document.body.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 3000);
}

// ========================================
// FONCTIONS CONTRAT
// ========================================
function openContratModal(id = null, type = '', dateDebut = '', dateFin = '') {
    const form = document.getElementById('contratForm');
    const modalTitle = document.getElementById('modalTitle');
    const errorMessage = document.getElementById('errorMessage');

    form.reset();
    errorMessage.classList.add('d-none');

    if (id) {
        modalTitle.textContent = 'Modifier le contrat';
        document.getElementById('contratId').value = id;
        document.getElementById('typeContrat').value = type;
        document.getElementById('dateDebut').value = dateDebut;
        document.getElementById('dateFin').value = dateFin;
    } else {
        modalTitle.textContent = 'Ajouter un contrat';
        document.getElementById('contratId').value = '';
    }

    contratModal.show();
}

function confirmDeleteContrat(id, type, dateDebut) {
    document.getElementById('deleteContratId').value = id;
    document.getElementById('deleteMessage').textContent = `Voulez-vous vraiment supprimer le contrat ${type} du ${dateDebut} ?`;
    deleteModal.show();
}

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
            alert('Erreur : ' + (data.error || 'Impossible de supprimer'));
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Erreur de connexion au serveur');
    });
}

function saveContrat() {
    const form = document.getElementById('contratForm');
    const formData = new FormData(form);
    const contratId = document.getElementById('contratId').value;
    const errorMessage = document.getElementById('errorMessage');

    const url = contratId ? `/employe/contrat/${contratId}/modifier-ajax/` : '/employe/contrat/nouveau-ajax/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
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

// ========================================
// FONCTIONS AFFECTATION
// ========================================
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
    const url = affectationId ? `/employe/affectation/${affectationId}/modifier-ajax/` : '/employe/affectation/nouveau-ajax/';

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

// ========================================
// FONCTIONS TÉLÉPHONE
// ========================================
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
    const url = telephoneId ? `/employe/telephone/${telephoneId}/modifier-ajax/` : '/employe/telephone/nouveau-ajax/';

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
        document.getElementById('telephoneError').textContent = 'Erreur de connexion';
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

// ========================================
// FONCTIONS EMAIL
// ========================================
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
    const url = emailId ? `/employe/email/${emailId}/modifier-ajax/` : '/employe/email/nouveau-ajax/';

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
        document.getElementById('emailError').textContent = 'Erreur de connexion';
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

// ========================================
// FONCTIONS ADRESSE
// ========================================
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
    const url = adresseId ? `/employe/adresse/${adresseId}/modifier-ajax/` : '/employe/adresse/nouveau-ajax/';

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
        document.getElementById('adresseError').textContent = 'Erreur de connexion';
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

// ========================================
// FONCTIONS DOCUMENT
// ========================================
function openDocumentModal() {
    document.getElementById('documentForm').reset();
    document.getElementById('documentError').classList.add('d-none');
    document.getElementById('documentModalTitle').textContent = 'Joindre un document';
    documentModal.show();
}

function saveDocument() {
    const formData = new FormData(document.getElementById('documentForm'));
    const url = '/employe/ajax/document/create/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            documentModal.hide();
            window.location.reload();
        } else {
            document.getElementById('documentError').textContent = data.error;
            document.getElementById('documentError').classList.remove('d-none');
        }
    })
    .catch(error => {
        document.getElementById('documentError').textContent = 'Erreur de connexion';
        document.getElementById('documentError').classList.remove('d-none');
    });
}

function confirmDeleteDocument(id, typeDocument) {
    document.getElementById('deleteDocumentId').value = id;
    document.getElementById('deleteDocumentMessage').textContent = `Supprimer le document "${typeDocument}" ?`;
    deleteDocumentModal.show();
}

function deleteDocument() {
    const id = document.getElementById('deleteDocumentId').value;
    fetch(`/employe/ajax/document/delete/${id}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            deleteDocumentModal.hide();
            window.location.reload();
        } else {
            alert('Erreur : ' + data.error);
        }
    });
}
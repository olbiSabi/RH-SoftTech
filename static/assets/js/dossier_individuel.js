// Configuration CSRF pour Django
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

const csrftoken = getCookie('csrftoken');

//##############################################
//############ Gestion des modales #############
//##############################################
class ModalManager {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.closeBtn = this.modal.querySelector('.close');
        this.cancelBtn = this.modal.querySelector('.btn-cancel');

        this.init();
    }

    init() {
        // Fermeture par le bouton X
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        // Fermeture par le bouton Annuler
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }

        // Fermeture en cliquant en dehors de la modale
        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.close();
            }
        });

        // Fermeture avec la touche Échap
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modal.classList.contains('show')) {
                this.close();
            }
        });
    }

    open() {
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.modal.classList.remove('show');
        document.body.style.overflow = 'auto';
        this.resetForm();
    }

    resetForm() {
        const form = this.modal.querySelector('form');
        if (form) {
            form.reset();
            // Nettoyer les messages d'erreur
            const errorMessages = form.querySelectorAll('.error-message');
            errorMessages.forEach(msg => msg.remove());
            // Retirer les classes d'erreur
            const errorInputs = form.querySelectorAll('.form-error');
            errorInputs.forEach(input => input.classList.remove('form-error'));
        }
    }
}

// Gestion de l'overlay de chargement
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('show');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// Afficher les messages d'alerte
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.style.transition = 'opacity 0.5s';
        alertDiv.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(alertDiv);
        }, 500);
    }, 3000);
}

//##############################################
//########### Gestion des adresses #############
//##############################################
class AdresseManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('adresseModal');
        this.form = document.getElementById('adresseForm');
        this.currentId = null;

        this.init();
    }

    init() {
        // Bouton ajouter
        const addBtn = document.getElementById('addAdresseBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        // Soumission du formulaire
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Boutons éditer et supprimer
        document.querySelectorAll('.edit-adresse-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-adresse-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('adresseModalTitle').textContent = 'Ajouter une adresse';
        document.getElementById('adresseSubmitBtn').textContent = 'Ajouter';
        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('adresseModalTitle').textContent = 'Modifier l\'adresse';
        document.getElementById('adresseSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/adresse/${id}/`);
            const data = await response.json();

            // Remplir le formulaire
            document.getElementById('type_adresse').value = data.type_adresse;
            document.getElementById('rue').value = data.rue;
            document.getElementById('complement').value = data.complement || '';
            document.getElementById('code_postal').value = data.code_postal;
            document.getElementById('ville').value = data.ville;
            document.getElementById('pays').value = data.pays;
            document.getElementById('date_debut').value = data.date_debut;
            document.getElementById('date_fin').value = data.date_fin || '';
            document.getElementById('actif').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }


    async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);
    const url = this.currentId
        ? `/employe/api/adresse/${this.currentId}/update/`
        : `/employe/api/adresse/create/`;

    showLoading();
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(
                this.currentId ? 'Adresse modifiée avec succès' : 'Adresse ajoutée avec succès',
                'success'
            );
            this.modal.close();
            this.reloadTab();
        } else {
            // Gérer les différentes erreurs
            if (data.errors && data.errors.__all__) {
                showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
            } else if (data.errors) {
                this.displayErrors(data.errors);
            } else {
                showAlert('Une erreur est survenue', 'danger');
            }
        }
    } catch (error) {
        showAlert('Une erreur est survenue: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/adresse/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Adresse supprimée avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                this.reloadTab();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        // Nettoyer les anciennes erreurs
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        // Afficher les nouvelles erreurs
        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }

    reloadTab() {
        window.location.href = window.location.href;
    }
}


//##############################################
//########### Gestion des téléphones ###########
//##############################################
class TelephoneManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('telephoneModal');
        this.form = document.getElementById('telephoneForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addTelephoneBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.edit-telephone-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-telephone-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('telephoneModalTitle').textContent = 'Ajouter un téléphone';
        document.getElementById('telephoneSubmitBtn').textContent = 'Ajouter';
        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('telephoneModalTitle').textContent = 'Modifier le téléphone';
        document.getElementById('telephoneSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/telephone/${id}/`);
            const data = await response.json();

            document.getElementById('numero').value = data.numero;
            document.getElementById('date_debut_validite_tel').value = data.date_debut_validite;
            document.getElementById('date_fin_validite_tel').value = data.date_fin_validite || '';
            document.getElementById('actif_tel').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);

    // Ajoutez le préfixe /employe/ devant les URLs API
    const url = this.currentId
        ? `/employe/api/telephone/${this.currentId}/update/`
        : `/employe/api/telephone/create/`;

    showLoading();
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(
                this.currentId ? 'Téléphone modifié avec succès' : 'Téléphone ajouté avec succès',
                'success'
            );
            this.modal.close();
            window.location.reload();
        } else {
            this.displayErrors(data.errors);
        }
    } catch (error) {
        showAlert('Une erreur est survenue: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/telephone/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Téléphone supprimé avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}

//##############################################
// Gestion des emails (similaire aux téléphones)
//##############################################
class EmailManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('emailModal');
        this.form = document.getElementById('emailForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addEmailBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.edit-email-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-email-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('emailModalTitle').textContent = 'Ajouter un email';
        document.getElementById('emailSubmitBtn').textContent = 'Ajouter';
        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('emailModalTitle').textContent = 'Modifier l\'email';
        document.getElementById('emailSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/email/${id}/`);
            const data = await response.json();

            document.getElementById('email').value = data.email;
            document.getElementById('date_debut_validite_email').value = data.date_debut_validite;
            document.getElementById('date_fin_validite_email').value = data.date_fin_validite || '';
            document.getElementById('actif_email').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const url = this.currentId
            ? `/employe/api/email/${this.currentId}/update/`
            : `/employe/api/email/create/`;

        showLoading();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(
                    this.currentId ? 'Email modifié avec succès' : 'Email ajouté avec succès',
                    'success'
                );
                this.modal.close();
                window.location.reload();
            } else {
                this.displayErrors(data.errors);
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/email/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Email supprimé avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}

//##############################################
//########## Gestion des documents #############
//##############################################
class DocumentManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('documentModal');
        this.form = document.getElementById('documentForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addDocumentBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.delete-document-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('documentModalTitle').textContent = 'Ajouter un document';
        this.modal.open();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        formData.append('employe_uuid', this.employeUuid);

        showLoading();
        try {
            const response = await fetch(`/employe/api/document/create/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('Document ajouté avec succès', 'success');
                this.modal.close();
                window.location.reload();
            } else {
                this.displayErrors(data.errors);
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/document/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Document supprimé avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}

//##############################################
//########### Gestion des contrats #############
//##############################################
class ContratManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('contratModal');
        this.form = document.getElementById('contratForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addContratBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.edit-contrat-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-contrat-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('contratModalTitle').textContent = 'Ajouter un contrat';
        document.getElementById('contratSubmitBtn').textContent = 'Ajouter';
        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('contratModalTitle').textContent = 'Modifier le contrat';
        document.getElementById('contratSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/contrat/${id}/`);
            const data = await response.json();

            document.getElementById('type_contrat').value = data.type_contrat;
            document.getElementById('date_debut_contrat').value = data.date_debut;
            document.getElementById('date_fin_contrat').value = data.date_fin || '';
            document.getElementById('actif_contrat').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);
    const url = this.currentId
        ? `/employe/api/contrat/${this.currentId}/update/`
        : `/employe/api/contrat/create/`;

    showLoading();
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(
                this.currentId ? 'Contrat modifié avec succès' : 'Contrat ajouté avec succès',
                'success'
            );
            this.modal.close();
            window.location.reload();
        } else {
            // GESTION AMÉLIORÉE DES ERREURS
            if (data.errors && data.errors.__all__) {
                // Afficher les erreurs générales (contrat actif, chevauchement)
                showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
            } else if (data.errors) {
                // Afficher les erreurs de champ spécifiques
                this.displayErrors(data.errors);
            } else if (data.error) {
                // Erreur générale
                showAlert('❌ Erreur: ' + data.error, 'danger');
            } else {
                showAlert('Une erreur est survenue', 'danger');
            }
        }
    } catch (error) {
        showAlert('Une erreur est survenue: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}
    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/contrat/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Contrat supprimé avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}

//##############################################
//######### Gestion des affectations ###########
//##############################################
class AffectationManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('affectationModal');
        this.form = document.getElementById('affectationForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addAffectationBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.edit-affectation-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-affectation-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });

        // Charger les postes lorsque le département change
        const departementSelect = document.getElementById('departement');
        if (departementSelect) {
            departementSelect.addEventListener('change', (e) => this.loadPostes(e.target.value));
        }
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('affectationModalTitle').textContent = 'Ajouter une affectation';
        document.getElementById('affectationSubmitBtn').textContent = 'Ajouter';
        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('affectationModalTitle').textContent = 'Modifier l\'affectation';
        document.getElementById('affectationSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/affectation/${id}/`);
            const data = await response.json();

            // Charger d'abord les postes du département
            await this.loadPostes(data.poste.departement_id);

            document.getElementById('poste').value = data.poste.id;
            document.getElementById('date_debut_affectation').value = data.date_debut;
            document.getElementById('date_fin_affectation').value = data.date_fin || '';
            document.getElementById('actif_affectation').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }

    async loadPostes(departementId) {
        if (!departementId) {
            document.getElementById('poste').innerHTML = '<option value="">Sélectionner d\'abord un département</option>';
            return;
        }

        try {
            const response = await fetch(`/employe/api/postes/?departement=${departementId}`);
            const postes = await response.json();

            const posteSelect = document.getElementById('poste');
            posteSelect.innerHTML = '<option value="">Sélectionner un poste...</option>';

            postes.forEach(poste => {
                const option = document.createElement('option');
                option.value = poste.id;
                option.textContent = poste.LIBELLE;
                posteSelect.appendChild(option);
            });
        } catch (error) {
            showAlert('Erreur lors du chargement des postes', 'danger');
        }
    }

    async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);
    const url = this.currentId
        ? `/employe/api/affectation/${this.currentId}/update/`
        : `/employe/api/affectation/create/`;

    showLoading();
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(
                this.currentId ? 'Affectation modifiée avec succès' : 'Affectation ajoutée avec succès',
                'success'
            );
            this.modal.close();
            window.location.reload();
        } else {
            // GESTION AMÉLIORÉE DES ERREURS
            if (data.errors && data.errors.__all__) {
                // Afficher les erreurs générales (affectation active, chevauchement)
                showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
            } else if (data.errors) {
                // Afficher les erreurs de champ spécifiques
                this.displayErrors(data.errors);
            } else if (data.error) {
                // Erreur générale
                showAlert('❌ Erreur: ' + data.error, 'danger');
            } else {
                showAlert('Une erreur est survenue', 'danger');
            }
        }
    } catch (error) {
        showAlert('Une erreur est survenue: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/affectation/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Affectation supprimée avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}

//##############################################
//####### Gestion des personnes à charge #######
//##############################################
class FamilleManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('familleModal');
        this.form = document.getElementById('familleForm');
        this.currentId = null;

        this.init();
    }

    init() {
        // Bouton ajouter
        const addBtn = document.getElementById('addFamilleBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        // Soumission du formulaire
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Boutons éditer et supprimer
        document.querySelectorAll('.edit-famille-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-famille-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });

        // Auto-remplir la date de début si enfant
        const personneChargeSelect = document.getElementById('personne_charge');
        const dateDebutInput = document.getElementById('date_debut_prise_charge');
        const dateNaissanceInput = document.getElementById('date_naissance');

        if (personneChargeSelect && dateDebutInput && dateNaissanceInput) {
            personneChargeSelect.addEventListener('change', () => this.autoFillDateDebut());
            dateNaissanceInput.addEventListener('change', () => this.autoFillDateDebut());
        }
    }

    autoFillDateDebut() {
        const personneCharge = document.getElementById('personne_charge').value;
        const dateNaissance = document.getElementById('date_naissance').value;
        const dateDebutInput = document.getElementById('date_debut_prise_charge');

        if (personneCharge === 'ENFANT' && dateNaissance && !dateDebutInput.value) {
            dateDebutInput.value = dateNaissance;
        }
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('familleModalTitle').textContent = 'Ajouter une personne à charge';
        document.getElementById('familleSubmitBtn').textContent = 'Ajouter';

        // Réinitialiser le formulaire
        if (this.form) {
            this.form.reset();
        }

        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('familleModalTitle').textContent = 'Modifier la personne à charge';
        document.getElementById('familleSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/famille/${id}/`);
            const data = await response.json();

            // Remplir le formulaire
            document.getElementById('personne_charge').value = data.personne_charge;
            document.getElementById('nom').value = data.nom;
            document.getElementById('prenom').value = data.prenom;
            document.getElementById('sexe').value = data.sexe;
            document.getElementById('date_naissance').value = data.date_naissance;
            document.getElementById('date_debut_prise_charge').value = data.date_debut_prise_charge;
            document.getElementById('date_fin_prise_charge').value = data.date_fin_prise_charge || '';
            document.getElementById('actif_famille').checked = data.actif;

            this.modal.open();
        } catch (error) {
            showAlert('Erreur lors du chargement des données', 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const url = this.currentId
            ? `/employe/api/famille/${this.currentId}/update/`
            : `/employe/api/famille/create/`;

        showLoading();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(
                    this.currentId ? 'Personne à charge modifiée avec succès' : 'Personne à charge ajoutée avec succès',
                    'success'
                );
                this.modal.close();
                window.location.reload();
            } else {
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else {
                    showAlert('Une erreur est survenue', 'danger');
                }
            }
        } catch (error) {
            showAlert('Une erreur est survenue: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        const deleteModal = new ModalManager('deleteModal');
        document.getElementById('confirmDeleteBtn').onclick = () => this.delete(id);
        deleteModal.open();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/employe/api/famille/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            if (response.ok) {
                showAlert('Personne à charge supprimée avec succès', 'success');
                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
                window.location.reload();
            } else {
                showAlert('Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            showAlert('Une erreur est survenue', 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        // Nettoyer les anciennes erreurs
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        // Afficher les nouvelles erreurs
        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                const formGroup = input.closest('.modal-form-group');
                formGroup.classList.add('form-error');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = messages.join(', ');
                formGroup.appendChild(errorDiv);
            }
        }
    }
}


// Mettre à jour l'initialisation dans DOMContentLoaded
// Ajouter ces lignes dans la fonction d'initialisation existante :

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const employeUuid = document.body.dataset.employeUuid;

    if (employeUuid) {
        const activeTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';

        if (activeTab === 'coordonnees') {
            new AdresseManager(employeUuid);
            new TelephoneManager(employeUuid);
            new EmailManager(employeUuid);
        } else if (activeTab === 'contrats') {
            // AJOUTER CES LIGNES
            new ContratManager(employeUuid);
            new AffectationManager(employeUuid);
        } else if (activeTab === 'documents') {
            new DocumentManager(employeUuid);
        } else if (activeTab === 'famille') {
            new FamilleManager(employeUuid);
        }
    }

    // ... reste du code
});

    // Gestion des clics sur les employés dans le sidebar
    document.querySelectorAll('.employee-item').forEach(item => {
        item.addEventListener('click', function() {
            const uuid = this.dataset.uuid;
            const currentTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';
            window.location.href = `/employe/dossier/${uuid}/?tab=${currentTab}`;
        });
    });

    // Fonction de recherche
    const searchBox = document.getElementById('searchBox');
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const employeeItems = document.querySelectorAll('.employee-item');

            employeeItems.forEach(item => {
                const name = item.querySelector('.employee-name').textContent.toLowerCase();
                const matricule = item.querySelector('.employee-matricule').textContent.toLowerCase();

                if (name.includes(searchTerm) || matricule.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }



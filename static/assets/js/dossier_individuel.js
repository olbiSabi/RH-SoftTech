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
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }

        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.close();
            }
        });

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
            const errorMessages = form.querySelectorAll('.error-message');
            errorMessages.forEach(msg => msg.remove());
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
        const addBtn = document.getElementById('addAdresseBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

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
// Gestion des emails
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
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else if (data.error) {
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
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else if (data.error) {
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
        const addBtn = document.getElementById('addFamilleBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

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
//####### Gestion Historique Noms/Prénoms ######
//##############################################
class ZNPManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('znpModal');
        this.form = document.getElementById('znpForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addZNPBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.edit-znp-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-znp-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });

        const restrictionsDiv = document.getElementById('znpRestrictions');
        if (restrictionsDiv) {
            restrictionsDiv.style.display = 'block';
        }
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('znpModalTitle').textContent = 'Ajouter un historique nom/prénom';
        document.getElementById('znpSubmitBtn').textContent = 'Ajouter';

        if (this.form) {
            this.form.reset();
        }

        this.modal.open();
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('znpModalTitle').textContent = 'Modifier l\'historique nom/prénom';
        document.getElementById('znpSubmitBtn').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/api/znp/${id}/`);
            if (!response.ok) {
                throw new Error('Erreur HTTP: ' + response.status);
            }
            const data = await response.json();

            document.getElementById('znp_nom').value = data.nom || '';
            document.getElementById('znp_prenoms').value = data.prenoms || '';
            document.getElementById('znp_date_debut_validite').value = data.date_debut_validite || '';
            document.getElementById('znp_date_fin_validite').value = data.date_fin_validite || '';
            document.getElementById('znp_actif').checked = data.actif || false;

            this.modal.open();
        } catch (error) {
            showAlert('❌ Erreur lors du chargement des données: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const url = this.currentId
            ? `/employe/api/znp/${this.currentId}/update/`
            : `/employe/api/znp/create/`;

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

            if (response.ok && data.success) {
                showAlert(
                    this.currentId ? '✅ Historique modifié avec succès' : '✅ Historique ajouté avec succès',
                    'success'
                );
                this.modal.close();
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 8000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else if (data.error) {
                    showAlert('❌ ' + data.error, 'danger');
                } else {
                    showAlert('❌ Une erreur est survenue lors de l\'opération', 'danger');
                }
            }
        } catch (error) {
            showAlert('❌ Erreur réseau: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        this.pendingDeleteId = id;

        const deleteModal = new ModalManager('deleteModal');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            const currentConfirmBtn = document.getElementById('confirmDeleteBtn');
            currentConfirmBtn.addEventListener('click', () => {
                this.delete(this.pendingDeleteId);
            });
        }

        const cancelBtn = document.querySelector('#deleteModal .btn-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                deleteModal.close();
                this.pendingDeleteId = null;
            });
        }

        deleteModal.open();
    }

    async delete(id) {
        if (!id) {
            return;
        }

        showLoading();

        try {
            const response = await fetch(`/employe/api/znp/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('✅ Historique supprimé avec succès', 'success');

                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();

                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } else {
                showAlert('❌ Erreur lors de la suppression: ' + (data.error || ''), 'danger');

                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
            }

        } catch (error) {
            showAlert('❌ Erreur réseau lors de la suppression', 'danger');

            const deleteModal = new ModalManager('deleteModal');
            deleteModal.close();

        } finally {
            hideLoading();
            this.pendingDeleteId = null;
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            let inputId;
            switch(field) {
                case 'nom':
                    inputId = 'znp_nom';
                    break;
                case 'prenoms':
                    inputId = 'znp_prenoms';
                    break;
                case 'date_debut_validite':
                    inputId = 'znp_date_debut_validite';
                    break;
                case 'date_fin_validite':
                    inputId = 'znp_date_fin_validite';
                    break;
                default:
                    inputId = field;
            }

            const input = document.getElementById(inputId);
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
//### Gestion des Personnes à Prévenir (ZYPP) ###
//##############################################
class PersonnePrevManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('personnePrevModal');
        this.viewModal = new ModalManager('personnePrevViewModal');
        this.form = document.getElementById('personnePrevForm');
        this.currentId = null;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addPersonnePrevBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        document.querySelectorAll('.view-personne-prev-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openViewModal(id);
            });
        });

        document.querySelectorAll('.edit-personne-prev-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-personne-prev-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        this.currentId = null;
        document.getElementById('personnePrevModalTitle').innerHTML = '<i class="fas fa-ambulance"></i> Ajouter un contact d\'urgence';
        document.getElementById('personnePrevSubmitText').textContent = 'Ajouter';

        if (this.form) {
            this.form.reset();
        }

        const today = new Date().toISOString().split('T')[0];
        document.getElementById('date_debut_validite_prev').value = today;

        this.modal.open();
    }

    async openViewModal(id) {
        showLoading();

        try {
            const response = await fetch(`/employe/ajax/personne-prevenir/${id}/detail/`);
            if (!response.ok) {
                throw new Error('Erreur HTTP: ' + response.status);
            }
            const data = await response.json();

            const content = `
                <div class="detail-view">
                    <div class="detail-section">
                        <h4><i class="fas fa-user"></i> Identité</h4>
                        <p><strong>Nom complet:</strong> ${data.prenom} ${data.nom}</p>
                        <p><strong>Lien de parenté:</strong> ${this.getLienParenteLabel(data.lien_parente)}</p>
                        <p><strong>Priorité:</strong> ${this.getPrioriteLabel(data.ordre_priorite)}</p>
                    </div>

                    <div class="detail-section">
                        <h4><i class="fas fa-phone"></i> Coordonnées</h4>
                        <p><strong>Téléphone principal:</strong> <a href="tel:${data.telephone_principal}">${data.telephone_principal}</a></p>
                        ${data.telephone_secondaire ? `<p><strong>Téléphone secondaire:</strong> <a href="tel:${data.telephone_secondaire}">${data.telephone_secondaire}</a></p>` : ''}
                        ${data.email ? `<p><strong>Email:</strong> <a href="mailto:${data.email}">${data.email}</a></p>` : ''}
                        ${data.adresse ? `<p><strong>Adresse:</strong> ${data.adresse}</p>` : ''}
                    </div>

                    ${data.remarques ? `
                    <div class="detail-section">
                        <h4><i class="fas fa-comment"></i> Remarques</h4>
                        <p>${data.remarques}</p>
                    </div>
                    ` : ''}

                    <div class="detail-section">
                        <h4><i class="fas fa-calendar"></i> Période de validité</h4>
                        <p><strong>Du:</strong> ${this.formatDate(data.date_debut_validite)}</p>
                        <p><strong>Au:</strong> ${data.date_fin_validite ? this.formatDate(data.date_fin_validite) : 'Indéterminé'}</p>
                        <p><strong>Statut:</strong> ${data.actif ? '<span class="badge badge-success">✅ Actif</span>' : '<span class="badge badge-secondary">⏹️ Inactif</span>'}</p>
                    </div>
                </div>
            `;

            document.getElementById('personnePrevViewContent').innerHTML = content;
            this.viewModal.open();

        } catch (error) {
            showAlert('❌ Erreur lors du chargement des détails: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    async openEditModal(id) {
        this.currentId = id;
        document.getElementById('personnePrevModalTitle').innerHTML = '<i class="fas fa-edit"></i> Modifier le contact d\'urgence';
        document.getElementById('personnePrevSubmitText').textContent = 'Modifier';

        showLoading();
        try {
            const response = await fetch(`/employe/ajax/personne-prevenir/${id}/detail/`);
            if (!response.ok) {
                throw new Error('Erreur HTTP: ' + response.status);
            }
            const data = await response.json();

            document.getElementById('nom_prev').value = data.nom || '';
            document.getElementById('prenom_prev').value = data.prenom || '';
            document.getElementById('lien_parente').value = data.lien_parente || '';
            document.getElementById('telephone_principal').value = data.telephone_principal || '';
            document.getElementById('telephone_secondaire').value = data.telephone_secondaire || '';
            document.getElementById('email_prev').value = data.email || '';
            document.getElementById('adresse_prev').value = data.adresse || '';
            document.getElementById('ordre_priorite').value = data.ordre_priorite || '';
            document.getElementById('remarques_prev').value = data.remarques || '';
            document.getElementById('date_debut_validite_prev').value = data.date_debut_validite || '';
            document.getElementById('date_fin_validite_prev').value = data.date_fin_validite || '';
            document.getElementById('actif_prev').checked = data.actif || false;

            this.modal.open();
        } catch (error) {
            showAlert('❌ Erreur lors du chargement des données: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const url = this.currentId
            ? `/employe/ajax/personne-prevenir/${this.currentId}/update/`
            : '/employe/ajax/personne-prevenir/create/';

        showLoading();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData
            });

            const contentType = response.headers.get('content-type');

            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                showAlert('❌ Erreur: Le serveur n\'a pas retourné une réponse JSON valide (Status: ' + response.status + ')', 'danger');
                return;
            }

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert(
                    this.currentId ? '✅ Contact d\'urgence modifié avec succès' : '✅ Contact d\'urgence ajouté avec succès',
                    'success'
                );
                this.modal.close();
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 8000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else if (data.error) {
                    showAlert('❌ ' + data.error, 'danger');
                } else {
                    showAlert('❌ Une erreur est survenue lors de l\'opération', 'danger');
                }
            }
        } catch (error) {
            showAlert('❌ Erreur: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        this.pendingDeleteId = id;

        const deleteModal = new ModalManager('deleteModal');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            const currentConfirmBtn = document.getElementById('confirmDeleteBtn');
            currentConfirmBtn.addEventListener('click', () => {
                this.delete(this.pendingDeleteId);
            });
        }

        const cancelBtn = document.querySelector('#deleteModal .btn-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                deleteModal.close();
                this.pendingDeleteId = null;
            });
        }

        deleteModal.open();
    }

    async delete(id) {
        if (!id) {
            return;
        }

        showLoading();

        try {
            const response = await fetch(`/employe/ajax/personne-prevenir/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('✅ Contact d\'urgence supprimé avec succès', 'success');

                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();

                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } else {
                showAlert('❌ Erreur lors de la suppression: ' + (data.error || ''), 'danger');

                const deleteModal = new ModalManager('deleteModal');
                deleteModal.close();
            }

        } catch (error) {
            showAlert('❌ Erreur réseau lors de la suppression', 'danger');

            const deleteModal = new ModalManager('deleteModal');
            deleteModal.close();

        } finally {
            hideLoading();
            this.pendingDeleteId = null;
        }
    }

    displayErrors(errors) {
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-error').forEach(el => el.classList.remove('form-error'));

        for (const [field, messages] of Object.entries(errors)) {
            let inputId;
            switch(field) {
                case 'nom':
                    inputId = 'nom_prev';
                    break;
                case 'prenom':
                    inputId = 'prenom_prev';
                    break;
                case 'email':
                    inputId = 'email_prev';
                    break;
                case 'adresse':
                    inputId = 'adresse_prev';
                    break;
                case 'remarques':
                    inputId = 'remarques_prev';
                    break;
                case 'date_debut_validite':
                    inputId = 'date_debut_validite_prev';
                    break;
                case 'date_fin_validite':
                    inputId = 'date_fin_validite_prev';
                    break;
                default:
                    inputId = field;
            }

            const input = document.getElementById(inputId);
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

    getLienParenteLabel(lien) {
        const liens = {
            'CONJOINT': '💑 Conjoint(e)',
            'PARENT': '👨‍👩‍👦 Parent',
            'ENFANT': '👶 Enfant',
            'FRERE_SOEUR': '👫 Frère/Sœur',
            'AMI': '🤝 Ami(e)',
            'COLLEGUE': '💼 Collègue',
            'VOISIN': '🏠 Voisin(e)',
            'AUTRE': '👤 Autre'
        };
        return liens[lien] || lien;
    }

    getPrioriteLabel(priorite) {
        const priorites = {
            1: '🔴 Contact principal',
            2: '🟠 Contact secondaire',
            3: '🟡 Contact tertiaire'
        };
        return priorites[priorite] || `Priorité ${priorite}`;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }
}

//##############################################
//### Gestion de l'Identité Bancaire (ZYIB) ###
//##############################################
class IdentiteBancaireManager {
    constructor(employeUuid) {
        this.employeUuid = employeUuid;
        this.modal = new ModalManager('identiteBancaireModal');
        this.form = document.getElementById('identiteBancaireForm');
        this.hasIdentiteBancaire = false;

        this.init();
    }

    init() {
        const addBtn = document.getElementById('addIdentiteBancaireBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        const editBtns = [
            document.getElementById('editIdentiteBancaireBtn'),
            document.getElementById('editIdentiteBancaireMobileBtn')
        ];

        editBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => this.openEditModal());
            }
        });

        const deleteBtns = [
            document.getElementById('deleteIdentiteBancaireBtn'),
            document.getElementById('deleteIdentiteBancaireMobileBtn')
        ];

        deleteBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => this.confirmDelete());
            }
        });

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        this.setupAutoFormatting();
    }

    setupAutoFormatting() {
        const codeBanqueInput = document.getElementById('code_banque');
        if (codeBanqueInput) {
            codeBanqueInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 5);
            });
        }

        const codeGuichetInput = document.getElementById('code_guichet');
        if (codeGuichetInput) {
            codeGuichetInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 5);
            });
        }

        const numeroCompteInput = document.getElementById('numero_compte');
        if (numeroCompteInput) {
            numeroCompteInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase().substring(0, 11);
            });
        }

        const cleRibInput = document.getElementById('cle_rib');
        if (cleRibInput) {
            cleRibInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 2);
            });
        }

        const ibanInput = document.getElementById('iban');
        if (ibanInput) {
            ibanInput.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\s/g, '').toUpperCase();
                value = value.substring(0, 34);
                e.target.value = value;
            });

            ibanInput.addEventListener('blur', (e) => {
                let value = e.target.value.replace(/\s/g, '');
                if (value.length > 0) {
                    e.target.value = value.match(/.{1,4}/g).join(' ');
                }
            });
        }

        const bicInput = document.getElementById('bic');
        if (bicInput) {
            bicInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\s/g, '').toUpperCase().substring(0, 11);
            });
        }
    }

    openAddModal() {
        document.getElementById('identiteBancaireTitleText').textContent = 'Ajouter une identité bancaire';
        document.getElementById('identiteBancaireSubmitText').textContent = 'Enregistrer';

        if (this.form) {
            this.form.reset();
        }

        this.modal.open();
    }

    async openEditModal() {
        document.getElementById('identiteBancaireTitleText').textContent = 'Modifier l\'identité bancaire';
        document.getElementById('identiteBancaireSubmitText').textContent = 'Mettre à jour';

        showLoading();
        try {
            const response = await fetch(`/employe/ajax/identite-bancaire/${this.employeUuid}/detail/`);

            if (!response.ok) {
                throw new Error('Erreur HTTP: ' + response.status);
            }

            const data = await response.json();

            document.getElementById('titulaire_compte').value = data.titulaire_compte || '';
            document.getElementById('nom_banque').value = data.nom_banque || '';
            document.getElementById('type_compte').value = data.type_compte || 'COURANT';
            document.getElementById('domiciliation').value = data.domiciliation || '';
            document.getElementById('date_ouverture').value = data.date_ouverture || '';

            document.getElementById('code_banque').value = data.code_banque || '';
            document.getElementById('code_guichet').value = data.code_guichet || '';
            document.getElementById('numero_compte').value = data.numero_compte || '';
            document.getElementById('cle_rib').value = data.cle_rib || '';

            document.getElementById('iban').value = data.iban || '';
            document.getElementById('bic').value = data.bic || '';

            document.getElementById('remarques').value = data.remarques || '';
            document.getElementById('actif_ib').checked = data.actif || false;

            this.modal.open();
        } catch (error) {
            showAlert('❌ Erreur lors du chargement des données: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const url = `/employe/ajax/identite-bancaire/${this.employeUuid}/save/`;

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

            if (response.ok && data.success) {
                showAlert(data.message, 'success');
                this.modal.close();
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 8000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                } else if (data.error) {
                    showAlert('❌ ' + data.error, 'danger');
                } else {
                    showAlert('❌ Une erreur est survenue lors de l\'opération', 'danger');
                }
            }
        } catch (error) {
            showAlert('❌ Erreur réseau: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete() {
        const deleteModal = new ModalManager('deleteModal');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            const currentConfirmBtn = document.getElementById('confirmDeleteBtn');
            currentConfirmBtn.addEventListener('click', () => {
                deleteModal.close();
                this.delete();
            });
        }

        const cancelBtn = document.querySelector('#deleteModal .btn-cancel');
        if (cancelBtn) {
            const newCancelBtn = cancelBtn.cloneNode(true);
            cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

            const currentCancelBtn = document.querySelector('#deleteModal .btn-cancel');
            currentCancelBtn.addEventListener('click', () => {
                deleteModal.close();
            });
        }

        const modalBody = document.querySelector('#deleteModal .modal-body p');
        if (modalBody) {
            modalBody.textContent = 'Êtes-vous sûr de vouloir supprimer cette identité bancaire ? Cette action est irréversible.';
        }

        deleteModal.open();
    }

    async delete() {
        showLoading();

        try {
            const response = await fetch(`/employe/ajax/identite-bancaire/${this.employeUuid}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showAlert('✅ Identité bancaire supprimée avec succès', 'success');

                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } else {
                showAlert('❌ Erreur lors de la suppression: ' + (data.error || ''), 'danger');
            }

        } catch (error) {
            showAlert('❌ Erreur réseau lors de la suppression', 'danger');
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
                if (formGroup) {
                    formGroup.classList.add('form-error');

                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = messages.join(', ');
                    formGroup.appendChild(errorDiv);
                }
            }
        }

        showAlert('❌ Veuillez corriger les erreurs dans le formulaire', 'warning');
    }

    formatRib(codeBanque, codeGuichet, numeroCompte, cleRib) {
        return `${codeBanque} ${codeGuichet} ${numeroCompte} ${cleRib}`;
    }

    formatIban(iban) {
        if (!iban) return '';
        const cleanIban = iban.replace(/\s/g, '');
        return cleanIban.match(/.{1,4}/g).join(' ');
    }
}

// Initialisation principale
document.addEventListener('DOMContentLoaded', function() {
    const employeUuid = document.body.dataset.employeUuid;

    if (employeUuid) {
        const activeTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';

        if (activeTab === 'coordonnees') {
            new AdresseManager(employeUuid);
            new TelephoneManager(employeUuid);
            new EmailManager(employeUuid);
            new IdentiteBancaireManager(employeUuid);
        } else if (activeTab === 'contrats') {
            new ContratManager(employeUuid);
            new AffectationManager(employeUuid);
        } else if (activeTab === 'documents') {
            new DocumentManager(employeUuid);
        } else if (activeTab === 'famille') {
            new FamilleManager(employeUuid);
            new ZNPManager(employeUuid);
            new PersonnePrevManager(employeUuid);
        }

        document.querySelectorAll('.employee-item').forEach(item => {
            item.addEventListener('click', function() {
                const uuid = this.dataset.uuid;
                const currentTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';
                window.location.href = `/employe/dossier/${uuid}/?tab=${currentTab}`;
            });
        });

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
    }
});

document.querySelectorAll('.employee-item').forEach(item => {
    item.addEventListener('click', function() {
        const uuid = this.dataset.uuid;
        const currentTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';
        window.location.href = `/employe/dossier/${uuid}/?tab=${currentTab}`;
    });
});

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
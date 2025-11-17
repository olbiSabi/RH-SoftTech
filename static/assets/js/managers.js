// static/assets/js/managers.js

// ============================================
// FONCTIONS UTILITAIRES (DOIVENT ÊTRE EN PREMIER)
// ============================================

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

// Fonction pour afficher le chargement
function showLoading() {
    // Créer un overlay de chargement simple
    let loadingOverlay = document.getElementById('loadingOverlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        loadingOverlay.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    loadingOverlay.style.display = 'flex';
}

// Fonction pour cacher le chargement
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Fonction pour afficher les alertes
function showAlert(message, type = 'success', duration = 3000) {
    // Supprimer les alertes existantes
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());

    // Créer une nouvelle alerte
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;

    document.body.appendChild(alertDiv);

    // Auto-fermer après la durée spécifiée
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// ============================================
// CLASSE MANAGER MANAGER
// ============================================

class ManagerManager {
    constructor() {
        this.modal = new bootstrap.Modal(document.getElementById('managerModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        this.form = document.getElementById('managerForm');
        this.currentId = null;

        this.init();
    }

    init() {
        console.log('✅ ManagerManager initialisé');

        // Boutons d'ajout
        const addBtn = document.getElementById('addManagerBtn');
        const addBtnEmpty = document.getElementById('addManagerBtnEmpty');

        if (addBtn) {
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        if (addBtnEmpty) {
            addBtnEmpty.addEventListener('click', () => this.openAddModal());
        }

        // Boutons d'ajout par département
        document.querySelectorAll('.add-manager-departement-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const departementId = e.currentTarget.dataset.departementId;
                const departementLibelle = e.currentTarget.dataset.departementLibelle;
                this.openAddModalForDepartement(departementId, departementLibelle);
            });
        });

        // Soumission du formulaire
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Boutons d'édition et suppression
        document.querySelectorAll('.edit-manager-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.openEditModal(id);
            });
        });

        document.querySelectorAll('.delete-manager-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.id;
                this.confirmDelete(id);
            });
        });
    }

    openAddModal() {
        console.log('📝 Ouverture modal ajout');
        this.currentId = null;
        document.getElementById('managerModalTitle').textContent = 'Ajouter un Manager';
        document.getElementById('managerSubmitBtn').textContent = 'Ajouter';

        // Réinitialiser le formulaire
        if (this.form) {
            this.form.reset();
            this.clearErrors();
        }

        this.modal.show();
    }

    openAddModalForDepartement(departementId, departementLibelle) {
        this.openAddModal();
        const departementSelect = document.getElementById('departement');
        if (departementSelect) {
            departementSelect.value = departementId;
        }
    }

    async openEditModal(id) {
        console.log('✏️ Ouverture modal édition pour ID:', id);
        this.currentId = id;

        showLoading();
        try {
            const response = await fetch(`/departement/api/manager/${id}/`);
            if (!response.ok) {
                throw new Error('Erreur ' + response.status);
            }

            const data = await response.json();
            console.log('📦 Données reçues:', data);

            document.getElementById('managerModalTitle').textContent = 'Modifier le Manager';
            document.getElementById('managerSubmitBtn').textContent = 'Modifier';

            // Remplir le formulaire
            document.getElementById('departement').value = data.departement;
            document.getElementById('employe').value = data.employe;
            document.getElementById('date_debut').value = data.date_debut;
            document.getElementById('date_fin').value = data.date_fin;

            this.modal.show();
        } catch (error) {
            console.error('❌ Erreur:', error);
            showAlert('Erreur lors du chargement des données: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        console.log('🚀 Soumission du formulaire...');

        // Valider les champs requis
        const departement = document.getElementById('departement').value;
        const employe = document.getElementById('employe').value;
        const dateDebut = document.getElementById('date_debut').value;

        if (!departement || !employe || !dateDebut) {
            showAlert('❌ Veuillez remplir tous les champs obligatoires', 'warning');
            return;
        }

        const formData = new FormData(this.form);
        const url = this.currentId
            ? `/departement/api/manager/${this.currentId}/update/`
            : `/departement/api/manager/create/`;

        console.log('📤 Envoi vers:', url);
        console.log('📋 Données:', Object.fromEntries(formData));

        showLoading();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });

            const data = await response.json();
            console.log('📥 Réponse:', data);

            if (response.ok) {
                showAlert(
                    this.currentId ? '✅ Manager modifié avec succès' : '✅ Manager ajouté avec succès',
                    'success'
                );
                this.modal.hide();

                // Recharger la page après un court délai
                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } else {
                console.error('❌ Erreur serveur:', data);
                if (data.errors && data.errors.__all__) {
                    showAlert('❌ ' + data.errors.__all__[0], 'warning', 6000);
                } else if (data.errors) {
                    this.displayErrors(data.errors);
                    showAlert('❌ Veuillez corriger les erreurs dans le formulaire', 'warning');
                } else if (data.error) {
                    showAlert('❌ Erreur: ' + data.error, 'danger');
                } else {
                    showAlert('❌ Une erreur est survenue lors de l\'enregistrement', 'danger');
                }
            }
        } catch (error) {
            console.error('❌ Erreur réseau:', error);
            showAlert('❌ Erreur réseau: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    confirmDelete(id) {
        this.currentDeleteId = id;
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            confirmBtn.onclick = () => this.delete(id);
        }
        this.deleteModal.show();
    }

    async delete(id) {
        showLoading();
        try {
            const response = await fetch(`/departement/api/manager/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('✅ Manager supprimé avec succès', 'success');
                this.deleteModal.hide();
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showAlert('❌ Erreur lors de la suppression: ' + (data.error || 'Erreur inconnue'), 'danger');
            }
        } catch (error) {
            console.error('❌ Erreur:', error);
            showAlert('❌ Erreur réseau: ' + error.message, 'danger');
        } finally {
            hideLoading();
        }
    }

    displayErrors(errors) {
        // Nettoyer les anciennes erreurs
        this.clearErrors();

        // Afficher les nouvelles erreurs
        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                input.classList.add('is-invalid');

                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = Array.isArray(messages) ? messages.join(', ') : messages;
                input.parentNode.appendChild(errorDiv);
            } else {
                console.warn(`Champ "${field}" non trouvé pour afficher l'erreur:`, messages);
            }
        }
    }

    clearErrors() {
        // Nettoyer toutes les erreurs
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        document.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
    }
}

// ============================================
// INITIALISATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM chargé - initialisation ManagerManager');

    // Vérifier que Bootstrap est disponible
    if (typeof bootstrap === 'undefined') {
        console.error('❌ Bootstrap non chargé!');
        return;
    }

    // Vérifier que le modal existe
    const modal = document.getElementById('managerModal');
    if (!modal) {
        console.error('❌ Modal managerModal non trouvé!');
        return;
    }

    new ManagerManager();
    console.log('✅ ManagerManager initialisé avec succès');
});
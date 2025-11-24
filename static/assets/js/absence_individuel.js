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


// Initialisation principale (REMPLACER LA SECTION EXISTANTE)
document.addEventListener('DOMContentLoaded', function() {
    const employeUuid = document.body.dataset.employeUuid;

    if (employeUuid) {
        const activeTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';

        console.log('🔧 Initialisation onglet:', activeTab, 'pour employé:', employeUuid);

        if (activeTab === 'coordonnees') {
            new AdresseManager(employeUuid);
            new TelephoneManager(employeUuid);
            new EmailManager(employeUuid);
            new IdentiteBancaireManager(employeUuid);
        } else if (activeTab === 'contrats') {
            new ContratManager(employeUuid);
            new AffectationManager(employeUuid);
        }

        // Gestion des clics sur les employés dans le sidebar
        document.querySelectorAll('.employee-item').forEach(item => {
            item.addEventListener('click', function() {
                const uuid = this.dataset.uuid;
                const currentTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';
                window.location.href = `/absence/dossier/${uuid}/?tab=${currentTab}`;
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

    } else {
        console.warn('⚠️ Aucun UUID employé trouvé');
    }
});


// Gestion des clics sur les employés dans le sidebar
document.querySelectorAll('.employee-item').forEach(item => {
        item.addEventListener('click', function() {
            const uuid = this.dataset.uuid;
            const currentTab = new URLSearchParams(window.location.search).get('tab') || 'donnees';
            window.location.href = `/absence/dossier/${uuid}/?tab=${currentTab}`;
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



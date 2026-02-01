// Fonction de recherche côté client
function filterEmployees() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const employeeRows = document.querySelectorAll('.employee-row');
    let hasResults = false;

    employeeRows.forEach(row => {
        const name = row.querySelector('.employee-name').textContent.toLowerCase();
        const matricule = row.querySelector('.employee-matricule').textContent.toLowerCase();

        if (name.includes(searchTerm) || matricule.includes(searchTerm)) {
            row.style.display = '';
            hasResults = true;
        } else {
            row.style.display = 'none';
        }
    });

    // Afficher un message si aucun résultat
    const noResultsRow = document.querySelector('.no-results');
    if (noResultsRow) {
        noResultsRow.style.display = hasResults ? 'none' : '';
    }
}

// Fonction pour gérer le clic sur un employé
function handleEmployeeClick(event) {
    // Empêcher la propagation de l'événement pour éviter les conflits
    event.stopPropagation();

    // Retirer la classe 'selected' de tous les employés
    document.querySelectorAll('.employee-row').forEach(row => {
        row.classList.remove('selected');
    });

    // Ajouter la classe 'selected' à l'employé cliqué
    const clickedRow = event.currentTarget;
    clickedRow.classList.add('selected');

    // Récupérer le matricule
    const matricule = clickedRow.getAttribute('data-matricule');

    // Afficher le matricule dans la console (vous pouvez modifier cette partie selon vos besoins)
    console.log('Matricule sélectionné:', matricule);

    // Sur mobile, fermer le sidebar après sélection
    if (window.innerWidth <= 767) {
        closeSidebar();
    }

    // Exemple d'utilisation: afficher une alerte
    // alert(`Matricule sélectionné: ${matricule}`);

    // Vous pouvez également appeler une autre fonction avec le matricule
    // processEmployeeMatricule(matricule);
}

// Gestion du menu vertical
function handleSubmenuClick(event) {
    event.preventDefault();
    event.stopPropagation();

    const submenu = event.currentTarget.closest('.submenu');
    submenu.classList.toggle('active');
}

// Gestion de l'ouverture/fermeture du sidebar sur mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

// Fermer le sidebar en cliquant sur l'overlay
function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('active');
}

// Ajuster le sidebar en fonction de la taille de la fenêtre
function handleResize() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const toggleButton = document.getElementById('sidebarToggle');

    if (window.innerWidth >= 768) {
        // Desktop: sidebar toujours visible
        sidebar.classList.add('active');
        mainContent.style.marginLeft = '220px';
        toggleButton.style.display = 'none';
    } else {
        // Mobile: sidebar caché par défaut
        sidebar.classList.remove('active');
        mainContent.style.marginLeft = '0';
        toggleButton.style.display = 'block';
    }
}

// Ajuster le sidebar en fonction de la taille de la fenêtre
function handleResize() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const toggleButton = document.getElementById('sidebarToggle');

    if (window.innerWidth >= 768) {
        sidebar.classList.add('active');
        mainContent.style.marginLeft = '260px';
        toggleButton.style.display = 'none';
    } else {
        sidebar.classList.remove('active');
        mainContent.style.marginLeft = '0';
        toggleButton.style.display = 'flex';
    }

    // Ajustement du texte dans les menus selon la taille
    const menuLinks = document.querySelectorAll('.menu-link span');
    if (window.innerWidth <= 1024) {
        // Sur tablette et mobile, on cache le texte mais garde les icônes
        menuLinks.forEach(span => {
            span.style.display = 'none';
        });
    } else {
        // Sur desktop, on réaffiche le texte
        menuLinks.forEach(span => {
            span.style.display = 'inline';
        });
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Ajouter l'événement de recherche
    document.getElementById('searchInput').addEventListener('input', filterEmployees);

    // Ajouter l'événement de clic à chaque ligne d'employé
    document.querySelectorAll('.employee-row').forEach(row => {
        row.addEventListener('click', handleEmployeeClick);
    });

    // Gestion du bouton hamburger
    document.getElementById('sidebarToggle').addEventListener('click', toggleSidebar);

    // Gestion de l'overlay
    document.getElementById('sidebarOverlay').addEventListener('click', closeSidebar);

    // Gestion du redimensionnement de la fenêtre
    window.addEventListener('resize', handleResize);

    // Initialiser l'état du sidebar
    handleResize();
});
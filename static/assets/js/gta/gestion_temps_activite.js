// static/js/gta/gestion_temps_activite.js

function toggleRattachement() {
    const typeRattachement = document.getElementById('id_type_rattachement');
    const projetDiv = document.getElementById('div_id_projet');
    const tacheDiv = document.getElementById('div_id_tache');

    if (typeRattachement.value === 'PROJET') {
        projetDiv.style.display = 'block';
        tacheDiv.style.display = 'none';
        document.getElementById('id_projet').required = true;
        document.getElementById('id_tache').required = false;
    } else if (typeRattachement.value === 'TACHE') {
        projetDiv.style.display = 'none';
        tacheDiv.style.display = 'block';
        document.getElementById('id_projet').required = false;
        document.getElementById('id_tache').required = true;
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    toggleRattachement();
});


// static/js/absence_manager.js
function validerAbsence(absenceId, decision) {
    const commentaire = prompt("Commentaire (optionnel) :", "");

    if (decision === 'REJETE' && !commentaire) {
        alert("Un commentaire est obligatoire pour rejeter une absence");
        return;
    }

    fetch(`/absence/valider-manager/${absenceId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `decision=${decision}&commentaire=${encodeURIComponent(commentaire || '')}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Erreur: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    });
}

// Fonction utilitaire pour récupérer le token CSRF
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
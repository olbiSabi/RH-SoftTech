//##############################################
//### GESTION DES NOTIFICATIONS HEADER       ###
//##############################################

document.addEventListener('DOMContentLoaded', function() {
    initNotifications();
});

function initNotifications() {
    const notificationBell = document.getElementById('notificationBell');
    const notificationDropdown = document.getElementById('notificationDropdown');

    if (!notificationBell || !notificationDropdown) {
        console.log('ℹ️ Composant notifications non présent sur cette page');
        return;
    }

    console.log('🔔 Initialisation système de notifications');

    const markAllReadBtn = document.getElementById('markAllRead');

    // Toggle dropdown au clic sur la cloche
    notificationBell.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationDropdown.classList.toggle('show');
        console.log('🔔 Toggle notification dropdown');
    });

    // Fermer le dropdown au clic ailleurs
    document.addEventListener('click', function(e) {
        if (!notificationDropdown.contains(e.target) && !notificationBell.contains(e.target)) {
            notificationDropdown.classList.remove('show');
        }
    });

    // Empêcher la fermeture au clic dans le dropdown
    notificationDropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Marquer toutes comme lues
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (!confirm('Marquer toutes les notifications comme lues ?')) {
                return;
            }

            fetch('/absence/notifications/marquer-toutes-lues/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('✅ Toutes les notifications marquées comme lues');
                    location.reload();
                } else {
                    console.error('❌ Erreur:', data.error);
                    alert('Erreur lors du marquage des notifications');
                }
            })
            .catch(error => {
                console.error('❌ Erreur réseau:', error);
                alert('Erreur réseau');
            });
        });
    }

    // Gérer le clic sur une notification
    const notificationItems = document.querySelectorAll('.notification-item');
    console.log(`📋 ${notificationItems.length} notification(s) trouvée(s)`);

    notificationItems.forEach(function(item, index) {
        // Debug au chargement
        console.log(`Notification ${index}:`, {
            id: item.dataset.notificationId,
            link: item.dataset.notificationLink,
            isUnread: item.classList.contains('unread')
        });

        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const notifId = this.dataset.notificationId;
            const notifLink = this.dataset.notificationLink;
            const isUnread = this.classList.contains('unread');

            console.log('═══════════════════════════════════');
            console.log('📌 CLIC SUR NOTIFICATION');
            console.log('ID:', notifId);
            console.log('Lien:', notifLink);
            console.log('Non lue:', isUnread);
            console.log('═══════════════════════════════════');

            // ✅ PAS DE VÉRIFICATION UUID - DIRECTEMENT L'ACTION

            // Si déjà lue, rediriger directement
            if (!isUnread) {
                console.log('ℹ️ Notification déjà lue, redirection');
                if (notifLink && notifLink !== '#') {
                    window.location.href = notifLink;
                }
                return;
            }

            // Construire l'URL
            const url = `/absence/notifications/${notifId}/marquer-lue/`;
            console.log('🌐 URL:', url);

            // Marquer comme lue
            console.log('🔄 Marquage de la notification comme lue...');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                console.log('📥 Réponse, status:', response.status);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(data => {
                console.log('📦 Données:', data);

                if (data.success) {
                    console.log('✅ Notification marquée comme lue');

                    // Animation de disparition
                    item.style.transition = 'all 0.3s ease-out';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(20px)';

                    // Mettre à jour le badge
                    updateBadge(-1);

                    // Supprimer l'élément du DOM
                    setTimeout(function() {
                        item.remove();

                        // Vérifier s'il reste des notifications
                        const remainingNotifs = document.querySelectorAll('.notification-item');
                        if (remainingNotifs.length === 0) {
                            const notificationList = document.querySelector('.notification-list');
                            if (notificationList) {
                                notificationList.innerHTML = `
                                    <div class="notification-empty">
                                        <i class="fas fa-bell-slash"></i>
                                        <p>Aucune nouvelle notification</p>
                                    </div>
                                `;
                            }

                            // Retirer le bouton "Tout marquer comme lu"
                            if (markAllReadBtn) {
                                markAllReadBtn.style.display = 'none';
                            }

                            // Retirer le footer
                            const footer = document.querySelector('.notification-footer');
                            if (footer) {
                                footer.style.display = 'none';
                            }
                        }
                    }, 300);

                    // Rediriger après l'animation
                    setTimeout(function() {
                        if (notifLink && notifLink !== '#') {
                            console.log('🔄 Redirection vers:', notifLink);
                            window.location.href = notifLink;
                        }
                    }, 600);
                } else {
                    console.error('❌ Erreur API:', data.error);
                    alert('Erreur: ' + data.error);
                }
            })
            .catch(error => {
                console.error('❌ ERREUR:', error);
                alert('Erreur: ' + error.message);
            });
        });
    });

    // Fonction pour mettre à jour le badge
    function updateBadge(change) {
        const badge = document.querySelector('.notification-badge');

        if (!badge) {
            console.log('ℹ️ Pas de badge à mettre à jour');
            return;
        }

        let currentCount = parseInt(badge.textContent) || 0;
        console.log('📊 Badge actuel:', currentCount);

        currentCount += change;
        console.log('📊 Nouveau badge:', currentCount);

        if (currentCount <= 0) {
            console.log('🗑️ Suppression du badge');
            badge.remove();
        } else {
            badge.textContent = currentCount;
        }
    }
}

// Fonction utilitaire pour récupérer le CSRF token
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

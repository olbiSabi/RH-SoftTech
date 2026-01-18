// notifications.js
document.addEventListener('DOMContentLoaded', function() {
    const notificationsBtn = document.getElementById('notificationsBtn');
    const notificationsMenu = document.getElementById('notificationsMenu');
    const tabs = document.querySelectorAll('.notification-tab');
    const notificationsList = document.querySelector('.notifications-list');

    // Ouvrir/fermer le menu
    if (notificationsBtn && notificationsMenu) {
        notificationsBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationsMenu.classList.toggle('show');

            // Ajouter classe pour animation
            if (notificationsMenu.classList.contains('show')) {
                notificationsBtn.classList.add('has-new');
            }
        });

        // Fermer en cliquant à l'extérieur
        document.addEventListener('click', function(e) {
            if (!notificationsMenu.contains(e.target) && !notificationsBtn.contains(e.target)) {
                notificationsMenu.classList.remove('show');
                notificationsBtn.classList.remove('has-new');
            }
        });
    }

    // Gestion des onglets
    if (tabs.length > 0 && notificationsList) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabType = this.dataset.tab;

                // Mettre à jour l'onglet actif
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Appliquer le filtre
                notificationsList.className = 'notifications-list';
                if (tabType !== 'all') {
                    notificationsList.classList.add('filter-' + tabType);
                }

                // Sauvegarder le filtre dans localStorage
                localStorage.setItem('notificationTab', tabType);
            });
        });

        // Restaurer le dernier filtre utilisé
        const savedTab = localStorage.getItem('notificationTab') || 'all';
        const tabToActivate = document.querySelector(`.notification-tab[data-tab="${savedTab}"]`);
        if (tabToActivate) {
            tabToActivate.click();
        }
    }

    // Marquer une notification comme lue (AJAX)
    document.querySelectorAll('.notification-mark-read').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const notificationItem = this.closest('.notification-item');
            const notificationId = notificationItem.dataset.notificationId;

            if (notificationId) {
                // Appel AJAX pour marquer comme lue
                fetch(`/absences/notification/${notificationId}/marquer-lue/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        notificationItem.classList.remove('unread');
                        notificationItem.querySelector('.notification-mark-read').remove();

                        // Mettre à jour les compteurs
                        updateNotificationCounts();
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Fonction pour récupérer le token CSRF
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

    // Mettre à jour les compteurs de notifications
    function updateNotificationCounts() {
        // Récupérer les nouvelles données via AJAX
        fetch('/absences/notification/counts/')
            .then(response => response.json())
            .then(data => {
                // Mettre à jour les badges
                document.querySelectorAll('.tab-count').forEach(badge => {
                    const tab = badge.closest('.notification-tab');
                    if (tab) {
                        const tabType = tab.dataset.tab;
                        badge.textContent = data[tabType] || 0;
                    }
                });

                // Mettre à jour le badge principal
                const mainBadge = document.querySelector('.notifications-badge');
                if (mainBadge) {
                    mainBadge.textContent = data.total;
                    if (data.total === 0) {
                        mainBadge.style.display = 'none';
                    } else {
                        mainBadge.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Error updating counts:', error));
    }

    // Mettre à jour périodiquement (toutes les 30 secondes)
    setInterval(updateNotificationCounts, 30000);
});
// ========================================
// GESTION DES NOTIFICATIONS
// ========================================

$(document).ready(function() {
    const notificationsBtn = $('#notificationsBtn');
    const notificationsMenu = $('#notificationsMenu');

    // Toggle menu
    notificationsBtn.on('click', function(e) {
        e.stopPropagation();
        notificationsMenu.toggleClass('show');
    });

    // Fermer le menu en cliquant ailleurs
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.notifications-dropdown').length) {
            notificationsMenu.removeClass('show');
        }
    });

    // Empêcher la fermeture en cliquant dans le menu
    notificationsMenu.on('click', function(e) {
        e.stopPropagation();
    });
});
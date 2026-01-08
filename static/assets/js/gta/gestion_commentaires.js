// static/assets/js/gta/gestion_commentaires.js - VERSION CORRIGÉE

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initCommentaires();
        initFormulaireCommentaire(); // NOUVELLE FONCTION
    });

    function initFormulaireCommentaire() {
    console.log('Initialisation du formulaire de commentaire...');

    // 1. Vérifier si le textarea existe
    const textarea = document.getElementById('id_contenu');
    if (textarea) {
        console.log('Textarea trouvé:', textarea.id);
        initMentionsAutocompleteForTextarea(textarea);
        initEditeurPourTextarea(textarea);
    } else {
        console.error('Textarea non trouvé !');
    }

    // 2. Validation du formulaire
    const form = document.getElementById('commentaire-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const textarea = this.querySelector('textarea[name="contenu"]');
            if (!textarea || !textarea.value.trim()) {
                e.preventDefault();
                alert('Veuillez écrire un commentaire.');
                if (textarea) textarea.focus();
                return false;
            }

            if (textarea.value.trim().length < 2) {
                e.preventDefault();
                alert('Le commentaire doit contenir au moins 2 caractères.');
                textarea.focus();
                return false;
            }
        });
    }
}

    function initMentionsAutocompleteForTextarea(textarea) {
        console.log('Initialisation autocomplete pour:', textarea.id);

        textarea.addEventListener('input', function(e) {
            const cursorPos = this.selectionStart;
            const textBeforeCursor = this.value.substring(0, cursorPos);
            const lastAtIndex = textBeforeCursor.lastIndexOf('@');

            if (lastAtIndex !== -1) {
                const searchText = textBeforeCursor.substring(lastAtIndex + 1);
                const spaceIndex = searchText.indexOf(' ');

                if (spaceIndex === -1 && searchText.length >= 1) {
                    console.log('Recherche mention:', searchText);

                    // Rechercher les correspondances
                    fetch(`/gestion-temps/api/commentaires/mentions/?q=${encodeURIComponent(searchText)}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Erreur réseau');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data && data.length > 0) {
                                console.log('Mentions trouvées:', data.length);
                                showMentionsDropdown(data, lastAtIndex, cursorPos, textarea);
                            }
                        })
                        .catch(error => {
                            console.error('Erreur lors de la recherche des mentions:', error);
                        });
                }
            }
        });
    }

    function showMentionsDropdown(mentions, startIndex, cursorPos, textarea) {
        console.log('Affichage dropdown avec', mentions.length, 'mentions');

        // Supprimer un dropdown existant
        const existingDropdown = document.querySelector('.mentions-dropdown');
        if (existingDropdown) {
            existingDropdown.remove();
        }

        // Créer le dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'mentions-dropdown dropdown-menu show';
        dropdown.style.position = 'absolute';
        dropdown.style.zIndex = '1000';

        mentions.forEach(mention => {
            const item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = '#';
            item.textContent = `${mention.text} (${mention.matricule})`;
            item.style.cursor = 'pointer';
            item.addEventListener('click', function(e) {
                e.preventDefault();

                // Remplacer le texte
                const text = textarea.value;
                const before = text.substring(0, startIndex);
                const after = text.substring(cursorPos);
                textarea.value = before + '@' + mention.text + ' ' + after;

                // Fermer le dropdown
                dropdown.remove();

                // Re-focus sur le textarea
                textarea.focus();
                const newPosition = before.length + mention.text.length + 2;
                textarea.selectionStart = textarea.selectionEnd = newPosition;

                console.log('Mention ajoutée:', mention.text);
            });

            dropdown.appendChild(item);
        });

        // Positionner le dropdown
        const rect = textarea.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        dropdown.style.left = rect.left + 'px';
        dropdown.style.top = (rect.bottom + scrollTop + 5) + 'px';

        document.body.appendChild(dropdown);

        // Fermer le dropdown si on clique ailleurs
        const closeDropdownHandler = function(e) {
            if (!dropdown.contains(e.target) && e.target !== textarea) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdownHandler);
                document.removeEventListener('scroll', closeDropdownHandler);
            }
        };

        document.addEventListener('click', closeDropdownHandler);
        document.addEventListener('scroll', closeDropdownHandler);
    }

    function initEditeurPourTextarea(textarea) {
        console.log('Initialisation éditeur pour:', textarea.id);

        // Ajouter des boutons de formatage simple
        const container = document.createElement('div');
        container.className = 'commentaire-editor-toolbar mb-2';
        container.innerHTML = `
            <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn btn-outline-secondary" data-action="bold" title="Gras">
                    <i class="fas fa-bold"></i>
                </button>
                <button type="button" class="btn btn-outline-secondary" data-action="italic" title="Italique">
                    <i class="fas fa-italic"></i>
                </button>
                <button type="button" class="btn btn-outline-secondary" data-action="code" title="Code">
                    <i class="fas fa-code"></i>
                </button>
                <button type="button" class="btn btn-outline-secondary" data-action="link" title="Lien">
                    <i class="fas fa-link"></i>
                </button>
            </div>
        `;

        textarea.parentNode.insertBefore(container, textarea);

        // Gérer les actions
        container.addEventListener('click', function(e) {
            const button = e.target.closest('button');
            if (!button) return;

            const action = button.dataset.action;
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const selectedText = textarea.value.substring(start, end);

            let insertText = '';
            switch(action) {
                case 'bold':
                    insertText = `**${selectedText}**`;
                    break;
                case 'italic':
                    insertText = `*${selectedText}*`;
                    break;
                case 'code':
                    insertText = `\`${selectedText}\``;
                    break;
                case 'link':
                    const url = prompt('Entrez l\'URL:', 'https://');
                    if (url) {
                        insertText = `[${selectedText || 'lien'}](${url})`;
                    } else {
                        return;
                    }
                    break;
            }

            textarea.value = textarea.value.substring(0, start) +
                             insertText +
                             textarea.value.substring(end);
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = start + insertText.length;
        });
    }

    // Vos fonctions existantes (gardez-les)
    function initCommentaires() {
        console.log('Initialisation des commentaires...');

        // Auto-complete pour les mentions (déjà géré par initFormulaireCommentaire)

        // Validation des formulaires de commentaire
        initCommentaireValidation();

        // Scroll vers un commentaire spécifique
        initCommentaireScrolling();

        // Éditeur enrichi (déjà géré par initEditeurPourTextarea)
    }

    function initCommentaireValidation() {
        const forms = document.querySelectorAll('.commentaire-form');
        console.log('Formulaires trouvés:', forms.length);

        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const textarea = this.querySelector('textarea[name="contenu"]');
                if (textarea && textarea.value.trim().length < 2) {
                    e.preventDefault();
                    alert('Le commentaire doit contenir au moins 2 caractères.');
                    textarea.focus();
                }
            });
        });
    }

    function initCommentaireScrolling() {
        // Si l'URL contient un hash de commentaire, scroll vers ce commentaire
        if (window.location.hash && window.location.hash.startsWith('#commentaire-')) {
            const commentaire = document.querySelector(window.location.hash);
            if (commentaire) {
                setTimeout(() => {
                    commentaire.scrollIntoView({ behavior: 'smooth' });
                    commentaire.classList.add('commentaire-highlight');
                    setTimeout(() => {
                        commentaire.classList.remove('commentaire-highlight');
                    }, 2000);
                }, 500);
            }
        }
    }

})();
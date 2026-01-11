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
            item.textContent = `${mention.text}`;
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

    // Créer l'éditeur WYSIWYG
    const editor = document.createElement('div');
    editor.className = 'wysiwyg-editor border p-2 rounded bg-white';
    editor.contentEditable = true;
    editor.style.minHeight = textarea.rows * 24 + 'px';
    editor.style.fontFamily = 'inherit';
    editor.style.lineHeight = '1.5';
    editor.innerHTML = textarea.value.replace(/\n/g, '<br>');

    // Cacher le textarea original mais le garder pour le formulaire
    textarea.style.display = 'none';
    textarea.parentNode.insertBefore(editor, textarea.nextSibling);

    // Synchroniser avec le textarea caché
    function updateTextarea() {
        // Nettoyer le HTML pour garder seulement les balises autorisées
        const cleanHTML = editor.innerHTML
            .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
            .replace(/<b>(.*?)<\/b>/g, '**$1**')
            .replace(/<em>(.*?)<\/em>/g, '*$1*')
            .replace(/<i>(.*?)<\/i>/g, '*$1*')
            .replace(/<code>(.*?)<\/code>/g, '`$1`')
            .replace(/<br>/g, '\n')
            .replace(/<\/div>|<\/p>/g, '\n')
            .replace(/<div>|<p>/g, '');

        textarea.value = cleanHTML;
    }

    editor.addEventListener('input', updateTextarea);
    editor.addEventListener('blur', updateTextarea);

    // Barre d'outils
    const container = document.createElement('div');
    container.className = 'commentaire-editor-toolbar mb-2';
    container.innerHTML = `
        <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-secondary" data-command="bold" title="Gras">
                <i class="fas fa-bold"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary" data-command="italic" title="Italique">
                <i class="fas fa-italic"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary" data-command="code" title="Code">
                <i class="fas fa-code"></i>
            </button>
        </div>
    `;

    textarea.parentNode.insertBefore(container, textarea);

    // Fonction pour vérifier si la sélection est déjà en code
    function isSelectionInCode() {
        const selection = window.getSelection();
        if (selection.rangeCount === 0) return false;

        let node = selection.anchorNode;
        while (node && node !== editor) {
            if (node.nodeType === Node.ELEMENT_NODE &&
                (node.tagName === 'CODE' || node.parentElement?.tagName === 'CODE')) {
                return true;
            }
            node = node.parentElement;
        }
        return false;
    }

    // Fonction pour appliquer/enlever le code
    function toggleCode() {
        const selection = window.getSelection();
        if (selection.rangeCount === 0) return;

        const range = selection.getRangeAt(0);

        if (isSelectionInCode()) {
            // Si déjà en code, on enlève les balises <code>
            const codeContent = range.commonAncestorContainer;
            if (codeContent.parentElement?.tagName === 'CODE') {
                const codeElement = codeContent.parentElement;
                const parent = codeElement.parentElement;

                // Remplacer <code>contenu</code> par juste "contenu"
                const fragment = document.createDocumentFragment();
                while (codeElement.firstChild) {
                    fragment.appendChild(codeElement.firstChild);
                }

                parent.replaceChild(fragment, codeElement);
                selection.selectAllChildren(fragment);
            }
        } else {
            // Si pas en code, on ajoute les balises
            if (selection.toString()) {
                // Texte sélectionné
                document.execCommand('insertHTML', false, `<code>${selection.toString()}</code>`);
            } else {
                // Aucune sélection, on insère des balises vides avec placeholder
                document.execCommand('insertHTML', false, '<code>code</code>');
                // Sélectionner le texte "code" pour qu'il soit facile à remplacer
                const codeElements = editor.getElementsByTagName('code');
                if (codeElements.length > 0) {
                    const lastCode = codeElements[codeElements.length - 1];
                    const range = document.createRange();
                    range.selectNodeContents(lastCode);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }
        }
    }

    // Gestion des boutons
    container.addEventListener('click', function(e) {
        const button = e.target.closest('button');
        if (!button) return;

        editor.focus();
        const command = button.dataset.command;

        if (command === 'code') {
            toggleCode();
        } else {
            document.execCommand(command, false, null);
        }

        updateTextarea();
    });

    // Amélioration : mettre en surbrillance les boutons actifs
    editor.addEventListener('input', function() {
        const buttons = container.querySelectorAll('button');
        buttons.forEach(btn => {
            const cmd = btn.dataset.command;
            if (cmd === 'bold') {
                btn.classList.toggle('active', document.queryCommandState('bold'));
            } else if (cmd === 'italic') {
                btn.classList.toggle('active', document.queryCommandState('italic'));
            } else if (cmd === 'code') {
                btn.classList.toggle('active', isSelectionInCode());
            }
        });
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

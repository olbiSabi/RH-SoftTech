// assets/js/gta/mentions-autocomplete.js
class MentionsAutocomplete {
    constructor(textareaId) {
        this.textarea = document.getElementById(textareaId);
        this.suggestionsContainer = null;
        this.currentSuggestions = [];
        this.currentQuery = '';

        if (this.textarea) {
            this.init();
        }
    }

    init() {
        // Écouter les frappes
        this.textarea.addEventListener('input', this.handleInput.bind(this));

        // Écouter les touches pour la navigation
        this.textarea.addEventListener('keydown', this.handleKeydown.bind(this));

        // Fermer les suggestions en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (this.suggestionsContainer && !this.suggestionsContainer.contains(e.target) && e.target !== this.textarea) {
                this.closeSuggestions();
            }
        });
    }

    handleInput(e) {
        const cursorPos = this.textarea.selectionStart;
        const text = this.textarea.value;
        const textBeforeCursor = text.substring(0, cursorPos);

        // Vérifier si on tape '@'
        const atMatch = textBeforeCursor.match(/@(\w*)$/);

        if (atMatch) {
            this.currentQuery = atMatch[1];
            this.fetchSuggestions(this.currentQuery);
        } else {
            this.closeSuggestions();
        }
    }

    handleKeydown(e) {
        if (!this.suggestionsContainer) return;

        const items = this.suggestionsContainer.querySelectorAll('.mention-suggestion');
        const activeItem = this.suggestionsContainer.querySelector('.mention-suggestion.active');
        let activeIndex = -1;

        if (activeItem) {
            activeIndex = Array.from(items).indexOf(activeItem);
        }

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (activeIndex < items.length - 1) {
                    this.setActiveItem(activeIndex + 1);
                } else {
                    this.setActiveItem(0);
                }
                break;

            case 'ArrowUp':
                e.preventDefault();
                if (activeIndex > 0) {
                    this.setActiveItem(activeIndex - 1);
                } else {
                    this.setActiveItem(items.length - 1);
                }
                break;

            case 'Enter':
            case 'Tab':
                if (activeItem) {
                    e.preventDefault();
                    this.selectSuggestion(activeItem);
                }
                break;

            case 'Escape':
                this.closeSuggestions();
                break;
        }
    }

    async fetchSuggestions(query) {
        const tacheId = window.location.pathname.split('/').filter(p => p)[3]; // Extraire l'ID de la tâche
        const url = `/gestion-temps/api/mentions/employes/?q=${encodeURIComponent(query)}&tache_id=${tacheId}`;

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (data.length > 0) {
                this.showSuggestions(data);
            } else {
                this.closeSuggestions();
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des suggestions:', error);
        }
    }

    showSuggestions(employes) {
        this.currentSuggestions = employes;

        // Créer ou mettre à jour le conteneur
        if (!this.suggestionsContainer) {
            this.suggestionsContainer = document.createElement('div');
            this.suggestionsContainer.className = 'mention-suggestions';
            document.body.appendChild(this.suggestionsContainer);
        }

        // Remplir les suggestions
        this.suggestionsContainer.innerHTML = '';

        employes.forEach((employe, index) => {
            const item = document.createElement('div');
            item.className = 'mention-suggestion';
            if (index === 0) item.classList.add('active');

            item.innerHTML = `
                <div class="mention-suggestion-content">
                    <img src="${employe.photo_url || '/static/assets/img/default-avatar.png'}"
                         alt="${employe.full_name}"
                         class="mention-avatar"
                         width="24" height="24">
                    <div class="mention-info">
                        <strong>${employe.full_name}</strong>
                        <small>${employe.departement || ''}</small>
                    </div>
                </div>
            `;

            item.addEventListener('click', () => this.selectSuggestion(item));
            item.addEventListener('mouseenter', () => this.setActiveItem(index));

            this.suggestionsContainer.appendChild(item);
        });

        // Positionner le conteneur
        this.positionSuggestions();
    }

    positionSuggestions() {
        const rect = this.textarea.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        this.suggestionsContainer.style.position = 'absolute';
        this.suggestionsContainer.style.top = `${rect.bottom + scrollTop}px`;
        this.suggestionsContainer.style.left = `${rect.left}px`;
        this.suggestionsContainer.style.width = `${rect.width}px`;
        this.suggestionsContainer.style.display = 'block';
    }

    setActiveItem(index) {
        const items = this.suggestionsContainer.querySelectorAll('.mention-suggestion');
        items.forEach(item => item.classList.remove('active'));
        items[index].classList.add('active');
        items[index].scrollIntoView({ block: 'nearest' });
    }

    selectSuggestion(item) {
        const index = Array.from(this.suggestionsContainer.querySelectorAll('.mention-suggestion')).indexOf(item);
        const employe = this.currentSuggestions[index];

        if (employe) {
            this.insertMention(employe.full_name);
            this.closeSuggestions();
        }
    }

    insertMention(fullName) {
        const cursorPos = this.textarea.selectionStart;
        const text = this.textarea.value;

        // Trouver la position du dernier '@'
        const textBeforeCursor = text.substring(0, cursorPos);
        const lastAtPos = textBeforeCursor.lastIndexOf('@');

        if (lastAtPos !== -1) {
            // Remplacer depuis le '@'
            const newText = text.substring(0, lastAtPos) + `@${fullName} ` + text.substring(cursorPos);
            this.textarea.value = newText;

            // Positionner le curseur après la mention
            const newCursorPos = lastAtPos + fullName.length + 2; // +2 pour le '@' et l'espace
            this.textarea.selectionStart = newCursorPos;
            this.textarea.selectionEnd = newCursorPos;
            this.textarea.focus();
        }
    }

    closeSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.remove();
            this.suggestionsContainer = null;
        }
        this.currentSuggestions = [];
    }
}

// Initialiser pour chaque textarea de commentaire
document.addEventListener('DOMContentLoaded', function() {
    const commentTextareas = [
        'commentaire_contenu',
        'reponse_contenu',
        'commentaire_contenu_modifier'
    ];

    commentTextareas.forEach(id => {
        if (document.getElementById(id)) {
            new MentionsAutocomplete(id);
        }
    });
});
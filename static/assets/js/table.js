// Recherche en temps réel
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('tableBody');

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = tableBody.querySelectorAll('tr:not(.empty-state)');
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Afficher un message si aucun résultat
            const emptyStates = tableBody.querySelectorAll('.empty-state');
            const searchEmpty = tableBody.querySelector('.search-empty');

            if (visibleCount === 0 && rows.length > 0 && !searchEmpty) {
                const emptyRow = document.createElement('tr');
                emptyRow.className = 'empty-state search-empty';
                emptyRow.innerHTML = `
                    <td colspan="6">
                        <div>
                            <span style="font-size: 3em;">🔍</span>
                            <p>Aucun résultat trouvé pour "${searchTerm}"</p>
                        </div>
                    </td>
                `;
                tableBody.appendChild(emptyRow);
            } else if (visibleCount > 0 && searchEmpty) {
                searchEmpty.remove();
            }
        });

        // Auto-focus sur le premier champ si le formulaire a des erreurs
        {% if form.errors %}
        window.addEventListener('DOMContentLoaded', function() {
            const firstErrorField = document.querySelector('.field-error').previousElementSibling;
            if (firstErrorField) {
                firstErrorField.focus();
            }
        });
        {% endif %}
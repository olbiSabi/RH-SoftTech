
/**
 * Gestion du formulaire d'absence avec support des demi-journées
 */
console.log('📄 ========================================');
console.log('📄 FICHIER CHARGÉ : absence_form.js (FORMULAIRE)');
console.log('📄 ========================================');
// ===== VARIABLES GLOBALES =====
let calendar;
let employe_id;
let flatpickrDebut, flatpickrFin;
let types_absence = {};
let currentTypeInfo = null;

// ===== INITIALISATION =====
document.addEventListener('DOMContentLoaded', function() {
    const employeInput = document.getElementById('employe_matricule');
    employe_id = employeInput ? employeInput.value : null;

    console.log('🔧 Initialisation formulaire absence');
    console.log('Employé:', employe_id);

    loadTypesAbsence();
    initMiniCalendar();
    initDatePickers();

    if (employe_id) {
        loadSolde(employe_id);
    }

    const typeSelect = document.getElementById('id_type_absence');
    if (typeSelect) {
        typeSelect.addEventListener('change', onTypeAbsenceChange);
        if (typeSelect.value) {
            onTypeAbsenceChange.call(typeSelect);
        }
    }

    const dateDebutInput = document.getElementById('id_date_debut');
    if (dateDebutInput) {
        dateDebutInput.addEventListener('change', onDatesChange);
    }

    const dateFinInput = document.getElementById('id_date_fin');
    if (dateFinInput) {
        dateFinInput.addEventListener('change', onDatesChange);
    }

    // ✅ UN SEUL EVENT LISTENER : periode (pas periode_debut/periode_fin)
    const periodeSelect = document.getElementById('id_periode');
    if (periodeSelect) {
        periodeSelect.addEventListener('change', onDatesChange);
    }

    const form = document.getElementById('absenceForm');
    if (form) {
        form.addEventListener('submit', validateForm);
    }
});
// Écouter les changements de dates
document.getElementById('id_date_debut').addEventListener('change', verifierPeriode);
document.getElementById('id_date_fin').addEventListener('change', verifierPeriode);

function loadTypesAbsence() {
    const select = document.getElementById('id_type_absence');
    if (!select) return;

    Array.from(select.options).forEach(option => {
        if (option.value) {
            types_absence[option.value] = {
                nom: option.text,
            };
        }
    });
}

function initMiniCalendar() {
    const calendarEl = document.getElementById('miniCalendar');
    if (!calendarEl) return;

    calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'fr',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: 'today'
        },
        buttonText: {
            today: "Aujourd'hui"
        },
        height: 'auto',
        selectable: true,
        selectMirror: true,
        select: function(info) {
            const startDate = info.startStr;
            let endDate = new Date(info.end);
            endDate.setDate(endDate.getDate() - 1);
            const endDateStr = endDate.toISOString().split('T')[0];

            if (flatpickrDebut) {
                flatpickrDebut.setDate(startDate);
            } else {
                document.getElementById('id_date_debut').value = startDate;
            }

            if (flatpickrFin) {
                flatpickrFin.setDate(endDateStr);
            } else {
                document.getElementById('id_date_fin').value = endDateStr;
            }

            onDatesChange();
        },
        events: function(info, successCallback, failureCallback) {
            if (!employe_id) {
                successCallback([]);
                return;
            }
            loadAbsencesForCalendar(employe_id, info.start, info.end, successCallback, failureCallback);
        },
        eventClassNames: function(arg) {
            const statut = arg.event.extendedProps.statut;
            if (statut === 'VALIDE') {
                return ['event-valide'];
            } else if (statut && statut.includes('ATTENTE')) {
                return ['event-attente'];
            }
            return [];
        },
        dayCellClassNames: function(arg) {
            if (arg.date.getDay() === 0 || arg.date.getDay() === 6) {
                return ['weekend-cell'];
            }
            return [];
        }
    });

    calendar.render();
}

function loadAbsencesForCalendar(employeId, start, end, successCallback, failureCallback) {
    fetch(`/absence/api/mes-absences-calendrier/?start=${start.toISOString()}&end=${end.toISOString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const events = data.absences.map(abs => {
                    let endDate = new Date(abs.date_fin);
                    endDate.setDate(endDate.getDate() + 1);

                    return {
                        title: abs.type_absence + ' (' + abs.jours_ouvrables + 'j)',
                        start: abs.date_debut,
                        end: endDate.toISOString().split('T')[0],
                        backgroundColor: abs.couleur || '#ffc107',
                        borderColor: abs.couleur || '#ffc107',
                        extendedProps: {
                            statut: abs.statut
                        }
                    };
                });
                successCallback(events);
            } else {
                successCallback([]);
            }
        })
        .catch(error => {
            console.error('Erreur chargement absences:', error);
            successCallback([]);
        });
}

function initDatePickers() {
    flatpickrDebut = flatpickr("#id_date_debut", {
        locale: "fr",
        dateFormat: "Y-m-d",
        minDate: "today",
        onChange: function(selectedDates, dateStr) {
            if (flatpickrFin) {
                flatpickrFin.set('minDate', dateStr);
            }
            if (calendar) {
                calendar.gotoDate(dateStr);
            }
            onDatesChange();
        }
    });

    flatpickrFin = flatpickr("#id_date_fin", {
        locale: "fr",
        dateFormat: "Y-m-d",
        minDate: "today",
        onChange: function() {
            onDatesChange();
        }
    });
}

function onTypeAbsenceChange() {
    const typeId = this.value;

    if (!typeId) {
        document.getElementById('type-info').textContent = '';
        document.getElementById('justificatif-obligatoire').style.display = 'none';

        const alertJustif = document.getElementById('justificatif-required-alert');
        if (alertJustif) {
            alertJustif.style.display = 'none';
        }

        currentTypeInfo = null;
        return;
    }

    fetch(`/absence/api/type/${typeId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const type = data.data;
                currentTypeInfo = type;

                let info = '';
                if (type.decompte_solde) {
                    info += '📊 Déduit du solde de congés';
                }
                if (type.justificatif_obligatoire) {
                    if (info) info += ' • ';
                    info += '⚠️ Justificatif obligatoire';
                }
                document.getElementById('type-info').textContent = info;

                const obligatoire = document.getElementById('justificatif-obligatoire');
                if (obligatoire) {
                    obligatoire.style.display = type.justificatif_obligatoire ? 'inline' : 'none';
                }

                const alertJustif = document.getElementById('justificatif-required-alert');
                if (alertJustif) {
                    alertJustif.style.display = type.justificatif_obligatoire ? 'block' : 'none';
                }

                const justificatifInput = document.getElementById('id_justificatif');
                if (justificatifInput) {
                    if (type.justificatif_obligatoire) {
                        justificatifInput.setAttribute('required', 'required');
                    } else {
                        justificatifInput.removeAttribute('required');
                    }
                }

                window.currentTypeDecompteSolde = type.decompte_solde;
                window.currentTypeJustificatifObligatoire = type.justificatif_obligatoire;

                onDatesChange();
            }
        })
        .catch(error => console.error('Erreur:', error));
}

function onDatesChange() {
    const dateDebut = document.getElementById('id_date_debut').value;
    const dateFin = document.getElementById('id_date_fin').value;

    // ✅ UN SEUL SELECT : periode (pas periode_debut/periode_fin)
    const periodeSelect = document.getElementById('id_periode');

    if (!dateDebut || !dateFin || !periodeSelect) {
        return;
    }

    const isSameDay = (dateDebut === dateFin);

    // ✅ Si plusieurs jours, désactiver et forcer "Journée complète"
    if (!isSameDay) {
        periodeSelect.value = 'JOURNEE_COMPLETE';
        periodeSelect.disabled = true;

        const periodeInfo = document.getElementById('periode-info');
        if (periodeInfo) {
            periodeInfo.style.display = 'block';
        }
    } else {
        // Réactiver pour un seul jour
        periodeSelect.disabled = false;

        const periodeInfo = document.getElementById('periode-info');
        if (periodeInfo) {
            periodeInfo.style.display = 'none';
        }
    }

    const periode = periodeSelect.value;

    // Calculer les jours
    const jours = calculateBusinessDaysWithPeriod(dateDebut, dateFin, periode);
    document.getElementById('jours-calcules').textContent = jours;
    document.getElementById('duree-info').style.display = 'block';

    // Vérifier le solde SEULEMENT si le type décompte le solde
    if (employe_id && window.currentTypeDecompteSolde) {
        verifierSoldeAvecJours(employe_id, dateDebut, dateFin, jours);
    } else {
        document.getElementById('solde-info').style.display = 'none';
        document.getElementById('solde-insuffisant').style.display = 'none';
        document.getElementById('submitBtn').disabled = false;
    }

    // Mettre à jour le calendrier
    if (calendar) {
        calendar.getEvents().forEach(event => {
            if (event.display === 'background') {
                event.remove();
            }
        });

        let endDateForCalendar = new Date(dateFin);
        endDateForCalendar.setDate(endDateForCalendar.getDate() + 1);

        calendar.addEvent({
            start: dateDebut,
            end: endDateForCalendar.toISOString().split('T')[0],
            display: 'background',
            backgroundColor: '#17a2b8',
            classNames: ['selected-period']
        });
    }
}

// ✅ Calcul simplifié avec UN SEUL champ période
function calculateBusinessDaysWithPeriod(startDate, endDate, periode) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    let jours = 0;
    let current = new Date(start);

    while (current <= end) {
        const day = current.getDay();

        if (day !== 0 && day !== 6) {
            // Même jour : Tenir compte de la période
            if (start.getTime() === end.getTime()) {
                if (periode === 'JOURNEE_COMPLETE') {
                    jours += 1;
                } else {
                    jours += 0.5;  // MATIN ou APRES_MIDI
                }
            }
            // Plusieurs jours : Toujours journée complète
            else {
                jours += 1;
            }
        }

        current.setDate(current.getDate() + 1);
    }

    return jours.toFixed(1);
}

function verifierSoldeAvecJours(employeId, dateDebut, dateFin, joursCalcules) {
    const anneeAbsence = new Date(dateDebut).getFullYear();
    const anneeAcquisition = anneeAbsence - 1;

    fetch(`/absence/api/acquisition-employe/${employeId}/${anneeAcquisition}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const soldeDisponible = parseFloat(data.data.jours_restants);

                document.getElementById('solde-disponible').textContent = soldeDisponible.toFixed(1);
                document.getElementById('annee-acquisition').textContent = anneeAcquisition;
                document.getElementById('solde-info').style.display = 'block';

                const soldeInsuffisant = document.getElementById('solde-insuffisant');
                const submitBtn = document.getElementById('submitBtn');

                if (soldeDisponible <= 0) {
                    document.getElementById('jours-demandes').textContent = joursCalcules;
                    document.getElementById('jours-disponibles').textContent = '0';
                    soldeInsuffisant.innerHTML = `
                        <i class="fas fa-times-circle"></i>
                        <strong>Aucun jour de congé disponible !</strong><br>
                        Vous n'avez aucun jour de congé pour l'année ${anneeAcquisition}.
                    `;
                    soldeInsuffisant.style.display = 'block';
                    submitBtn.disabled = true;
                } else if (joursCalcules > soldeDisponible) {
                    document.getElementById('jours-demandes').textContent = joursCalcules;
                    document.getElementById('jours-disponibles').textContent = soldeDisponible.toFixed(1);
                    soldeInsuffisant.innerHTML = `
                        <i class="fas fa-times-circle"></i>
                        <strong>Solde insuffisant !</strong><br>
                        Vous demandez <strong>${joursCalcules} jours</strong> mais vous n'avez que
                        <strong>${soldeDisponible.toFixed(1)} jours</strong> disponibles.
                    `;
                    soldeInsuffisant.style.display = 'block';
                    submitBtn.disabled = true;
                } else {
                    soldeInsuffisant.style.display = 'none';
                    submitBtn.disabled = false;
                }
            } else {
                document.getElementById('solde-info').style.display = 'none';
                const soldeInsuffisant = document.getElementById('solde-insuffisant');
                const anneeAcquisition = new Date(dateDebut).getFullYear() - 1;
                soldeInsuffisant.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Aucune acquisition de congés trouvée !</strong><br>
                    Vous n'avez pas de solde de congés pour l'année ${anneeAcquisition}.
                `;
                soldeInsuffisant.style.display = 'block';
                document.getElementById('submitBtn').disabled = true;
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            document.getElementById('solde-info').style.display = 'none';
        });
}

// ✅ Validation avant soumission
function validateForm(event) {
    const errors = [];

    console.log('🔍 Validation du formulaire...');

    const dateDebut = document.getElementById('id_date_debut').value;
    const dateFin = document.getElementById('id_date_fin').value;
    const periodeSelect = document.getElementById('id_periode');

    // ✅ 0. VALIDATION : Date de fin >= Date de début
    if (dateDebut && dateFin) {
        const debut = new Date(dateDebut);
        const fin = new Date(dateFin);

        if (fin < debut) {
            errors.push('La date de fin ne peut pas être antérieure à la date de début');
        }
    }

    // ✅ 1. CRITIQUE : Forcer "JOURNEE_COMPLETE" pour plusieurs jours
    if (dateDebut && dateFin && dateDebut !== dateFin) {
        periodeSelect.disabled = false;
        periodeSelect.value = 'JOURNEE_COMPLETE';
        console.log('✅ Période forcée à JOURNEE_COMPLETE pour plusieurs jours');
    }

    // 2. Vérifier le justificatif si obligatoire
    if (currentTypeInfo && currentTypeInfo.justificatif_obligatoire) {
        const justificatifInput = document.getElementById('id_justificatif');
        const hasExistingFile = document.querySelector('a[href*="justificatif"]');

        if (!justificatifInput.files.length && !hasExistingFile) {
            errors.push('Un justificatif est obligatoire pour ce type d\'absence');
        }
    }

    // 3. Vérifier le solde si type avec décompte
    if (currentTypeInfo && currentTypeInfo.decompte_solde) {
        const soldeInsuffisant = document.getElementById('solde-insuffisant');
        if (soldeInsuffisant && soldeInsuffisant.style.display !== 'none') {
            errors.push('Solde de congés insuffisant');
        }
    }

    // Afficher les erreurs
    if (errors.length > 0) {
        event.preventDefault();

        console.log('❌ Erreurs de validation:', errors);

        const errorHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <h5><i class="fas fa-exclamation-triangle"></i> Erreurs de validation</h5>
                <ul class="mb-0">
                    ${errors.map(err => `<li>${err}</li>`).join('')}
                </ul>
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            </div>
        `;

        const cardBody = document.querySelector('#absenceForm .card-body');
        const existingAlert = cardBody.querySelector('.alert-danger.fade.show');
        if (existingAlert) {
            existingAlert.remove();
        }
        cardBody.insertAdjacentHTML('afterbegin', errorHtml);

        cardBody.scrollIntoView({ behavior: 'smooth', block: 'start' });

        return false;
    }

    console.log('✅ Validation réussie');
    return true;
}

function loadSolde(employeId) {
    const anneeAcquisition = new Date().getFullYear() - 1;

    console.log(`🔍 Chargement solde: ${employeId}, année: ${anneeAcquisition}`);

    fetch(`/absence/api/acquisition-employe/${employeId}/${anneeAcquisition}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 Données solde reçues:', data);

            if (data.success) {
                const acq = data.data;
                document.getElementById('solde-acquis').textContent = acq.jours_acquis;
                document.getElementById('solde-pris').textContent = acq.jours_pris;
                document.getElementById('solde-restant').textContent = acq.jours_restants;
            } else {
                console.warn('❌ API retourne success: false', data.error);
                document.getElementById('solde-acquis').textContent = '0.00';
                document.getElementById('solde-pris').textContent = '0.00';
                document.getElementById('solde-restant').textContent = '0.00';

                // Afficher un message d'information
                const soldeCard = document.querySelector('.solde-card');
                if (soldeCard) {
                    soldeCard.innerHTML += `
                        <div class="alert alert-warning mt-2 mb-0">
                            <i class="fas fa-info-circle"></i>
                            Pas d'acquisition trouvée pour ${anneeAcquisition}.
                            Une acquisition sera créée automatiquement.
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            console.error('❌ Erreur chargement solde:', error);
            document.getElementById('solde-acquis').textContent = '-';
            document.getElementById('solde-pris').textContent = '-';
            document.getElementById('solde-restant').textContent = '-';
        });
}

function verifierSoldeAvecJours(employeId, dateDebut, dateFin, joursCalcules) {
    const anneeAbsence = new Date(dateDebut).getFullYear();
    const anneeAcquisition = anneeAbsence - 1;

    console.log(`🔍 Vérification solde: ${employeId}, année: ${anneeAcquisition}, jours: ${joursCalcules}`);

    fetch(`/absence/api/acquisition-employe/${employeId}/${anneeAcquisition}/`)
        .then(response => {
            if (!response.ok) {
                // Si 404 ou 400, on considère que le solde est 0
                return {
                    success: false,
                    data: { jours_restants: "0.00" }
                };
            }
            return response.json();
        })
        .then(data => {
            let soldeDisponible;

            if (data.success) {
                soldeDisponible = parseFloat(data.data.jours_restants);
                console.log(`✅ Solde disponible: ${soldeDisponible}`);
            } else {
                // Si pas d'acquisition, solde = 0
                soldeDisponible = 0.00;
                console.log('⚠️ Pas d\'acquisition, solde = 0');
            }

            document.getElementById('solde-disponible').textContent = soldeDisponible.toFixed(1);
            document.getElementById('annee-acquisition').textContent = anneeAcquisition;
            document.getElementById('solde-info').style.display = 'block';

            const soldeInsuffisant = document.getElementById('solde-insuffisant');
            const submitBtn = document.getElementById('submitBtn');

            if (soldeDisponible <= 0) {
                document.getElementById('jours-demandes').textContent = joursCalcules;
                document.getElementById('jours-disponibles').textContent = '0';
                soldeInsuffisant.innerHTML = `
                    <i class="fas fa-times-circle"></i>
                    <strong>Aucun jour de congé disponible !</strong><br>
                    Vous n'avez aucun jour de congé pour l'année ${anneeAcquisition}.
                    ${!data.success ? '<br><small><i class="fas fa-info-circle"></i> Aucune acquisition trouvée</small>' : ''}
                `;
                soldeInsuffisant.style.display = 'block';
                submitBtn.disabled = true;
            } else if (parseFloat(joursCalcules) > soldeDisponible) {
                document.getElementById('jours-demandes').textContent = joursCalcules;
                document.getElementById('jours-disponibles').textContent = soldeDisponible.toFixed(1);
                soldeInsuffisant.innerHTML = `
                    <i class="fas fa-times-circle"></i>
                    <strong>Solde insuffisant !</strong><br>
                    Vous demandez <strong>${joursCalcules} jours</strong> mais vous n'avez que
                    <strong>${soldeDisponible.toFixed(1)} jours</strong> disponibles.
                `;
                soldeInsuffisant.style.display = 'block';
                submitBtn.disabled = true;
            } else {
                soldeInsuffisant.style.display = 'none';
                submitBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('❌ Erreur vérification solde:', error);
            document.getElementById('solde-info').style.display = 'none';

            // En cas d'erreur, autoriser quand même la soumission
            // avec un avertissement
            const soldeInsuffisant = document.getElementById('solde-insuffisant');
            if (soldeInsuffisant) {
                soldeInsuffisant.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Attention :</strong> Impossible de vérifier le solde.<br>
                        Votre demande sera soumise, mais le solde sera vérifié lors de la validation.
                    </div>
                `;
                soldeInsuffisant.style.display = 'block';
            }

            document.getElementById('submitBtn').disabled = false;
        });
}

function verifierPeriode() {
    const dateDebut = document.getElementById('id_date_debut').value;
    const dateFin = document.getElementById('id_date_fin').value;
    const periodeSelect = document.getElementById('id_periode');
    const periodeInfo = document.getElementById('periode-info');

    if (dateDebut && dateFin && dateDebut !== dateFin) {
        // ✅ Plusieurs jours : forcer JOURNEE_COMPLETE et désactiver
        periodeSelect.value = 'JOURNEE_COMPLETE';
        periodeSelect.disabled = true;

        // Afficher message info
        if (periodeInfo) {
            periodeInfo.style.display = 'block';
        }

        console.log('✅ Plusieurs jours détectés, période forcée à JOURNEE_COMPLETE');
    } else {
        // Un seul jour : réactiver le choix
        periodeSelect.disabled = false;

        // Masquer message info
        if (periodeInfo) {
            periodeInfo.style.display = 'none';
        }

        console.log('✅ Un seul jour, choix de période disponible');
    }
}

// Appeler au chargement de la page
document.addEventListener('DOMContentLoaded', verifierPeriode);
/**
 * PlanningApp - Module principal du calendrier planning.
 * Utilise FullCalendar 6.1.10 + Bootstrap 4 modals + Toastr.
 */
const PlanningApp = (function() {
    'use strict';

    let calendar;
    const config = window.PLANNING_CONFIG;

    // ===== INITIALISATION =====

    function init() {
        // Toastr config
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: 'toast-top-right',
            timeOut: 5000
        };

        populateSelects();
        initCalendar();
    }

    function populateSelects() {
        // Plannings
        var selPlanning = document.getElementById('affPlanning');
        if (selPlanning) {
            config.plannings.forEach(function(p) {
                var opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.reference + ' - ' + p.titre;
                selPlanning.appendChild(opt);
            });
        }

        // Employes (affectation)
        var selEmploye = document.getElementById('affEmploye');
        if (selEmploye) {
            config.employes.forEach(function(e) {
                var opt = document.createElement('option');
                opt.value = e.matricule;
                opt.textContent = e.matricule + ' - ' + e.nom + ' ' + e.prenoms;
                selEmploye.appendChild(opt);
            });
        }

        // Employes (evenement - multi-select)
        var selEvtEmployes = document.getElementById('evtEmployes');
        if (selEvtEmployes) {
            config.employes.forEach(function(e) {
                var opt = document.createElement('option');
                opt.value = e.matricule;
                opt.textContent = e.matricule + ' - ' + e.nom + ' ' + e.prenoms;
                selEvtEmployes.appendChild(opt);
            });
        }

        // Sites
        var selSite = document.getElementById('affSite');
        if (selSite) {
            config.sites.forEach(function(s) {
                var opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.nom;
                selSite.appendChild(opt);
            });
        }

        // Postes (tous par defaut)
        loadPostesLocal();
    }

    function loadPostesLocal(siteId) {
        var selPoste = document.getElementById('affPoste');
        if (!selPoste) return;

        // Garder le premier option
        selPoste.innerHTML = '<option value="">-- Choisir --</option>';

        var postes = config.postes;
        if (siteId) {
            postes = postes.filter(function(p) { return p.site_id == siteId; });
        }

        postes.forEach(function(p) {
            var opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.nom + ' (' + p.site_nom + ')';
            opt.dataset.heureDebut = p.heure_debut;
            opt.dataset.heureFin = p.heure_fin;
            selPoste.appendChild(opt);
        });
    }

    function loadPostes(siteId) {
        if (!siteId) {
            loadPostesLocal();
            return;
        }

        var url = config.urls.postesBySite.replace('{site_id}', siteId);
        fetch(url, { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var selPoste = document.getElementById('affPoste');
                selPoste.innerHTML = '<option value="">-- Choisir --</option>';
                if (data.success && data.postes) {
                    data.postes.forEach(function(p) {
                        var opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = p.nom;
                        opt.dataset.heureDebut = p.heure_debut;
                        opt.dataset.heureFin = p.heure_fin;
                        selPoste.appendChild(opt);
                    });
                }
            })
            .catch(function() {
                loadPostesLocal(siteId);
            });
    }

    // ===== CALENDRIER =====

    function initCalendar() {
        var el = document.getElementById('planningCalendar');
        if (!el) return;

        calendar = new FullCalendar.Calendar(el, {
            locale: 'fr',
            initialView: 'timeGridWeek',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            slotMinTime: '06:00:00',
            slotMaxTime: '22:00:00',
            nowIndicator: true,
            selectable: config.canEdit,
            firstDay: 1,
            allDaySlot: true,
            height: 'auto',
            slotDuration: '00:30:00',
            eventSources: [
                { events: fetchAffectations },
                { events: fetchEvenements }
            ],
            eventClick: handleEventClick,
            select: handleDateSelect,
            eventContent: function(arg) {
                var props = arg.event.extendedProps;
                var container = document.createElement('div');
                container.style.overflow = 'hidden';
                container.style.width = '100%';
                container.style.padding = '1px 3px';

                // Ligne 1 : horaire + titre
                var titleLine = document.createElement('div');
                titleLine.style.fontWeight = '600';
                titleLine.style.fontSize = '0.8rem';
                titleLine.style.whiteSpace = 'nowrap';
                titleLine.style.overflow = 'hidden';
                titleLine.style.textOverflow = 'ellipsis';

                var timeText = arg.timeText ? arg.timeText + ' ' : '';
                titleLine.textContent = timeText + arg.event.title;
                container.appendChild(titleLine);

                // Ligne 2 : participants (evenements) ou poste (affectations)
                if (props.type === 'evenement' && props.participants_noms && props.participants_noms.length > 0) {
                    var partLine = document.createElement('div');
                    partLine.style.fontSize = '0.7rem';
                    partLine.style.opacity = '0.85';
                    partLine.style.whiteSpace = 'nowrap';
                    partLine.style.overflow = 'hidden';
                    partLine.style.textOverflow = 'ellipsis';
                    partLine.textContent = props.participants_noms.join(', ');
                    container.appendChild(partLine);
                }

                return { domNodes: [container] };
            },
            eventDidMount: function(info) {
                var props = info.event.extendedProps;
                var tooltipText = '';

                if (props.type === 'affectation' && props.notes) {
                    tooltipText = props.notes;
                } else if (props.type === 'evenement' && props.description) {
                    tooltipText = props.description;
                }

                if (tooltipText) {
                    $(info.el).tooltip({
                        title: tooltipText,
                        placement: 'top',
                        trigger: 'hover',
                        container: 'body',
                        html: false
                    });
                }
            }
        });

        calendar.render();
    }

    function fetchAffectations(info, successCallback, failureCallback) {
        var url = config.urls.affectations +
            '?start=' + info.startStr + '&end=' + info.endStr;

        fetch(url, { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(events) {
                if (Array.isArray(events)) {
                    successCallback(events);
                } else {
                    successCallback([]);
                }
            })
            .catch(function(err) {
                console.error('Erreur chargement affectations:', err);
                failureCallback(err);
            });
    }

    function fetchEvenements(info, successCallback, failureCallback) {
        var url = config.urls.evenements +
            '?start=' + info.startStr + '&end=' + info.endStr;

        fetch(url, { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(events) {
                if (Array.isArray(events)) {
                    successCallback(events);
                } else {
                    successCallback([]);
                }
            })
            .catch(function(err) {
                console.error('Erreur chargement evenements:', err);
                failureCallback(err);
            });
    }

    // ===== GESTION DES CLICS =====

    function handleEventClick(info) {
        var props = info.event.extendedProps;

        if (!config.canEdit) {
            // Lecture seule : afficher le detail
            openDetailModal(props);
            return;
        }

        // Mode edition
        if (props.type === 'affectation') {
            openAffectationModal(props);
        } else if (props.type === 'evenement') {
            openEvenementModal(props);
        }
    }

    function handleDateSelect(info) {
        if (!config.canEdit) return;

        // Pre-remplir le modal affectation avec la date/heure selectionnee
        resetFormAffectation();
        document.getElementById('affDate').value = info.startStr.substring(0, 10);

        var startTime = info.startStr.substring(11, 16);
        var endTime = info.endStr.substring(11, 16);
        if (startTime && startTime !== '00:00') {
            document.getElementById('affHeureDebut').value = startTime;
        }
        if (endTime && endTime !== '00:00') {
            document.getElementById('affHeureFin').value = endTime;
        }

        $('#modalAffectation').modal('show');
        calendar.unselect();
    }

    // ===== MODAL AFFECTATION =====

    function openAffectationModal(data) {
        resetFormAffectation();

        if (data && data.pk) {
            // Mode edition : charger les details
            document.getElementById('modalAffectationTitle').innerHTML =
                '<i class="fas fa-edit mr-1"></i> Modifier l\'affectation';
            document.getElementById('btnDeleteAff').style.display = 'inline-block';

            var url = config.urls.affectationDetail.replace('{pk}', data.pk);
            fetch(url, { credentials: 'same-origin' })
                .then(function(r) { return r.json(); })
                .then(function(resp) {
                    if (resp.success) {
                        var d = resp.data;
                        document.getElementById('affPk').value = d.id;
                        document.getElementById('affPlanning').value = d.planning_id;
                        document.getElementById('affEmploye').value = d.employe_matricule;
                        document.getElementById('affPoste').value = d.poste_id;
                        document.getElementById('affDate').value = d.date;
                        document.getElementById('affHeureDebut').value = d.heure_debut;
                        document.getElementById('affHeureFin').value = d.heure_fin;
                        document.getElementById('affStatut').value = d.statut;
                        document.getElementById('affNotes').value = d.notes || '';
                    }
                })
                .catch(function(err) {
                    toastr.error('Erreur lors du chargement');
                    console.error(err);
                });
        } else {
            document.getElementById('modalAffectationTitle').innerHTML =
                '<i class="fas fa-user-clock mr-1"></i> Nouvelle affectation';
            document.getElementById('btnDeleteAff').style.display = 'none';
        }

        $('#modalAffectation').modal('show');
    }

    function resetFormAffectation() {
        document.getElementById('formAffectation').reset();
        document.getElementById('affPk').value = '';
        document.getElementById('btnDeleteAff').style.display = 'none';
        document.getElementById('modalAffectationTitle').innerHTML =
            '<i class="fas fa-user-clock mr-1"></i> Nouvelle affectation';
    }

    function validateAffectationForm() {
        var planning = document.getElementById('affPlanning').value;
        var employe = document.getElementById('affEmploye').value;
        var poste = document.getElementById('affPoste').value;
        var date = document.getElementById('affDate').value;
        var debut = document.getElementById('affHeureDebut').value;
        var fin = document.getElementById('affHeureFin').value;

        if (!planning || !employe || !poste || !date || !debut || !fin) {
            toastr.warning('Veuillez remplir tous les champs obligatoires');
            return false;
        }
        if (fin <= debut) {
            toastr.warning('L\'heure de fin doit etre apres l\'heure de debut');
            return false;
        }
        return true;
    }

    function setButtonLoading(btn, loading) {
        if (loading) {
            btn.dataset.originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Enregistrement...';
            btn.disabled = true;
        } else {
            btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
            btn.disabled = false;
        }
    }

    function saveAffectation() {
        if (!validateAffectationForm()) return;

        var pk = document.getElementById('affPk').value;
        var isEdit = pk !== '';
        var btn = document.getElementById('btnSaveAff');

        var formData = new FormData();
        formData.append('planning', document.getElementById('affPlanning').value);
        formData.append('employe', document.getElementById('affEmploye').value);
        formData.append('poste', document.getElementById('affPoste').value);
        formData.append('date', document.getElementById('affDate').value);
        formData.append('heure_debut', document.getElementById('affHeureDebut').value);
        formData.append('heure_fin', document.getElementById('affHeureFin').value);
        formData.append('statut', document.getElementById('affStatut').value);
        formData.append('notes', document.getElementById('affNotes').value);

        var url = isEdit
            ? config.urls.affectationUpdate.replace('{pk}', pk)
            : config.urls.affectationCreate;

        setButtonLoading(btn, true);

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            setButtonLoading(btn, false);
            if (data.success) {
                toastr.success(data.message || 'Affectation enregistree');
                $('#modalAffectation').modal('hide');
                calendar.refetchEvents();
            } else {
                toastr.error(data.error || 'Erreur');
            }
        })
        .catch(function(err) {
            setButtonLoading(btn, false);
            toastr.error('Erreur de communication');
            console.error(err);
        });
    }

    function deleteAffectation() {
        var pk = document.getElementById('affPk').value;
        if (!pk) return;

        if (!confirm('Supprimer cette affectation ?')) return;

        var url = config.urls.affectationDelete.replace('{pk}', pk);
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                toastr.success(data.message || 'Affectation supprimee');
                $('#modalAffectation').modal('hide');
                calendar.refetchEvents();
            } else {
                toastr.error(data.error || 'Erreur');
            }
        })
        .catch(function(err) {
            toastr.error('Erreur de communication');
            console.error(err);
        });
    }

    // ===== MODAL EVENEMENT =====

    function openEvenementModal(data) {
        resetFormEvenement();

        if (data && data.pk) {
            document.getElementById('modalEvenementTitle').innerHTML =
                '<i class="fas fa-edit mr-1"></i> Modifier l\'evenement';
            document.getElementById('btnDeleteEvt').style.display = 'inline-block';

            var url = config.urls.evenementDetail.replace('{pk}', data.pk);
            fetch(url, { credentials: 'same-origin' })
                .then(function(r) { return r.json(); })
                .then(function(resp) {
                    if (resp.success) {
                        var d = resp.data;
                        document.getElementById('evtPk').value = d.id;
                        document.getElementById('evtTitre').value = d.titre;
                        document.getElementById('evtType').value = d.type_evenement;
                        document.getElementById('evtDateDebut').value = d.date_debut;
                        document.getElementById('evtDateFin').value = d.date_fin;
                        document.getElementById('evtLieu').value = d.lieu || '';
                        document.getElementById('evtDescription').value = d.description || '';

                        // Selectionner les participants (compatible Select2)
                        if (d.participants) {
                            var matricules = d.participants.map(function(p) { return p.matricule; });
                            if (typeof $ !== 'undefined' && $.fn.select2) {
                                $('#evtEmployes').val(matricules).trigger('change');
                            } else {
                                var sel = document.getElementById('evtEmployes');
                                for (var i = 0; i < sel.options.length; i++) {
                                    sel.options[i].selected = matricules.indexOf(sel.options[i].value) !== -1;
                                }
                            }
                        }
                    }
                })
                .catch(function(err) {
                    toastr.error('Erreur lors du chargement');
                    console.error(err);
                });
        } else {
            document.getElementById('modalEvenementTitle').innerHTML =
                '<i class="fas fa-calendar-plus mr-1"></i> Nouvel evenement';
            document.getElementById('btnDeleteEvt').style.display = 'none';
        }

        $('#modalEvenement').modal('show');
    }

    function resetFormEvenement() {
        document.getElementById('formEvenement').reset();
        document.getElementById('evtPk').value = '';
        document.getElementById('btnDeleteEvt').style.display = 'none';
        document.getElementById('modalEvenementTitle').innerHTML =
            '<i class="fas fa-calendar-plus mr-1"></i> Nouvel evenement';
        // Reset Select2 si disponible
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('#evtEmployes').val(null).trigger('change');
        }
    }

    function validateEvenementForm() {
        var titre = document.getElementById('evtTitre').value;
        var debut = document.getElementById('evtDateDebut').value;
        var fin = document.getElementById('evtDateFin').value;

        if (!titre || !debut || !fin) {
            toastr.warning('Veuillez remplir tous les champs obligatoires');
            return false;
        }
        if (fin <= debut) {
            toastr.warning('La date de fin doit etre apres la date de debut');
            return false;
        }
        return true;
    }

    function saveEvenement() {
        if (!validateEvenementForm()) return;

        var pk = document.getElementById('evtPk').value;
        var isEdit = pk !== '';
        var btn = document.getElementById('btnSaveEvt');

        var formData = new FormData();
        formData.append('titre', document.getElementById('evtTitre').value);
        formData.append('type_evenement', document.getElementById('evtType').value);
        formData.append('date_debut', document.getElementById('evtDateDebut').value);
        formData.append('date_fin', document.getElementById('evtDateFin').value);
        formData.append('lieu', document.getElementById('evtLieu').value);
        formData.append('description', document.getElementById('evtDescription').value);

        // Participants (multi-select) — envoyer meme si vide pour permettre la suppression
        var sel = document.getElementById('evtEmployes');
        var hasParticipants = false;
        for (var i = 0; i < sel.options.length; i++) {
            if (sel.options[i].selected) {
                formData.append('employes', sel.options[i].value);
                hasParticipants = true;
            }
        }
        if (!hasParticipants) {
            formData.append('employes', '');
        }

        var url = isEdit
            ? config.urls.evenementUpdate.replace('{pk}', pk)
            : config.urls.evenementCreate;

        setButtonLoading(btn, true);

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            setButtonLoading(btn, false);
            if (data.success) {
                toastr.success(data.message || 'Evenement enregistre');
                $('#modalEvenement').modal('hide');
                calendar.refetchEvents();
            } else {
                toastr.error(data.error || 'Erreur');
            }
        })
        .catch(function(err) {
            setButtonLoading(btn, false);
            toastr.error('Erreur de communication');
            console.error(err);
        });
    }

    function deleteEvenement() {
        var pk = document.getElementById('evtPk').value;
        if (!pk) return;

        if (!confirm('Supprimer cet evenement ?')) return;

        var url = config.urls.evenementDelete.replace('{pk}', pk);
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                toastr.success(data.message || 'Evenement supprime');
                $('#modalEvenement').modal('hide');
                calendar.refetchEvents();
            } else {
                toastr.error(data.error || 'Erreur');
            }
        })
        .catch(function(err) {
            toastr.error('Erreur de communication');
            console.error(err);
        });
    }

    // ===== MODAL DETAIL (lecture seule) =====

    function openDetailModal(props) {
        var body = document.getElementById('modalDetailBody');
        var title = document.getElementById('modalDetailTitle');
        var header = document.getElementById('modalDetailHeader');

        // Loading
        body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div><p class="mt-2">Chargement...</p></div>';
        $('#modalDetail').modal('show');

        if (props.type === 'affectation') {
            header.className = 'modal-header planning-header-primary';
            title.textContent = 'Detail de l\'affectation';

            var url = config.urls.affectationDetail.replace('{pk}', props.pk);
            fetch(url, { credentials: 'same-origin' })
                .then(function(r) { return r.json(); })
                .then(function(resp) {
                    if (resp.success) {
                        var d = resp.data;
                        body.innerHTML =
                            '<table class="table table-sm">' +
                            '<tr><th>Employe</th><td>' + escapeHtml(d.employe_nom) + ' (' + escapeHtml(d.employe_matricule) + ')</td></tr>' +
                            '<tr><th>Poste</th><td>' + escapeHtml(d.poste_nom) + '</td></tr>' +
                            '<tr><th>Site</th><td>' + escapeHtml(d.site_nom) + '</td></tr>' +
                            '<tr><th>Planning</th><td>' + escapeHtml(d.planning_titre) + '</td></tr>' +
                            '<tr><th>Date</th><td>' + escapeHtml(d.date) + '</td></tr>' +
                            '<tr><th>Horaires</th><td>' + escapeHtml(d.heure_debut) + ' - ' + escapeHtml(d.heure_fin) + '</td></tr>' +
                            '<tr><th>Statut</th><td>' + escapeHtml(d.statut) + '</td></tr>' +
                            (d.notes ? '<tr><th>Notes</th><td>' + escapeHtml(d.notes) + '</td></tr>' : '') +
                            '</table>';
                    } else {
                        body.innerHTML = '<p class="text-danger">Erreur: ' + escapeHtml(resp.error || 'Inconnu') + '</p>';
                    }
                })
                .catch(function() {
                    body.innerHTML = '<p class="text-danger">Erreur de chargement</p>';
                });

        } else if (props.type === 'evenement') {
            header.className = 'modal-header planning-header-event';
            title.textContent = 'Detail de l\'evenement';

            var urlEvt = config.urls.evenementDetail.replace('{pk}', props.pk);
            fetch(urlEvt, { credentials: 'same-origin' })
                .then(function(r) { return r.json(); })
                .then(function(resp) {
                    if (resp.success) {
                        var d = resp.data;
                        var participantsHtml = '';
                        if (d.participants && d.participants.length > 0) {
                            participantsHtml = d.participants.map(function(p) {
                                return escapeHtml(p.nom + ' ' + p.prenoms);
                            }).join(', ');
                        } else {
                            participantsHtml = '<em>Aucun</em>';
                        }

                        body.innerHTML =
                            '<table class="table table-sm">' +
                            '<tr><th>Titre</th><td>' + escapeHtml(d.titre) + '</td></tr>' +
                            '<tr><th>Type</th><td>' + escapeHtml(d.type_evenement_display) + '</td></tr>' +
                            '<tr><th>Debut</th><td>' + formatDateTime(d.date_debut) + '</td></tr>' +
                            '<tr><th>Fin</th><td>' + formatDateTime(d.date_fin) + '</td></tr>' +
                            (d.lieu ? '<tr><th>Lieu</th><td>' + escapeHtml(d.lieu) + '</td></tr>' : '') +
                            (d.description ? '<tr><th>Description</th><td>' + escapeHtml(d.description) + '</td></tr>' : '') +
                            '<tr><th>Participants</th><td>' + participantsHtml + '</td></tr>' +
                            '</table>';
                    } else {
                        body.innerHTML = '<p class="text-danger">Erreur: ' + escapeHtml(resp.error || 'Inconnu') + '</p>';
                    }
                })
                .catch(function() {
                    body.innerHTML = '<p class="text-danger">Erreur de chargement</p>';
                });
        }
    }

    // ===== UTILITAIRES =====

    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function escapeHtml(text) {
        if (text == null) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(String(text)));
        return div.innerHTML;
    }

    function formatDateTime(dtStr) {
        if (!dtStr) return '';
        var dt = new Date(dtStr);
        return dt.toLocaleDateString('fr-FR') + ' ' +
               dt.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }

    // ===== API PUBLIQUE =====

    return {
        init: init,
        openAffectationModal: openAffectationModal,
        openEvenementModal: openEvenementModal,
        saveAffectation: saveAffectation,
        saveEvenement: saveEvenement,
        deleteAffectation: deleteAffectation,
        deleteEvenement: deleteEvenement,
        loadPostes: loadPostes
    };

})();

document.addEventListener('DOMContentLoaded', PlanningApp.init);

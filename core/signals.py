# core/signals.py
"""
Système d'audit centralisé pour le projet HR_ONIAN.

Ce module utilise une approche générique pour logger automatiquement
toutes les opérations CRUD sur les modèles configurés.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from threading import local

from .models import ZDLOG

# Thread-local storage pour la requête courante
_thread_locals = local()
_old_values = {}


# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def get_current_request():
    """Récupère la requête HTTP courante depuis le thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Récupère l'utilisateur courant depuis la requête."""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None


def set_current_request(request):
    """Définit la requête courante dans le thread-local storage."""
    _thread_locals.request = request


def model_to_dict(instance, exclude_fields=None):
    """
    Convertit une instance de modèle en dictionnaire sérialisable.

    Args:
        instance: Instance du modèle Django
        exclude_fields: Liste des champs à exclure

    Returns:
        dict: Données du modèle sérialisées
    """
    if exclude_fields is None:
        exclude_fields = ['id']

    data = {}
    for field in instance._meta.fields:
        if field.name not in exclude_fields:
            value = getattr(instance, field.name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif not isinstance(value, (str, int, float, bool, type(None))):
                value = str(value)
            data[field.name] = value
    return data


# ==============================================================================
# CONFIGURATION DES MODÈLES À AUDITER
# ==============================================================================

# Configuration: (model_class, table_name, description_func)
# description_func(instance, created) -> str

def _get_description_zdde(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} du département {instance.CODE} - {instance.LIBELLE}"


def _get_description_zdpo(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} du poste {instance.CODE} - {instance.LIBELLE}"


def _get_description_zy00(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} de l'employé {instance.matricule} - {instance.nom} {instance.prenoms}"


def _get_description_zynp(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} historique nom/prénom pour {instance.employe.matricule}: {instance.nom} {instance.prenoms}"


def _get_description_zyco(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} contrat {instance.type_contrat} pour {instance.employe.matricule}"


def _get_description_zyte(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} téléphone {instance.numero} pour {instance.employe.matricule}"


def _get_description_zyme(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} email {instance.email} pour {instance.employe.matricule}"


def _get_description_zyaf(instance, created):
    action = "Affectation" if created else "Modification affectation"
    return f"{action} de {instance.employe.matricule} au poste {instance.poste.CODE}"


def _get_description_zyad(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} adresse {instance.type_adresse} pour {instance.employe.matricule}: {instance.ville}"


def _get_description_zydo(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} document {instance.get_type_document_display()} pour {instance.employe.matricule}"


def _get_description_zyfa(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} personne à charge {instance.prenom} {instance.nom} ({instance.get_personne_charge_display()}) pour {instance.employe.matricule}"


def _get_description_zypp(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} personne à prévenir {instance.prenom} {instance.nom} (Priorité {instance.ordre_priorite}) pour {instance.employe.matricule}"


def _get_description_zyib(instance, created):
    action = "Ajout" if created else "Modification"
    return f"{action} identité bancaire {instance.nom_banque} pour {instance.employe.matricule}"


def _get_description_zyma(instance, created):
    if created:
        return f"Nomination de {instance.employe.nom} {instance.employe.prenoms} ({instance.employe.matricule}) comme manager du département {instance.departement.CODE} - {instance.departement.LIBELLE}"
    return f"Modification du management de {instance.employe.nom} {instance.employe.prenoms} pour le département {instance.departement.CODE}"


def _get_description_config_conv(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} de la convention {instance.code} - {instance.nom} ({instance.annee_reference})"


def _get_description_type_absence(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} du type d'absence {instance.code} - {instance.libelle}"


def _get_description_jour_ferie(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} du jour férié {instance.nom} - {instance.date.strftime('%d/%m/%Y')}"


def _get_description_param_calcul(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} des paramètres de calcul pour {instance.configuration.nom}"


def _get_description_acquisition(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} acquisition congés {instance.employe.matricule} - Année {instance.annee_reference}: {instance.jours_acquis} jours acquis"


def _get_description_absence(instance, created):
    if created:
        return f"Création demande d'absence {instance.type_absence.libelle} pour {instance.employe.matricule} du {instance.date_debut.strftime('%d/%m/%Y')} au {instance.date_fin.strftime('%d/%m/%Y')} ({instance.jours_ouvrables} jours)"
    return f"Modification absence {instance.employe.matricule} - {instance.type_absence.libelle}"


def _get_description_validation(instance, created):
    if created:
        return f"Validation {instance.get_etape_display()} par {instance.validateur.nom} {instance.validateur.prenoms} - Décision: {instance.get_decision_display()}"
    return f"Modification validation {instance.get_etape_display()}"


def _get_description_notification(instance, created):
    if created:
        return f"Création notification {instance.get_type_notification_display()} pour {instance.destinataire.matricule} - Contexte: {instance.get_contexte_display()}"
    return f"Modification notification pour {instance.destinataire.matricule}"


def _get_description_entreprise(instance, created):
    action = "Création" if created else "Modification"
    return f"{action} de l'entreprise {instance.code} - {instance.nom}"


# ==============================================================================
# DESCRIPTIONS POUR GESTION TEMPS ET ACTIVITÉS
# ==============================================================================

def _get_description_zdcl(instance, created):
    """Client"""
    action = "Création" if created else "Modification"
    return f"{action} du client {instance.code_client} - {instance.raison_sociale}"


def _get_description_zdac(instance, created):
    """Type d'activité"""
    action = "Création" if created else "Modification"
    return f"{action} du type d'activité {instance.code_activite} - {instance.libelle}"


def _get_description_zdpj(instance, created):
    """Projet"""
    action = "Création" if created else "Modification"
    client_info = f" (Client: {instance.client.raison_sociale})" if instance.client else ""
    return f"{action} du projet {instance.code_projet} - {instance.nom_projet}{client_info}"


def _get_description_zdta(instance, created):
    """Tâche"""
    action = "Création" if created else "Modification"
    projet_info = f" (Projet: {instance.projet.nom_projet})" if instance.projet else ""
    return f"{action} de la tâche {instance.code_tache} - {instance.titre}{projet_info}"


def _get_description_zddo_gta(instance, created):
    """Document GTA"""
    action = "Ajout" if created else "Modification"
    rattachement = f"projet {instance.projet.nom_projet}" if instance.projet else f"tâche {instance.tache.titre}" if instance.tache else "non rattaché"
    return f"{action} du document {instance.nom_document} au {rattachement}"


def _get_description_zdit(instance, created):
    """Imputation temps"""
    action = "Création" if created else "Modification"
    employe_info = f"{instance.employe.nom} {instance.employe.prenoms}" if instance.employe else "Employé inconnu"
    return f"{action} imputation {instance.duree}h pour {employe_info} - Tâche: {instance.tache.titre if instance.tache else 'N/A'}"


def _get_description_zdcm(instance, created):
    """Commentaire"""
    action = "Ajout" if created else "Modification"
    auteur = f"{instance.employe.nom} {instance.employe.prenoms}" if instance.employe else "Anonyme"
    return f"{action} commentaire par {auteur} sur la tâche {instance.tache.titre if instance.tache else 'N/A'}"


# ==============================================================================
# DESCRIPTIONS POUR MODULE FRAIS
# ==============================================================================

def _get_description_nfca(instance, created):
    """Catégorie de frais"""
    action = "Création" if created else "Modification"
    return f"{action} de la catégorie de frais {instance.CODE} - {instance.LIBELLE}"


def _get_description_nfpl(instance, created):
    """Plafond de frais"""
    action = "Création" if created else "Modification"
    grade = instance.GRADE or "Tous grades"
    return f"{action} du plafond pour {instance.CATEGORIE.CODE} - {grade}"


def _get_description_nfnf(instance, created):
    """Note de frais"""
    action = "Création" if created else "Modification"
    employe_info = f"{instance.EMPLOYE.nom} {instance.EMPLOYE.prenoms}" if instance.EMPLOYE else "Employé inconnu"
    return f"{action} de la note de frais {instance.REFERENCE} - {employe_info} ({instance.get_STATUT_display()})"


def _get_description_nflf(instance, created):
    """Ligne de frais"""
    action = "Ajout" if created else "Modification"
    return f"{action} ligne de frais {instance.CATEGORIE.LIBELLE} - {instance.MONTANT}€ sur {instance.NOTE.REFERENCE}"


def _get_description_nfav(instance, created):
    """Avance sur frais"""
    action = "Création" if created else "Modification"
    employe_info = f"{instance.EMPLOYE.nom} {instance.EMPLOYE.prenoms}" if instance.EMPLOYE else "Employé inconnu"
    return f"{action} de l'avance {instance.REFERENCE} - {employe_info} ({instance.MONTANT}€)"


# ==============================================================================
# DESCRIPTIONS POUR MODULE MATÉRIEL
# ==============================================================================

def _get_description_mtca(instance, created):
    """Catégorie de matériel"""
    action = "Création" if created else "Modification"
    return f"{action} de la catégorie de matériel {instance.CODE} - {instance.LIBELLE}"


def _get_description_mtfo(instance, created):
    """Fournisseur de matériel"""
    action = "Création" if created else "Modification"
    return f"{action} du fournisseur {instance.CODE} - {instance.RAISON_SOCIALE}"


def _get_description_mtmt(instance, created):
    """Matériel"""
    action = "Création" if created else "Modification"
    categorie = instance.CATEGORIE.LIBELLE if instance.CATEGORIE else "N/A"
    return f"{action} du matériel {instance.CODE_INTERNE} - {instance.DESIGNATION} ({categorie})"


def _get_description_mtaf(instance, created):
    """Affectation de matériel"""
    action = "Affectation" if created else "Modification affectation"
    employe_info = f"{instance.EMPLOYE.nom} {instance.EMPLOYE.prenoms}" if instance.EMPLOYE else "Employé inconnu"
    materiel = instance.MATERIEL.CODE_INTERNE if instance.MATERIEL else "N/A"
    return f"{action} du matériel {materiel} à {employe_info}"


def _get_description_mtmv(instance, created):
    """Mouvement de matériel"""
    action = "Création" if created else "Modification"
    materiel = instance.MATERIEL.CODE_INTERNE if instance.MATERIEL else "N/A"
    return f"{action} mouvement {instance.get_TYPE_MOUVEMENT_display()} pour {materiel}"


def _get_description_mtma(instance, created):
    """Maintenance de matériel"""
    action = "Création" if created else "Modification"
    materiel = instance.MATERIEL.CODE_INTERNE if instance.MATERIEL else "N/A"
    return f"{action} maintenance {instance.get_TYPE_MAINTENANCE_display()} pour {materiel}"


# ==============================================================================
# DESCRIPTIONS POUR MODULE AUDIT
# ==============================================================================

def _get_description_aurc(instance, created):
    """Règle de conformité"""
    action = "Création" if created else "Modification"
    return f"{action} de la règle de conformité {instance.CODE} - {instance.LIBELLE}"


def _get_description_aual(instance, created):
    """Alerte de conformité"""
    action = "Création" if created else "Modification"
    employe_info = f" pour {instance.EMPLOYE.matricule}" if instance.EMPLOYE else ""
    return f"{action} de l'alerte {instance.REFERENCE} - {instance.TITRE}{employe_info}"


def _get_description_aura(instance, created):
    """Rapport d'audit"""
    action = "Création" if created else "Modification"
    return f"{action} du rapport {instance.REFERENCE} - {instance.TITRE} ({instance.get_TYPE_RAPPORT_display()})"


# ==============================================================================
# FACTORY POUR CRÉER LES HANDLERS DE SIGNALS
# ==============================================================================

def create_audit_handlers(model_class, table_name, get_description_func):
    """
    Crée et enregistre les handlers de signals pour un modèle.

    Args:
        model_class: Classe du modèle Django
        table_name: Nom de la table pour les logs
        get_description_func: Fonction (instance, created) -> str
    """

    def store_old_values(sender, instance, **kwargs):
        """Handler pre_save: stocke les anciennes valeurs."""
        if instance.pk:
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                _old_values[f'{table_name}_{instance.pk}'] = model_to_dict(old_instance)
            except sender.DoesNotExist:
                pass

    def log_save(sender, instance, created, **kwargs):
        """Handler post_save: log la création ou modification."""
        request = get_current_request()
        user = get_current_user()
        nouvelle_valeur = model_to_dict(instance)

        if created:
            ZDLOG.log_action(
                table_name=table_name,
                record_id=instance.pk,
                type_mouvement=ZDLOG.TYPE_CREATION,
                user=user,
                request=request,
                nouvelle_valeur=nouvelle_valeur,
                description=get_description_func(instance, True)
            )
        else:
            old_key = f'{table_name}_{instance.pk}'
            ancienne_valeur = _old_values.get(old_key, {})

            # Calculer les changements
            changes = []
            for key, new_val in nouvelle_valeur.items():
                old_val = ancienne_valeur.get(key)
                if old_val != new_val:
                    changes.append(f"{key}: {old_val} → {new_val}")

            description = get_description_func(instance, False)
            if changes:
                description += ": " + ", ".join(changes)

            ZDLOG.log_action(
                table_name=table_name,
                record_id=instance.pk,
                type_mouvement=ZDLOG.TYPE_MODIFICATION,
                user=user,
                request=request,
                ancienne_valeur=ancienne_valeur,
                nouvelle_valeur=nouvelle_valeur,
                description=description
            )

            # Nettoyer le cache
            if old_key in _old_values:
                del _old_values[old_key]

    def log_delete(sender, instance, **kwargs):
        """Handler post_delete: log la suppression."""
        request = get_current_request()
        user = get_current_user()
        ancienne_valeur = model_to_dict(instance)

        # Description de suppression
        base_desc = get_description_func(instance, True)
        description = base_desc.replace("Création", "Suppression").replace("Ajout", "Suppression").replace("Affectation", "Suppression affectation").replace("Nomination", "Suppression du rôle de manager")

        ZDLOG.log_action(
            table_name=table_name,
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_SUPPRESSION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            description=description
        )

    # Enregistrer les signals
    pre_save.connect(store_old_values, sender=model_class, weak=False)
    post_save.connect(log_save, sender=model_class, weak=False)
    post_delete.connect(log_delete, sender=model_class, weak=False)


# ==============================================================================
# ENREGISTREMENT DES MODÈLES À AUDITER
# ==============================================================================

def register_all_audit_signals():
    """
    Enregistre les signals d'audit pour tous les modèles configurés.
    Appelé lors du chargement de l'application.
    """
    # Import des modèles ici pour éviter les imports circulaires
    from employee.models import ZY00, ZYNP, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYPP, ZYIB
    from departement.models import ZDDE, ZDPO, ZYMA
    from absence.models import (
        ConfigurationConventionnelle,
        TypeAbsence,
        JourFerie,
        ParametreCalculConges,
        AcquisitionConges,
        Absence,
        ValidationAbsence,
        NotificationAbsence
    )
    from entreprise.models import Entreprise
    from gestion_temps_activite.models import ZDCL, ZDAC, ZDPJ, ZDTA, ZDDO, ZDIT, ZDCM
    from frais.models import NFCA, NFPL, NFNF, NFLF, NFAV
    from materiel.models import MTCA, MTFO, MTMT, MTAF, MTMV, MTMA
    from audit.models import AURC, AUAL, AURA

    # Liste des modèles à auditer: (model_class, table_name, description_func)
    AUDIT_CONFIG = [
        # Departement
        (ZDDE, 'ZDDE', _get_description_zdde),
        (ZDPO, 'ZDPO', _get_description_zdpo),
        (ZYMA, 'ZYMA', _get_description_zyma),

        # Employee
        (ZY00, 'ZY00', _get_description_zy00),
        (ZYNP, 'ZYNP', _get_description_zynp),
        (ZYCO, 'ZYCO', _get_description_zyco),
        (ZYTE, 'ZYTE', _get_description_zyte),
        (ZYME, 'ZYME', _get_description_zyme),
        (ZYAF, 'ZYAF', _get_description_zyaf),
        (ZYAD, 'ZYAD', _get_description_zyad),
        (ZYDO, 'ZYDO', _get_description_zydo),
        (ZYFA, 'ZYFA', _get_description_zyfa),
        (ZYPP, 'ZYPP', _get_description_zypp),
        (ZYIB, 'ZYIB', _get_description_zyib),

        # Absence
        (ConfigurationConventionnelle, 'ConfigurationConventionnelle', _get_description_config_conv),
        (TypeAbsence, 'TypeAbsence', _get_description_type_absence),
        (JourFerie, 'JourFerie', _get_description_jour_ferie),
        (ParametreCalculConges, 'ParametreCalculConges', _get_description_param_calcul),
        (AcquisitionConges, 'AcquisitionConges', _get_description_acquisition),
        (Absence, 'Absence', _get_description_absence),
        (ValidationAbsence, 'ValidationAbsence', _get_description_validation),
        (NotificationAbsence, 'NotificationAbsence', _get_description_notification),

        # Entreprise
        (Entreprise, 'Entreprise', _get_description_entreprise),

        # Gestion Temps et Activités
        (ZDCL, 'ZDCL', _get_description_zdcl),
        (ZDAC, 'ZDAC', _get_description_zdac),
        (ZDPJ, 'ZDPJ', _get_description_zdpj),
        (ZDTA, 'ZDTA', _get_description_zdta),
        (ZDDO, 'ZDDO', _get_description_zddo_gta),
        (ZDIT, 'ZDIT', _get_description_zdit),
        (ZDCM, 'ZDCM', _get_description_zdcm),

        # Frais
        (NFCA, 'NFCA', _get_description_nfca),
        (NFPL, 'NFPL', _get_description_nfpl),
        (NFNF, 'NFNF', _get_description_nfnf),
        (NFLF, 'NFLF', _get_description_nflf),
        (NFAV, 'NFAV', _get_description_nfav),

        # Matériel
        (MTCA, 'MTCA', _get_description_mtca),
        (MTFO, 'MTFO', _get_description_mtfo),
        (MTMT, 'MTMT', _get_description_mtmt),
        (MTAF, 'MTAF', _get_description_mtaf),
        (MTMV, 'MTMV', _get_description_mtmv),
        (MTMA, 'MTMA', _get_description_mtma),

        # Audit
        (AURC, 'AURC', _get_description_aurc),
        (AUAL, 'AUAL', _get_description_aual),
        (AURA, 'AURA', _get_description_aura),
    ]

    for model_class, table_name, desc_func in AUDIT_CONFIG:
        create_audit_handlers(model_class, table_name, desc_func)


# Enregistrer tous les signals au chargement du module
register_all_audit_signals()

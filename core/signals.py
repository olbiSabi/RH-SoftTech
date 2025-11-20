from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from threading import local
from parametre.models import ZDAB
from employee.models import ZY00, ZYNP, ZYCO, ZYTE, ZYME, ZYAF, ZYAD, ZYDO, ZYFA, ZYPP, ZYIB
from .models import ZDLOG
from departement.models import ZDDE, ZDPO, ZYMA

# Thread-local storage
_thread_locals = local()
_old_values = {}


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None


def set_current_request(request):
    _thread_locals.request = request


def model_to_dict(instance, exclude_fields=None):
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


# ========================================
# SIGNALS POUR ZDDE (Départements)
# ========================================

@receiver(pre_save, sender=ZDDE)
def store_old_values_zdde(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZDDE_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZDDE)
def log_zdde_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZDDE',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Création du département {instance.CODE} - {instance.LIBELLE}"
        )
    else:
        old_key = f'ZDDE_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification du département {instance.CODE}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZDDE',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZDDE)
def log_zdde_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZDDE',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression du département {instance.CODE} - {instance.LIBELLE}"
    )


# ========================================
# SIGNALS POUR ZDPO (Postes)
# ========================================

@receiver(pre_save, sender=ZDPO)
def store_old_values_zdpo(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZDPO_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZDPO)
def log_zdpo_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZDPO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Création du poste {instance.CODE} - {instance.LIBELLE}"
        )
    else:
        old_key = f'ZDPO_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification du poste {instance.CODE}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZDPO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZDPO)
def log_zdpo_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZDPO',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression du poste {instance.CODE} - {instance.LIBELLE}"
    )


# ========================================
# SIGNALS POUR ZDAB
# ========================================

@receiver(pre_save, sender=ZDAB)
def store_old_values_zdab(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZDAB_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZDAB)
def log_zdab_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZDAB',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Création du paramètre {instance.CODE} - {instance.LIBELLE}"
        )
    else:
        old_key = f'ZDAB_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification du paramètre {instance.CODE}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZDAB',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZDAB)
def log_zdab_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZDAB',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression du paramètre {instance.CODE} - {instance.LIBELLE}"
    )


# ========================================
# SIGNALS POUR ZY00 (Employés)
# ========================================

@receiver(pre_save, sender=ZY00)
def store_old_values_zy00(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZY00_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZY00)
def log_zy00_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZY00',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Création de l'employé {instance.matricule} - {instance.nom} {instance.prenoms}"
        )
    else:
        old_key = f'ZY00_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification de l'employé {instance.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZY00',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZY00)
def log_zy00_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZY00',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression de l'employé {instance.matricule} - {instance.nom} {instance.prenoms}"
    )


# ========================================
# SIGNALS POUR ZYNP (Historique Nom/Prénom)
# ========================================

@receiver(pre_save, sender=ZYNP)
def store_old_values_zynp(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYNP_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYNP)
def log_zynp_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYNP',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout historique nom/prénom pour {instance.employe.matricule}: {instance.nom} {instance.prenoms}"
        )
    else:
        old_key = f'ZYNP_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification historique nom/prénom {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYNP',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYNP)
def log_zynp_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYNP',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression historique nom/prénom pour {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYCO (Contrats)
# ========================================

@receiver(pre_save, sender=ZYCO)
def store_old_values_zyco(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYCO_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYCO)
def log_zyco_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYCO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Création contrat {instance.type_contrat} pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYCO_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification contrat {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYCO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYCO)
def log_zyco_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYCO',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression contrat {instance.type_contrat} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYTE (Téléphones)
# ========================================

@receiver(pre_save, sender=ZYTE)
def store_old_values_zyte(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYTE_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYTE)
def log_zyte_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYTE',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout téléphone {instance.numero} pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYTE_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification téléphone {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYTE',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYTE)
def log_zyte_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYTE',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression téléphone {instance.numero} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYME (Emails)
# ========================================

@receiver(pre_save, sender=ZYME)
def store_old_values_zyme(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYME_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYME)
def log_zyme_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYME',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout email {instance.email} pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYME_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification email {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYME',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYME)
def log_zyme_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYME',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression email {instance.email} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYAF (Affectations)
# ========================================

@receiver(pre_save, sender=ZYAF)
def store_old_values_zyaf(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYAF_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYAF)
def log_zyaf_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYAF',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Affectation de {instance.employe.matricule} au poste {instance.poste.CODE}"
        )
    else:
        old_key = f'ZYAF_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification affectation {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYAF',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYAF)
def log_zyaf_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYAF',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression affectation de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYAD (Adresses)
# ========================================

@receiver(pre_save, sender=ZYAD)
def store_old_values_zyad(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYAD_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYAD)
def log_zyad_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYAD',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout adresse {instance.type_adresse} pour {instance.employe.matricule}: {instance.ville}"
        )
    else:
        old_key = f'ZYAD_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification adresse {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYAD',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYAD)
def log_zyad_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYAD',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression adresse {instance.type_adresse} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYDO (Documents)
# ========================================

@receiver(pre_save, sender=ZYDO)
def store_old_values_zydo(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYDO_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYDO)
def log_zydo_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYDO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout document {instance.get_type_document_display()} pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYDO_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification document {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYDO',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYDO)
def log_zydo_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYDO',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression document {instance.get_type_document_display()} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYFA (Famille)
# ========================================

@receiver(pre_save, sender=ZYFA)
def store_old_values_zyfa(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYFA_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYFA)
def log_zyfa_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYFA',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout personne à charge {instance.prenom} {instance.nom} ({instance.get_personne_charge_display()}) pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYFA_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification personne à charge {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYFA',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYFA)
def log_zyfa_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYFA',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression personne à charge {instance.prenom} {instance.nom} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYPP (Personnes à Prévenir)
# ========================================

@receiver(pre_save, sender=ZYPP)
def store_old_values_zypp(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYPP_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYPP)
def log_zypp_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYPP',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout personne à prévenir {instance.prenom} {instance.nom} (Priorité {instance.ordre_priorite}) pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYPP_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification personne à prévenir {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYPP',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYPP)
def log_zypp_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYPP',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression personne à prévenir {instance.prenom} {instance.nom} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYIB (Identités Bancaires)
# ========================================

@receiver(pre_save, sender=ZYIB)
def store_old_values_zyib(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYIB_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYIB)
def log_zyib_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYIB',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Ajout identité bancaire {instance.nom_banque} pour {instance.employe.matricule}"
        )
    else:
        old_key = f'ZYIB_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification identité bancaire {instance.employe.matricule}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYIB',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYIB)
def log_zyib_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYIB',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression identité bancaire {instance.nom_banque} de {instance.employe.matricule}"
    )


# ========================================
# SIGNALS POUR ZYMA (Managers)
# ========================================

@receiver(pre_save, sender=ZYMA)
def store_old_values_zyma(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values[f'ZYMA_{instance.pk}'] = model_to_dict(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=ZYMA)
def log_zyma_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    nouvelle_valeur = model_to_dict(instance)

    if created:
        ZDLOG.log_action(
            table_name='ZYMA',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_CREATION,
            user=user,
            request=request,
            nouvelle_valeur=nouvelle_valeur,
            description=f"Nomination de {instance.employe.nom} {instance.employe.prenoms} ({instance.employe.matricule}) comme manager du département {instance.departement.CODE} - {instance.departement.LIBELLE}"
        )
    else:
        old_key = f'ZYMA_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification du management de {instance.employe.nom} {instance.employe.prenoms} pour le département {instance.departement.CODE}"
        if changes:
            description += ": " + ", ".join(changes)

        ZDLOG.log_action(
            table_name='ZYMA',
            record_id=instance.pk,
            type_mouvement=ZDLOG.TYPE_MODIFICATION,
            user=user,
            request=request,
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            description=description
        )

        if old_key in _old_values:
            del _old_values[old_key]


@receiver(post_delete, sender=ZYMA)
def log_zyma_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    ancienne_valeur = model_to_dict(instance)

    ZDLOG.log_action(
        table_name='ZYMA',
        record_id=instance.pk,
        type_mouvement=ZDLOG.TYPE_SUPPRESSION,
        user=user,
        request=request,
        ancienne_valeur=ancienne_valeur,
        description=f"Suppression du rôle de manager de {instance.employe.nom} {instance.employe.prenoms} ({instance.employe.matricule}) pour le département {instance.departement.CODE} - {instance.departement.LIBELLE}"
    )
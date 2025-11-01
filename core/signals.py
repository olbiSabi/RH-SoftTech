from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from threading import local
from parametre.models import ZDAB
from .models import ZDLOG
from departement.models import ZDDE, ZDPO

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
            description=f"Création du poste {instance.CODE} - {instance.LIBELLE}"  # ← Corrigé
        )
    else:
        old_key = f'ZDPO_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        # Comparer et créer une description des changements
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
            description=description  # ← Amélioration avec détails
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
        description=f"Suppression du poste {instance.CODE} - {instance.LIBELLE}"  # ← Corrigé
    )

# ========================================
# SIGNALS POUR ZDAB (Postes)
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
            description=f"Création du poste {instance.CODE} - {instance.LIBELLE}"  # ← Corrigé
        )
    else:
        old_key = f'ZDAB_{instance.pk}'
        ancienne_valeur = _old_values.get(old_key, {})

        # Comparer et créer une description des changements
        changes = []
        for key, new_val in nouvelle_valeur.items():
            old_val = ancienne_valeur.get(key)
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")

        description = f"Modification du poste {instance.CODE}"
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
            description=description  # ← Amélioration avec détails
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
        description=f"Suppression du poste {instance.CODE} - {instance.LIBELLE}"  # ← Corrigé
    )
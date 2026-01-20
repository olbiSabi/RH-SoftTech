# employee/signals.py
from django.contrib.auth.models import User
from .models import UserSecurity
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import ZYCO

@receiver(post_save, sender=User)
def create_user_security(sender, instance, created, **kwargs):
    """Créer automatiquement un profil de sécurité pour chaque nouvel utilisateur"""
    if created:
        UserSecurity.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_security(sender, instance, **kwargs):
    """Sauvegarder le profil de sécurité"""
    try:
        instance.security.save()
    except UserSecurity.DoesNotExist:
        UserSecurity.objects.create(user=instance)

@receiver([post_save, post_delete], sender=ZYCO)
def synchroniser_etat_employe(sender, instance, **kwargs):
    """
    Synchronise l'état de l'employé après chaque modification de contrat
    NE BLOQUE PAS si erreur
    """
    try:
        # Utiliser transaction.on_commit pour éviter les deadlocks
        transaction.on_commit(
            lambda: instance.employe.synchroniser_etat()
        )
    except Exception:
        # Ne pas bloquer l'opération principale en cas d'erreur
        pass
# employee/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserSecurity

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
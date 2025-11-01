from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ZDLOG(models.Model):
    """Table de logs centralisée pour tout le projet"""

    TYPE_CREATION = 'CREATE'
    TYPE_MODIFICATION = 'UPDATE'
    TYPE_SUPPRESSION = 'DELETE'

    TYPE_CHOICES = [
        (TYPE_CREATION, 'Création'),
        (TYPE_MODIFICATION, 'Modification'),
        (TYPE_SUPPRESSION, 'Suppression'),
    ]

    TABLE_NAME = models.CharField(max_length=100, verbose_name="Nom de la table")
    RECORD_ID = models.CharField(max_length=100, verbose_name="Clé de l'enregistrement")
    TYPE_MOUVEMENT = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type de mouvement")
    DATE_MODIFICATION = models.DateTimeField(default=timezone.now, verbose_name="Date et heure de modification")
    USER = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utilisateur")
    USER_NAME = models.CharField(max_length=150, blank=True, verbose_name="Nom d'utilisateur")
    ANCIENNE_VALEUR = models.JSONField(null=True, blank=True, verbose_name="Ancienne valeur")
    NOUVELLE_VALEUR = models.JSONField(null=True, blank=True, verbose_name="Nouvelle valeur")
    DESCRIPTION = models.TextField(blank=True, verbose_name="Description")
    IP_ADDRESS = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")

    class Meta:
        db_table = 'ZDLOG'
        verbose_name = "Log de modification"
        verbose_name_plural = "Logs de modifications"
        ordering = ['-DATE_MODIFICATION']
        indexes = [
            models.Index(fields=['TABLE_NAME', 'RECORD_ID']),
            models.Index(fields=['DATE_MODIFICATION']),
            models.Index(fields=['USER']),
            models.Index(fields=['TYPE_MOUVEMENT']),
        ]

    def __str__(self):
        user_display = self.USER_NAME or "Système"
        return f"{self.TABLE_NAME} [{self.RECORD_ID}] - {self.get_TYPE_MOUVEMENT_display()} par {user_display}"

    @classmethod
    def log_action(cls, table_name, record_id, type_mouvement, user=None, request=None,
                   ancienne_valeur=None, nouvelle_valeur=None, description=''):
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

        user_name = ''
        if user and user.is_authenticated:
            user_name = user.get_full_name() or user.username

        log_entry = cls(
            TABLE_NAME=table_name,
            RECORD_ID=str(record_id),
            TYPE_MOUVEMENT=type_mouvement,
            USER=user if user and user.is_authenticated else None,
            USER_NAME=user_name,
            ANCIENNE_VALEUR=ancienne_valeur,
            NOUVELLE_VALEUR=nouvelle_valeur,
            DESCRIPTION=description,
            IP_ADDRESS=ip_address
        )
        log_entry.save()
        return log_entry



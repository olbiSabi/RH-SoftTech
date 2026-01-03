from django.db.models.signals import post_save, pre_save
from .models import ZDDA, ZANO
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ZDDA
from .views import mettre_a_jour_solde_conges


@receiver(post_save, sender=ZDDA)
def gerer_notifications_demande_absence(sender, instance, created, **kwargs):
    """
    Signal pour gérer les notifications lors des changements de statut
    """
    print(f"🔔 Signal déclenché pour demande: {instance.numero_demande}, créé: {created}, statut: {instance.statut}")

    # Éviter les boucles infinies
    if hasattr(instance, '_notifications_envoyees'):
        return

    try:
        # 1. NOUVELLE DEMANDE - Notifier le manager
        if created and instance.statut == 'EN_ATTENTE':
            print(f"📧 Nouvelle demande créée - notification manager")
            manager = instance.get_manager()

            if manager and manager.employe:
                print(f"✅ Manager trouvé: {manager.employe.nom} {manager.employe.prenoms}")
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_NOUVELLE',
                    destinataire=manager.employe
                )
                print(f"✅ Notification créée pour le manager")
            else:
                print(f"⚠️ Aucun manager trouvé pour {instance.employe.nom}")

        # 2. VALIDATION MANAGER - Notifier l'employé et les RH
        elif not created and instance.statut == 'VALIDEE_MANAGER':
            print(f"📧 Validation manager - notification employé et RH")

            # Notifier l'employé
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_VALIDEE_MANAGER',
                destinataire=instance.employe
            )
            print(f"✅ Notification créée pour l'employé")

            # Notifier les RH
            employes_rh = obtenir_employes_rh()
            print(f"👥 {len(employes_rh)} employé(s) RH trouvé(s)")

            for employe_rh in employes_rh:
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_NOUVELLE',
                    destinataire=employe_rh
                )
                print(f"✅ Notification créée pour RH: {employe_rh.nom} {employe_rh.prenoms}")

        # 3. REFUS MANAGER - Notifier l'employé
        elif not created and instance.statut == 'REFUSEE_MANAGER':
            print(f"📧 Refus manager - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_REJETEE_MANAGER',
                destinataire=instance.employe
            )
            print(f"✅ Notification rejet créée pour l'employé")

        # 4. VALIDATION RH - Notifier l'employé
        elif not created and instance.statut == 'VALIDEE_RH':
            print(f"📧 Validation RH - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_VALIDEE_RH',
                destinataire=instance.employe
            )
            print(f"✅ Notification validation RH créée pour l'employé")

        # 5. REFUS RH - Notifier l'employé
        elif not created and instance.statut == 'REFUSEE_RH':
            print(f"📧 Refus RH - notification employé")
            ZANO.creer_notification_absence(
                demande_absence=instance,
                type_notification='ABSENCE_REJETEE_RH',
                destinataire=instance.employe
            )
            print(f"✅ Notification rejet RH créée pour l'employé")

        # 6. ANNULATION - Notifier le manager et les RH
        elif not created and instance.statut == 'ANNULEE':
            print(f"📧 Annulation - notification manager et RH")

            # Notifier le manager
            manager = instance.get_manager()
            if manager and manager.employe:
                ZANO.creer_notification_absence(
                    demande_absence=instance,
                    type_notification='ABSENCE_ANNULEE',
                    destinataire=manager.employe
                )
                print(f"✅ Notification annulation créée pour le manager")

            # Notifier les RH si déjà validée par le manager
            if instance.validee_manager:
                employes_rh = obtenir_employes_rh()
                for employe_rh in employes_rh:
                    ZANO.creer_notification_absence(
                        demande_absence=instance,
                        type_notification='ABSENCE_ANNULEE',
                        destinataire=employe_rh
                    )
                    print(f"✅ Notification annulation créée pour RH: {employe_rh.nom}")

    except Exception as e:
        print(f"❌ Erreur dans signal notifications: {e}")
        import traceback
        traceback.print_exc()


def obtenir_employes_rh():
    """
    Retourne la liste des employés ayant le rôle DRH actif
    Utilise la méthode has_role() existante
    """
    from employee.models import ZY00

    employes_rh = []

    try:
        print("  🔍 Recherche des employés avec rôle DRH...")

        # Méthode optimisée : requête directe sur ZYRE
        from employee.models import ZYRE

        # Récupérer directement les employés avec le rôle DRH actif
        attributions_drh = ZYRE.objects.filter(
            role__CODE='DRH',
            actif=True,
            date_fin__isnull=True
        ).select_related('employe')

        for attribution in attributions_drh:
            employes_rh.append(attribution.employe)
            print(
                f"  ✅ DRH trouvé: {attribution.employe.matricule} - {attribution.employe.nom} {attribution.employe.prenoms}")

        if not employes_rh:
            print(f"  ⚠️ Aucun employé avec le rôle DRH actif trouvé")

            # Debug: afficher tous les rôles RH disponibles
            from employee.models import ZYRO
            print(f"  📋 Recherche de rôles contenant 'RH' ou 'DRH':")
            roles_rh = ZYRO.objects.filter(CODE__icontains='RH')
            for role in roles_rh:
                print(f"    - {role.CODE}: {role.LIBELLE}")

                # Chercher les attributions de ces rôles
                attributions = ZYRE.objects.filter(
                    role=role,
                    actif=True,
                    date_fin__isnull=True
                )
                if attributions.exists():
                    print(f"      {attributions.count()} attribution(s) active(s)")
                    for attr in attributions:
                        employes_rh.append(attr.employe)
                        print(f"      ✅ {attr.employe.matricule} - {attr.employe.nom}")

    except Exception as e:
        print(f"  ❌ Erreur lors de la recherche des RH: {e}")
        import traceback
        traceback.print_exc()

    # Dédupliquer la liste
    employes_rh = list(set(employes_rh))
    print(f"  📊 Total RH trouvés: {len(employes_rh)}")
    return employes_rh


@receiver(pre_save, sender=ZDDA)
def detecter_changement_statut(sender, instance, **kwargs):
    """
    Détecte les changements de statut pour enregistrer l'ancien statut
    """
    if instance.pk:
        try:
            old_instance = ZDDA.objects.get(pk=instance.pk)
            instance._old_statut = old_instance.statut
        except ZDDA.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender=ZDDA)
def mettre_a_jour_solde_apres_demande(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement le solde après chaque modification d'une demande
    """
    if instance.type_absence.CODE in ['CPN', 'RTT']:
        mettre_a_jour_solde_conges(instance.employe, instance.date_debut.year)


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ZDDA


@receiver(post_save, sender=ZDDA)
def mettre_a_jour_solde_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement le solde après chaque création/modification de demande
    """
    from .views import mettre_a_jour_solde_conges

    # Ne mettre à jour que pour les types CPN et RTT
    if instance.type_absence.CODE in ['CPN', 'RTT']:
        print(f"\n🔔 Signal: Demande {instance.numero_demande} {'créée' if created else 'modifiée'}")
        print(f"🔔 Date consommation: {instance.date_debut}")

        # Mettre à jour le solde pour cette date de consommation
        mettre_a_jour_solde_conges(instance.employe, instance.date_debut)


@receiver(post_delete, sender=ZDDA)
def mettre_a_jour_solde_apres_suppression(sender, instance, **kwargs):
    """
    Met à jour automatiquement le solde après suppression d'une demande
    """
    from .views import mettre_a_jour_solde_conges

    if instance.type_absence.CODE in ['CPN', 'RTT']:
        print(f"\n🔔 Signal: Demande {instance.numero_demande} supprimée")
        mettre_a_jour_solde_conges(instance.employe, instance.date_debut.year)
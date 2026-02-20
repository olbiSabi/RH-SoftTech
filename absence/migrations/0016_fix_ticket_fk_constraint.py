# Migration pour corriger la contrainte FK de ticket_id
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('absence', '0015_rename_tache_to_ticket'),
        ('project_management', '0002_alter_jrticket_statut'),
    ]

    operations = [
        # 1. Supprimer l'ancienne contrainte FK vers zdta
        migrations.RunSQL(
            sql="ALTER TABLE notification_absence DROP CONSTRAINT IF EXISTS notification_absence_tache_id_a35d9b51_fk_zdta_id;",
            reverse_sql="SELECT 1;",
        ),
        # 2. Supprimer aussi si elle a un autre nom
        migrations.RunSQL(
            sql="ALTER TABLE notification_absence DROP CONSTRAINT IF EXISTS notification_absence_ticket_id_fkey;",
            reverse_sql="SELECT 1;",
        ),
        # 3. Nettoyer les anciennes notifications avec des références invalides
        # (tâches de l'ancien module gestion_temps_activite)
        migrations.RunSQL(
            sql="UPDATE notification_absence SET ticket_id = NULL WHERE ticket_id IS NOT NULL;",
            reverse_sql="SELECT 1;",
        ),
        # 4. Créer la nouvelle contrainte FK vers project_management_jrticket
        migrations.RunSQL(
            sql="""
                ALTER TABLE notification_absence
                ADD CONSTRAINT notification_absence_ticket_id_fkey
                FOREIGN KEY (ticket_id)
                REFERENCES project_management_jrticket(id)
                ON DELETE CASCADE;
            """,
            reverse_sql="ALTER TABLE notification_absence DROP CONSTRAINT IF EXISTS notification_absence_ticket_id_fkey;",
        ),
    ]

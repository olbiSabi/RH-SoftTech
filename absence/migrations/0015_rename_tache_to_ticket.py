# Migration pour renommer tache_id en ticket_id
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('absence', '0014_acquisitionconges_detail_mensuel'),
    ]

    operations = [
        # Renommer la colonne tache_id en ticket_id si elle existe
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'notification_absence'
                        AND column_name = 'tache_id'
                    ) THEN
                        ALTER TABLE notification_absence RENAME COLUMN tache_id TO ticket_id;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'notification_absence'
                        AND column_name = 'ticket_id'
                    ) THEN
                        ALTER TABLE notification_absence RENAME COLUMN ticket_id TO tache_id;
                    END IF;
                END $$;
            """,
        ),
        # Supprimer l'ancien index s'il existe
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS notificatio_tache_i_a1b2c3_idx;",
            reverse_sql="SELECT 1;",  # No-op pour le reverse
        ),
        # Créer le nouvel index
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS notificatio_ticket__a1b2c3_idx ON notification_absence (ticket_id);",
            reverse_sql="DROP INDEX IF EXISTS notificatio_ticket__a1b2c3_idx;",
        ),
    ]

# Configuration de l'ordonnancement du calcul des acquisitions de congés

Ce document explique comment configurer l'exécution automatique du calcul des acquisitions de congés.

## 📋 Vue d'ensemble

Le calcul des acquisitions de congés doit être exécuté régulièrement pour :
- Calculer automatiquement les jours de congés acquis par chaque employé
- Maintenir à jour les soldes de congés
- Générer des rapports mensuels précis

## 1. Préparation des scripts

### Rendre les scripts exécutables

```bash
chmod +x /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
chmod +x /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.py
```

### Tester manuellement

```bash
# Avec le script Bash
/chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh

# Avec le script Python
python /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.py

# En mode simulation (sans sauvegarder)
python /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.py --dry-run
```

## 2. Fréquence recommandée

### Production

Le calcul des acquisitions devrait être exécuté **mensuellement**, idéalement :
- **Le dernier jour du mois à 23h00** (pour avoir le mois complet)
- **Ou le 1er jour du mois suivant à 1h00** (début du nouveau mois)

### Développement/Test

Pour les tests, vous pouvez exécuter plus fréquemment (quotidien ou hebdomadaire).

## 3. Configuration avec Cron

### Éditer la crontab

```bash
crontab -e
```

### A. Calcul mensuel - Dernier jour du mois à 23h00

```cron
# Calcul des acquisitions le dernier jour de chaque mois à 23h00
0 23 28-31 * * [ $(date -d '+1 day' +\%d) -eq 1 ] && /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
```

### B. Calcul mensuel - 1er jour du mois à 1h00 (RECOMMANDÉ)

```cron
# Calcul des acquisitions le 1er de chaque mois à 1h00
0 1 1 * * /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
```

### C. Calcul mensuel avec une année spécifique

Si vous utilisez le script Python et voulez spécifier l'année :

```cron
# Calcul pour l'année en cours
0 1 1 * * cd /chemin/vers/HR_ONIAN && python scripts/calculer_acquisitions.py --annee $(date +\%Y) --verbose
```

### D. Calcul bimensuel (deux fois par mois)

```cron
# Le 1er et le 15 de chaque mois à 2h00
0 2 1,15 * * /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
```

### E. Calcul hebdomadaire (pour tests)

```cron
# Tous les lundis à 2h00
0 2 * * 1 /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
```

## 4. Configuration avec systemd (Linux)

### Créer le service systemd

Créer `/etc/systemd/system/hronian-acquisitions.service` :

```ini
[Unit]
Description=Calcul des acquisitions de congés HR_ONIAN
After=network.target

[Service]
Type=oneshot
User=votre_utilisateur
WorkingDirectory=/chemin/vers/HR_ONIAN
ExecStart=/chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Créer le timer systemd

Créer `/etc/systemd/system/hronian-acquisitions.timer` :

```ini
[Unit]
Description=Timer pour calcul des acquisitions HR_ONIAN
Requires=hronian-acquisitions.service

[Timer]
# Exécuter le 1er de chaque mois à 1h00
OnCalendar=monthly
OnCalendar=*-*-01 01:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Activer le timer

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer le timer
sudo systemctl enable hronian-acquisitions.timer

# Démarrer le timer
sudo systemctl start hronian-acquisitions.timer

# Vérifier le statut
sudo systemctl status hronian-acquisitions.timer

# Voir les prochaines exécutions
systemctl list-timers | grep hronian
```

## 5. Configuration avec Task Scheduler (Windows)

### Via l'interface graphique

1. Ouvrir le **Planificateur de tâches**
2. Créer une tâche de base
3. **Déclencheurs** :
   - Mensuel
   - Le 1er de chaque mois
   - Heure : 01:00

4. **Actions** :
   - Programme/script : `C:\chemin\vers\.env\Scripts\python.exe`
   - Arguments : `scripts\calculer_acquisitions.py --tous --verbeux`
   - Démarrer dans : `C:\chemin\vers\HR_ONIAN`

### Via PowerShell

```powershell
$action = New-ScheduledTaskAction `
    -Execute "C:\chemin\vers\.env\Scripts\python.exe" `
    -Argument "scripts\calculer_acquisitions.py --tous --verbeux" `
    -WorkingDirectory "C:\chemin\vers\HR_ONIAN"

$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "01:00"

Register-ScheduledTask `
    -TaskName "HROnian_Acquisitions" `
    -Action $action `
    -Trigger $trigger `
    -Description "Calcul mensuel des acquisitions de congés"
```

## 6. Monitoring et logs

### Emplacement des logs

Les logs sont enregistrés dans : `HR_ONIAN/logs/acquisitions/`

Format du nom : `acquisitions_YYYYMMDD.log`

### Consulter les logs

```bash
# Voir le log du jour
tail -f /chemin/vers/HR_ONIAN/logs/acquisitions/acquisitions_$(date +%Y%m%d).log

# Voir les 50 dernières lignes
tail -n 50 /chemin/vers/HR_ONIAN/logs/acquisitions/acquisitions_$(date +%Y%m%d).log

# Chercher des erreurs
grep "ERREUR\|❌" /chemin/vers/HR_ONIAN/logs/acquisitions/*.log

# Voir le résumé des exécutions
grep "Traitements réussis" /chemin/vers/HR_ONIAN/logs/acquisitions/*.log
```

### Rotation des logs

Créer `/etc/logrotate.d/hronian-acquisitions` :

```
/chemin/vers/HR_ONIAN/logs/acquisitions/*.log {
    monthly
    rotate 24
    compress
    delaycompress
    notifempty
    missingok
    create 0644 votre_utilisateur votre_groupe
}
```

## 7. Notifications par email

Le script Python supporte les notifications par email :

```bash
# Avec notification email
python scripts/calculer_acquisitions.py --email admin@example.com
```

Pour automatiser avec cron :

```cron
# Calcul mensuel avec notification
0 1 1 * * cd /chemin/vers/HR_ONIAN && python scripts/calculer_acquisitions.py --tous --email admin@example.com
```

## 8. Combinaison avec Celery Beat

Ajouter dans `scripts/celery_config_example.py` ou votre fichier Celery :

```python
@app.task(name='calculer_acquisitions_mensuelles')
def calculer_acquisitions_mensuelles():
    """
    Calcule les acquisitions de congés mensuellement.
    """
    from django.core.management import call_command
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("Début du calcul des acquisitions mensuelles")
        call_command('calculer_acquisitions', '--tous', '--verbeux')
        logger.info("Calcul des acquisitions terminé avec succès")
        return {'status': 'success', 'message': 'Acquisitions calculées'}
    except Exception as e:
        logger.error(f"Erreur lors du calcul des acquisitions: {e}")
        return {'status': 'error', 'message': str(e)}


# Dans CELERY_BEAT_SCHEDULE
'calculer-acquisitions-mensuel': {
    'task': 'calculer_acquisitions_mensuelles',
    'schedule': crontab(hour=1, minute=0, day_of_month=1),  # 1er du mois à 1h00
    'options': {
        'expires': 3600,
    }
}
```

## 9. Bonnes pratiques

### Avant la mise en production

1. **Tester en simulation** :
   ```bash
   python manage.py calculer_acquisitions --dry-run --verbeux
   ```

2. **Vérifier les résultats** :
   ```bash
   python manage.py verifier_acquisitions --annee 2026
   ```

3. **Tester le script d'automatisation** :
   ```bash
   ./scripts/calculer_acquisitions.sh
   ```

### En production

1. **Ordonnancer le 1er du mois** (pas en fin de mois pour éviter les problèmes de mois courts)

2. **Monitorer les logs régulièrement**

3. **Configurer des alertes email** en cas d'erreur

4. **Vérifier mensuellement** que les calculs sont corrects

5. **Sauvegarder les logs** pour l'audit

## 10. Dépannage

### Le calcul ne s'exécute pas

```bash
# Vérifier les permissions
ls -l scripts/calculer_acquisitions.sh

# Tester manuellement
./scripts/calculer_acquisitions.sh

# Vérifier les logs cron
tail -f /var/log/syslog | grep CRON
```

### Erreurs de calcul

```bash
# Consulter les logs
cat logs/acquisitions/acquisitions_$(date +%Y%m%d).log

# Tester avec un employé spécifique
python manage.py calculer_acquisitions --employe MT000001 --verbeux

# Simulation pour voir ce qui serait calculé
python manage.py calculer_acquisitions --dry-run --verbeux
```

### Vérifier la cohérence

```bash
# Vérifier que les acquisitions sont à jour
python manage.py verifier_acquisitions --annee 2026

# Recalculer si nécessaire
python manage.py verifier_acquisitions --annee 2026 --recalculer
```

## 11. Calendrier d'exécution recommandé

Pour un système complet et automatisé :

```cron
# ACQUISITIONS DE CONGÉS
# Calcul mensuel le 1er de chaque mois à 1h00
0 1 1 * * /chemin/vers/HR_ONIAN/scripts/calculer_acquisitions.sh

# VÉRIFICATION DE CONFORMITÉ
# Vérification quotidienne à 6h00
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh

# VÉRIFICATION DES ACQUISITIONS
# Vérification hebdomadaire tous les lundis à 3h00
0 3 * * 1 cd /chemin/vers/HR_ONIAN && python manage.py verifier_acquisitions --annee $(date +\%Y) --recalculer
```

## 12. Documentation complémentaire

- Pour la conformité : voir `CRON_SETUP.md`
- Pour Celery : voir `celery_config_example.py`
- Pour les commandes Django : voir `README.md`

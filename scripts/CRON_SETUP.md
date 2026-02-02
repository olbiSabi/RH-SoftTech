# Configuration de l'ordonnancement des vérifications de conformité

Ce document explique comment configurer l'exécution automatique des vérifications de conformité.

## 1. Préparation du script

### Rendre le script exécutable

```bash
chmod +x /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

### Tester le script manuellement

```bash
/chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

Les logs seront enregistrés dans : `HR_ONIAN/logs/conformite/`

## 2. Configuration avec Cron (Linux/macOS)

### Éditer la crontab

```bash
crontab -e
```

### Exemples de configuration

#### A. Vérification quotidienne à 6h00 du matin

```cron
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

#### B. Vérification tous les jours à 6h00 et 18h00

```cron
0 6,18 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

#### C. Vérification du lundi au vendredi à 7h00

```cron
0 7 * * 1-5 /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

#### D. Vérification tous les lundis à 8h00

```cron
0 8 * * 1 /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

#### E. Vérification le 1er jour de chaque mois à 6h00

```cron
0 6 1 * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

#### F. Vérification toutes les 6 heures

```cron
0 */6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

### Syntaxe Cron

```
┌───────────── minute (0 - 59)
│ ┌───────────── heure (0 - 23)
│ │ ┌───────────── jour du mois (1 - 31)
│ │ │ ┌───────────── mois (1 - 12)
│ │ │ │ ┌───────────── jour de la semaine (0 - 6) (0=dimanche)
│ │ │ │ │
* * * * * commande à exécuter
```

### Vérifier que cron fonctionne

```bash
# Lister les tâches cron de l'utilisateur actuel
crontab -l

# Vérifier que le service cron est actif (Linux)
sudo systemctl status cron

# Vérifier que le service cron est actif (macOS)
sudo launchctl list | grep cron
```

## 3. Configuration avec systemd (Linux)

### Créer un service systemd

Créer le fichier `/etc/systemd/system/hronian-conformite.service` :

```ini
[Unit]
Description=Vérification de conformité HR_ONIAN
After=network.target

[Service]
Type=oneshot
User=votre_utilisateur
WorkingDirectory=/chemin/vers/HR_ONIAN
ExecStart=/chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Créer un timer systemd

Créer le fichier `/etc/systemd/system/hronian-conformite.timer` :

```ini
[Unit]
Description=Timer pour vérification de conformité HR_ONIAN
Requires=hronian-conformite.service

[Timer]
# Exécuter tous les jours à 6h00
OnCalendar=daily
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Activer et démarrer le timer

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer le timer (démarre au boot)
sudo systemctl enable hronian-conformite.timer

# Démarrer le timer immédiatement
sudo systemctl start hronian-conformite.timer

# Vérifier le statut
sudo systemctl status hronian-conformite.timer

# Voir les prochaines exécutions
systemctl list-timers
```

## 4. Configuration avec Task Scheduler (Windows)

### Via l'interface graphique

1. Ouvrir le **Planificateur de tâches** (Task Scheduler)
2. Cliquer sur **Créer une tâche...**
3. Dans l'onglet **Général** :
   - Nom : "Vérification Conformité HR_ONIAN"
   - Description : "Vérification automatique de la conformité"
   - Sélectionner "Exécuter même si l'utilisateur n'est pas connecté"

4. Dans l'onglet **Déclencheurs** :
   - Cliquer sur **Nouveau**
   - Choisir la fréquence (Quotidien, Hebdomadaire, etc.)
   - Définir l'heure d'exécution

5. Dans l'onglet **Actions** :
   - Cliquer sur **Nouveau**
   - Action : Démarrer un programme
   - Programme/script : `C:\chemin\vers\python.exe`
   - Arguments : `manage.py verifier_conformite --tous`
   - Démarrer dans : `C:\chemin\vers\HR_ONIAN`

### Via PowerShell

```powershell
$action = New-ScheduledTaskAction -Execute "C:\chemin\vers\.env\Scripts\python.exe" -Argument "manage.py verifier_conformite --tous" -WorkingDirectory "C:\chemin\vers\HR_ONIAN"

$trigger = New-ScheduledTaskTrigger -Daily -At "06:00"

$principal = New-ScheduledTaskPrincipal -UserId "DOMAIN\User" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "HROnian_Conformite" -Action $action -Trigger $trigger -Principal $principal -Description "Vérification de conformité automatique"
```

## 5. Monitoring et logs

### Emplacement des logs

Les logs sont enregistrés dans : `HR_ONIAN/logs/conformite/`

Format du nom : `conformite_YYYYMMDD.log`

### Consulter les logs

```bash
# Voir le log du jour
tail -f /chemin/vers/HR_ONIAN/logs/conformite/conformite_$(date +%Y%m%d).log

# Voir les 50 dernières lignes
tail -n 50 /chemin/vers/HR_ONIAN/logs/conformite/conformite_$(date +%Y%m%d).log

# Chercher des erreurs
grep "ERREUR" /chemin/vers/HR_ONIAN/logs/conformite/*.log

# Chercher le résumé des exécutions
grep "Total:" /chemin/vers/HR_ONIAN/logs/conformite/*.log
```

### Rotation des logs (optionnel)

Créer `/etc/logrotate.d/hronian-conformite` :

```
/chemin/vers/HR_ONIAN/logs/conformite/*.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    missingok
    create 0644 votre_utilisateur votre_groupe
}
```

## 6. Notifications par email (optionnel)

Le système envoie déjà des emails automatiques lors de la création d'alertes.

Pour recevoir également le résumé de l'exécution par email, modifier le script :

```bash
# À la fin du script verifier_conformite.sh, ajouter :
if [ $EXIT_CODE -eq 0 ]; then
    mail -s "✅ Conformité HR_ONIAN - Vérification réussie" admin@example.com < "$LOG_FILE"
else
    mail -s "❌ Conformité HR_ONIAN - Erreur détectée" admin@example.com < "$LOG_FILE"
fi
```

## 7. Recommandations de production

### Fréquence recommandée

- **Contrats** : Quotidien (6h00 du matin)
- **Documents** : Hebdomadaire (lundi matin)
- **Visites médicales** : Mensuel (1er du mois)
- **Matériel** : Hebdomadaire (lundi matin)

### Configuration recommandée pour la production

```cron
# Vérification complète quotidienne à 6h00
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh

# Ou si vous préférez séparer les vérifications :
# Contrats - Tous les jours à 6h00
0 6 * * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh --type contrat

# Documents et matériel - Tous les lundis à 7h00
0 7 * * 1 /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh --type document
0 7 * * 1 /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh --type materiel

# Visites médicales - Le 1er de chaque mois à 8h00
0 8 1 * * /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh --type visite
```

## 8. Dépannage

### Le script ne s'exécute pas

1. Vérifier les permissions :
   ```bash
   ls -l /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
   ```

2. Vérifier le chemin de l'environnement virtuel dans le script

3. Vérifier les logs cron :
   ```bash
   # Linux
   tail -f /var/log/syslog | grep CRON

   # macOS
   tail -f /var/log/system.log | grep cron
   ```

### Le script échoue

1. Tester manuellement :
   ```bash
   /chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
   ```

2. Vérifier les logs de conformité :
   ```bash
   cat /chemin/vers/HR_ONIAN/logs/conformite/conformite_$(date +%Y%m%d).log
   ```

3. Vérifier la configuration Django (settings.py, base de données, etc.)

## 9. Exécution manuelle

### Avec le script

```bash
/chemin/vers/HR_ONIAN/scripts/verifier_conformite.sh
```

### Directement avec Django

```bash
# Toutes les vérifications
python manage.py verifier_conformite --tous --verbeux

# Vérification spécifique
python manage.py verifier_conformite --type contrat

# Sans affichage détaillé
python manage.py verifier_conformite
```

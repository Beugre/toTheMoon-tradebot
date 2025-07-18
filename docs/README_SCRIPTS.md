# Scripts de Déploiement VPS

Ce dossier contient tous les scripts nécessaires pour déployer le bot de trading sur votre VPS.

## 📁 Fichiers inclus

### Scripts de déploiement
- `full_deploy.sh` - **Script principal** de déploiement complet (Linux/Mac)
- `deploy_windows.ps1` - Script de déploiement pour Windows PowerShell
- `deploy_to_vps.sh` - Script de copie des fichiers vers le VPS

### Scripts de gestion
- `disable_old_bot.sh` - Désactive l'ancien bot sur le VPS
- `setup_systemd.sh` - Configure le service systemd

### Configuration système
- `tothemoon-tradebot.service` - Fichier de service systemd

## 🚀 Déploiement rapide

### Option 1: Script automatique (recommandé)
```bash
# Linux/Mac
chmod +x scripts/full_deploy.sh
./scripts/full_deploy.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts\deploy_windows.ps1
```

### Option 2: Déploiement manuel étape par étape

#### 1. Désactivation de l'ancien bot
```bash
ssh root@213.199.41.168 'bash -s' < scripts/disable_old_bot.sh
```

#### 2. Copie des fichiers
```bash
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='logs/' ./ root@213.199.41.168:/opt/toTheMoon_tradebot/
```

#### 3. Installation des dépendances
```bash
ssh root@213.199.41.168
cd /opt/toTheMoon_tradebot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configuration du service
```bash
bash scripts/setup_systemd.sh
```

## ⚙️ Configuration post-déploiement

### 1. Configuration du fichier .env
```bash
ssh root@213.199.41.168
cd /opt/toTheMoon_tradebot
nano .env
```

Copiez le contenu de votre fichier `.env` local.

### 2. Configuration Google Sheets (optionnel)
```bash
nano credentials.json
```

### 3. Test de la configuration
```bash
source venv/bin/activate
python3 run.py --test
```

### 4. Démarrage du service
```bash
systemctl start tothemoon-tradebot
systemctl status tothemoon-tradebot
```

## 📊 Gestion du service

### Commandes systemd
```bash
# Démarrer
systemctl start tothemoon-tradebot

# Arrêter
systemctl stop tothemoon-tradebot

# Redémarrer
systemctl restart tothemoon-tradebot

# Statut
systemctl status tothemoon-tradebot

# Activer au démarrage
systemctl enable tothemoon-tradebot

# Désactiver au démarrage
systemctl disable tothemoon-tradebot
```

### Logs en temps réel
```bash
# Logs du service
journalctl -u tothemoon-tradebot -f

# Logs avec détails
journalctl -u tothemoon-tradebot -f --output=verbose

# Logs depuis une date
journalctl -u tothemoon-tradebot --since "2024-01-01"
```

## 🔧 Dépannage

### Problèmes de connexion SSH
```bash
# Test de connexion
ssh -v root@213.199.41.168

# Génération de clés SSH si nécessaire
ssh-keygen -t rsa -b 4096
ssh-copy-id root@213.199.41.168
```

### Problèmes d'installation TA-Lib
```bash
# Installation manuelle de TA-Lib
apt install -y build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr/local
make && make install
ldconfig
pip install TA-Lib
```

### Problèmes de permissions
```bash
# Correction des permissions
chmod +x run.py
chmod +x investor_report.py
chmod +x scripts/*.sh
chown -R root:root /opt/toTheMoon_tradebot
```

### Vérification des processus
```bash
# Processus Python actifs
ps aux | grep python

# Ports en écoute
netstat -tlnp | grep python

# Mémoire utilisée
free -h
top -p $(pgrep -f tothemoon)
```

## 📈 Monitoring et maintenance

### Rapport d'investisseurs
```bash
cd /opt/toTheMoon_tradebot
source venv/bin/activate

# Résumé rapide
python3 investor_report.py summary

# Rapport complet (30 jours)
python3 investor_report.py report 30

# Rapport personnalisé
python3 investor_report.py report 90 rapport_investisseurs.json
```

### Sauvegarde des données
```bash
# Sauvegarde de la base de données
cp data/trading_bot.db backups/trading_bot_$(date +%Y%m%d).db

# Sauvegarde des logs
tar -czf backups/logs_$(date +%Y%m%d).tar.gz logs/
```

### Mise à jour du bot
```bash
# Arrêt du service
systemctl stop tothemoon-tradebot

# Sauvegarde
cp -r /opt/toTheMoon_tradebot /opt/toTheMoon_tradebot.backup

# Mise à jour (copie des nouveaux fichiers)
rsync -avz --exclude='data/' --exclude='logs/' --exclude='.env' ./ root@213.199.41.168:/opt/toTheMoon_tradebot/

# Redémarrage
systemctl start tothemoon-tradebot
```

## 🔒 Sécurité

### Recommandations
- Changez le mot de passe root après déploiement
- Configurez un firewall (ufw)
- Utilisez des clés SSH au lieu de mots de passe
- Surveillez les logs régulièrement
- Effectuez des sauvegardes régulières

### Configuration firewall basique
```bash
ufw enable
ufw allow ssh
ufw allow from YOUR_IP_ADDRESS
ufw status
```

## 📞 Support

En cas de problème, vérifiez :
1. Les logs du service : `journalctl -u tothemoon-tradebot -f`
2. La configuration : `.env` et `credentials.json`
3. Les permissions des fichiers
4. La connectivité réseau et API

---

**Note**: Remplacez `213.199.41.168` par l'adresse IP réelle de votre VPS si différente.

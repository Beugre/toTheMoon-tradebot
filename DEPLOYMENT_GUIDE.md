# 🚀 Guide de Déploiement VPS - toTheMoon Bot

## 📋 Pré-requis VPS

### 1. Connexion au VPS
```bash
ssh user@your-vps-ip
```

### 2. Installation des dépendances système
```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation Python et outils
sudo apt install python3 python3-pip python3-venv git curl -y

# Installation TA-Lib (requis pour l'analyse technique)
sudo apt-get install build-essential wget -y
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib*
```

## 🚀 Déploiement Initial

### 1. Clonage du repository
```bash
cd ~
git clone https://github.com/Beugre/toTheMoon-tradebot.git
cd toTheMoon-tradebot
```

### 2. Configuration de l'environnement
```bash
# Création environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration des fichiers
```bash
# Configuration principale
cp .env.template .env
nano .env
# ✏️ Remplissez vos clés API Binance, Telegram, etc.

# Configuration Firebase (optionnel)
# 📁 Uploadez votre firebase_credentials.json depuis Firebase Console
# 🔧 Les variables Firebase sont déjà dans .env
```

### 4. Déploiement automatique
```bash
# Rendre exécutable
chmod +x deploy.sh
chmod +x update.sh

# Déploiement complet
./deploy.sh
```

## 🔄 Mises à jour

### Mise à jour rapide (recommandée)
```bash
./update.sh
```

### Mise à jour complète (si problèmes)
```bash
./deploy.sh
```

## 📊 Monitoring

### Status du bot
```bash
sudo systemctl status toTheMoon-bot
```

### Logs en temps réel
```bash
sudo journalctl -u toTheMoon-bot -f
```

### Logs récents
```bash
sudo journalctl -u toTheMoon-bot -n 50
```

## 🔧 Gestion du Service

### Commandes principales
```bash
# Démarrer
sudo systemctl start toTheMoon-bot

# Arrêter
sudo systemctl stop toTheMoon-bot

# Redémarrer
sudo systemctl restart toTheMoon-bot

# Statut
sudo systemctl status toTheMoon-bot

# Logs
sudo journalctl -u toTheMoon-bot -f
```

## 🔥 Firebase Analytics

### Configuration
1. **Firebase Console**: https://console.firebase.google.com/
2. **Projet**: `tothemoon-9e4d5`
3. **Données temps réel**: Firestore + Realtime Database

### Collections créées automatiquement
- `bot_logs`: Tous les logs détaillés
- `trades`: Historique complet des trades
- `performance`: Performances journalières
- `metrics`: Métriques temps réel

### Accès aux données
- **Console Firebase**: Interface web complète
- **APIs**: Accès programmatique
- **Exports**: JSON, CSV automatiques

## 🛡️ Sécurité

### Fichiers sensibles
```bash
# Permissions restrictives
chmod 600 .env
chmod 600 firebase_credentials.json

# Sauvegarde sécurisée
cp .env ~/.env.backup
cp firebase_credentials.json ~/.firebase_credentials.backup
```

### Surveillance
```bash
# Surveillance disque
df -h

# Surveillance mémoire
free -h

# Surveillance CPU
top
```

## 🆘 Dépannage

### Bot ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u toTheMoon-bot -n 20

# Vérifier la configuration
cd ~/toTheMoon-tradebot
python3 test_non_regression_simple.py

# Test Firebase
python3 check_firebase.py
```

### Erreurs communes

#### 1. **Erreur API Binance**
```bash
# Vérifier les clés dans .env
grep BINANCE .env
```

#### 2. **Erreur Firebase**
```bash
# Vérifier credentials
ls -la firebase_credentials.json
python3 debug_firebase.py
```

#### 3. **Erreur Google Sheets**
```bash
# Vérifier credentials
ls -la credentials.json
```

### Redéploiement complet
```bash
# Sauvegarde config
cp .env .env.backup
cp firebase_credentials.json firebase_credentials.backup

# Nettoyage
sudo systemctl stop toTheMoon-bot
rm -rf ~/toTheMoon-tradebot

# Re-clone et config
git clone https://github.com/Beugre/toTheMoon-tradebot.git
cd toTheMoon-tradebot
cp ~/.env.backup .env
cp ~/.firebase_credentials.backup firebase_credentials.json

# Redéploiement
./deploy.sh
```

## 📈 Performance

### Optimisations appliquées
- ✅ **Gestion miettes**: Seuil 5$ USDC
- ✅ **Analysis technique**: Pas de double calcul
- ✅ **API robuste**: Gestion d'erreurs améliorée
- ✅ **Firebase**: Analytics temps réel
- ✅ **Logging**: Rotatif et optimisé

### Surveillance continue
```bash
# Script de monitoring automatique
crontab -e
# Ajouter: */5 * * * * systemctl is-active --quiet toTheMoon-bot || systemctl restart toTheMoon-bot
```

---

## 🎯 Checklist de Déploiement

- [ ] VPS configuré avec Python 3.8+
- [ ] Repository cloné
- [ ] Fichier `.env` configuré avec toutes les clés
- [ ] Firebase credentials uploadé (optionnel)
- [ ] TA-Lib installé
- [ ] Tests de non-régression passés
- [ ] Service systemd configuré
- [ ] Bot démarré et logs OK
- [ ] Firebase Analytics fonctionnels
- [ ] Monitoring activé

**🚀 Votre bot est maintenant déployé avec Firebase Analytics en temps réel !**

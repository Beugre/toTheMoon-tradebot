# 🚀 ToTheMoon Trading Bot v2.0

Bot de trading automatisé spécialisé dans le scalping sur les paires EUR avec gestion dynamique du capital.

## ✨ Fonctionnalités

### 🎯 Trading Automatisé
- **Multi-paires EUR** : Sélection automatique des meilleures paires de trading
- **Signaux techniques avancés** : EMA, MACD, RSI, Bollinger Bands
- **Scalping haute fréquence** : Optimisé pour les gains rapides

### 💰 Gestion du Capital
- **Capital dynamique** : Calcul en temps réel (EUR + positions crypto)
- **Protection surexposition** : Limite automatique à 30% par asset
- **Taille de position adaptative** : Basée sur le capital total disponible

### ⚡ Gestion des Risques
- **Stop Loss automatique** : Protection des pertes
- **Take Profit intelligent** : Sécurisation des gains
- **Trailing Stop** : Maximisation des profits
- **Monitoring 24/7** : Surveillance continue des positions

### 📱 Notifications & Monitoring
- **Telegram intégré** : Notifications en temps réel
- **Valeurs dynamiques** : Toutes les alertes basées sur la configuration
- **Google Sheets logging** : Suivi détaillé des performances
- **Base de données SQLite** : Historique complet des trades

## 🚀 Installation Rapide

### Prérequis
- Python 3.8+
- Compte Binance avec API activée
- Bot Telegram (optionnel)
- VPS Linux (pour production)

### 1. Cloner le projet
```bash
git clone https://github.com/YOUR_USERNAME/toTheMoon-tradebot.git
cd toTheMoon-tradebot
```

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos clés API
nano .env
```

### 4. Configuration requise
```env
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Telegram (optionnel)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Google Sheets (optionnel)
GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

### 5. Test et lancement
```bash
# Test de la configuration
python test_config.py

# Lancement en mode test
python run.py --test

# Lancement en production
python run.py
```

## 🖥️ Déploiement VPS

### Déploiement automatique (Windows -> Linux VPS)
```powershell
# Modifier deploy_simple.ps1 avec vos paramètres VPS
.\deploy_simple.ps1
```

### Configuration manuelle VPS
```bash
# Installation sur Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Création du service systemd
sudo cp scripts/tothemoon-tradebot.service /etc/systemd/system/
sudo systemctl enable tothemoon-tradebot
sudo systemctl start tothemoon-tradebot
```

## 📊 Configuration Trading

### Paramètres principaux (config.py)
```python
# Gestion du capital
POSITION_SIZE_PERCENT = 12.0  # % du capital par position
MAX_OPEN_POSITIONS = 3        # Nombre max de positions simultanées
DAILY_TARGET_PERCENT = 1.0    # Objectif quotidien en %
DAILY_STOP_LOSS_PERCENT = 1.0 # Stop loss quotidien en %

# Gestion des risques
STOP_LOSS_PERCENT = 0.5       # Stop loss par trade
TAKE_PROFIT_PERCENT = 1.0     # Take profit par trade
TRAILING_STOP_PERCENT = 0.5   # Trailing stop
```

### Paires supportées
- BTCEUR, ETHEUR, XRPEUR
- ADAEUR, DOGEEUR, BNBEUR
- MATICEUR, DOTEUR, LINKEUR
- LTCEUR, SOLEUR, AVAXEUR

## 📈 Monitoring

### Commandes utiles
```bash
# Logs en temps réel
ssh root@YOUR_VPS 'tail -f /opt/toTheMoon_tradebot/logs/trading_bot.log'

# Statut du service
ssh root@YOUR_VPS 'systemctl status tothemoon-tradebot'

# Processus actifs
ssh root@YOUR_VPS 'ps aux | grep python'
```

### Dashboard Telegram
- 🚀 Notification de démarrage avec capital dynamique
- 📈 Alertes d'ouverture/fermeture de positions
- 💰 Résumé quotidien des performances
- ⚠️ Alertes d'erreurs et avertissements

## 🔧 Maintenance

### Mise à jour du bot
```bash
# Sur votre machine locale
git pull origin main
.\deploy_simple.ps1
```

### Sauvegarde
```bash
# Sauvegarder la base de données
scp root@YOUR_VPS:/opt/toTheMoon_tradebot/data/trading_bot.db ./backups/
```

## 📚 Documentation

- [Guide de démarrage rapide](docs/QUICK_START.md)
- [Guide de déploiement](docs/DEPLOYMENT_SUMMARY.md)
- [Configuration avancée](docs/OPTIMISATION_CONFIG.md)
- [Commandes utiles](docs/commandes_utiles.md)

## ⚠️ Avertissements

- **Trading à risque** : Ne tradez que ce que vous pouvez vous permettre de perdre
- **Tests recommandés** : Utilisez le mode test avant la production
- **Clés API sécurisées** : Ne partagez jamais vos clés API
- **Surveillance requise** : Monitorer régulièrement les performances

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 💡 Support

- **Issues GitHub** : Pour les bugs et demandes de fonctionnalités
- **Discussions** : Pour les questions et discussions
- **Documentation** : Dossier `docs/` pour guides détaillés

---

**⚡ Développé avec passion pour les traders qui visent la lune ! 🌙**
# 🚀 ToTheMoon Trading Bot v3.0 - ENHANCED EDITION

Bot de trading automatisé ultra-sophistiqué spécialisé dans le scalping EUR avec gestion intelligente du capital et protection automatique contre la surexposition.

## ✨ Fonctionnalités Avancées

### 🎯 Trading Automatisé Intelligent
- **Multi-paires EUR optimisées** : Sélection dynamique des top 5 paires les plus performantes
- **Signaux techniques convergents** : EMA crossover + MACD + RSI rebond confirmé + Bollinger Bands
- **Scalping ultra-précis** : Timeframe 1 minute pour capter les micro-mouvements
- **Scoring automatique** : Système de notation des paires par performance et volume

### 💰 Gestion du Capital Dynamique
- **Capital temps réel** : Calcul automatique (EUR libre + TOUTES cryptos valorisées)
- **Protection surexposition RENFORCÉE** : Limite stricte à 20% par asset avec correction automatique
- **Position sizing adaptatif** : Ajustement selon volatilité (réduction si >3%, augmentation si <1%)
- **Vérification de cohérence** : Détection et correction automatique des positions fantômes

### ⚡ Gestion des Risques Ultra-Sécurisée
- **Stop Loss serré** : 0.25% pour limiter les pertes unitaires
- **Take Profit optimisé** : 0.8% pour sécuriser rapidement les gains
- **Trailing Stop intelligent** : SL ET TP se mettent à jour ensemble lors du trailing
- **Sortie momentum faible** : Détection automatique de signaux d'affaiblissement
- **Timeouts adaptatifs** : Durée variable selon la volatilité du marché

### 📱 Monitoring & Alertes Avancées
- **Telegram Premium** : Notifications temps réel avec détails techniques
- **Calculs dynamiques** : Toutes les valeurs basées sur le capital actuel
- **Google Sheets Pro** : Logging détaillé avec capital avant/après chaque trade
- **Base de données complète** : Historique, métriques temps réel, performances quotidiennes
- **Détection incohérences** : Alertes automatiques en cas de positions fantômes

### 🛡️ Protections Automatiques NOUVELLES
- **Vente forcée d'urgence** : Correction automatique en cas de surexposition détectée
- **Validation multi-niveau** : Vérification exposition avant ET après chaque position
- **Gestion soldes insuffisants** : Fermeture virtuelle sécurisée si problème technique
- **Retry intelligent** : Système de tentatives avec ajustement automatique des quantités
- **Unique Trade IDs** : Prévention totale des positions multiples sur même paire

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

## 📊 Configuration Trading Optimisée

### Paramètres de performance (config.py)
```python
# Gestion du capital (optimisé pour 15K+ EUR)
BASE_POSITION_SIZE_PERCENT = 12.0     # Taille de base par position
MAX_OPEN_POSITIONS = 5                # Maximum 5 positions simultanées
MAX_TRADES_PER_PAIR = 2              # Maximum 2 trades par paire
MAX_EXPOSURE_PER_ASSET_PERCENT = 20.0 # LIMITE STRICTE par crypto

# Objectifs & protection quotidienne
DAILY_TARGET_PERCENT = 1.0            # Objectif +1% par jour
DAILY_STOP_LOSS_PERCENT = 2.0         # Stop loss quotidien étendu

# Gestion des risques ultra-serrée
STOP_LOSS_PERCENT = 0.25              # SL serré pour limiter pertes
TAKE_PROFIT_PERCENT = 0.8             # TP rapide pour sécuriser
TRAILING_ACTIVATION_PERCENT = 0.1     # Trailing dès +0.1%
TRAILING_STEP_PERCENT = 0.2           # Step trailing fin

# Signaux techniques renforcés
RSI_OVERSOLD_LEVEL = 30               # Seuil survente
RSI_BOUNCE_CONFIRM_LEVEL = 35         # Confirmation rebond RSI
MIN_SIGNAL_CONDITIONS = 4             # Minimum 4/4 conditions
MIN_VOLATILITY_1H_PERCENT = 0.5       # Volatilité minimum requise

# Position sizing adaptatif
HIGH_VOLATILITY_THRESHOLD = 3.0       # Réduction si volatilité élevée
LOW_VOLATILITY_THRESHOLD = 1.0        # Augmentation si faible volatilité
VOLATILITY_REDUCTION_FACTOR = 0.5     # Facteur de réduction
```

### Critères de sélection des paires
```python
# Filtres qualité
MIN_VOLUME_EUR = 100000               # Volume minimum 100K EUR
MAX_SPREAD_PERCENT = 0.15             # Spread maximum 0.15%
MAX_PAIRS_TO_ANALYZE = 5              # Top 5 paires analysées
SCAN_INTERVAL = 40                    # Scan toutes les 40 secondes
```

### Paires supportées & algorithme de scoring
```python
# Paires EUR premium (top liquidité)
PRINCIPALES: BTCEUR, ETHEUR, XRPEUR, ADAEUR, DOGEEUR
SECONDAIRES: BNBEUR, MATICEUR, DOTEUR, LINKEUR, LTCEUR, SOLEUR, AVAXEUR
ÉMERGENTES: SUIEUR, SEUR, etc.

# Blacklist automatique
STABLECOINS: USDCEUR, BUSDEUR, TUSDEUR
ASSETS_SPECIAUX: PAXGEUR (or tokenisé)

# Scoring automatique par :
- Volume 24h en EUR (poids: 40%)
- Volatilité 1h optimale (poids: 30%) 
- Spread bid/ask (poids: 20%)
- Momentum technique (poids: 10%)
```

## 🚀 Performance Attendue

### 📈 Objectifs réalistes
- **Gain quotidien** : +1% (196 EUR/jour sur 19.6K capital)
- **Gain mensuel** : 15-30% (conservateur avec protection)
- **Win rate estimé** : 65-75% (signaux de qualité convergents)
- **Trades par jour** : 5-15 selon volatilité du marché
- **Drawdown max** : <5% grâce aux protections multicouches

### 💎 Avantages compétitifs
✅ **Protection surexposition** : Impossible de dépasser 20% par crypto  
✅ **Signaux convergents** : 4 indicateurs techniques obligatoires  
✅ **Capital dynamique** : Valorisation temps réel de tout le portefeuille  
✅ **Trailing intelligent** : SL ET TP progressent ensemble  
✅ **Timeouts adaptatifs** : Durée variable selon volatilité  
✅ **Correction automatique** : Vente forcée si surexposition détectée

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

### Dashboard Telegram Premium
- 🚀 **Démarrage** : Capital dynamique total et répartition EUR/crypto
- 📈 **Trades** : Ouverture avec exposition actuelle et sizing adaptatif
- 💰 **Fermetures** : P&L détaillé + capital avant/après + durée
- �️ **Protections** : Alertes surexposition avec correction automatique
- ⚠️ **Maintenance** : Positions fantômes, incohérences, erreurs techniques
- � **Résumé quotidien** : Performance, win rate, capital progression

### 🔍 Monitoring avancé
```bash
# Exposition temps réel par asset
# Capital : 19,650 EUR
# BTC: 3,935 EUR (20.0%) ✅ LIMITE RESPECTÉE
# ETH: 3,934 EUR (20.0%) ✅ LIMITE RESPECTÉE  
# EUR libre: 1,426 EUR pour nouvelles positions

# Signaux détectés mais protégés
# ❌ Trade BTCEUR refusé: Exposition BTC déjà trop élevée
# ✅ Protection automatique active
```

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

## ⚠️ Avertissements & Bonnes Pratiques

### 🛡️ Sécurité renforcée
- **Capital à risque** : Ne tradez que 50-70% de votre capital total
- **Tests obligatoires** : Mode test pendant 1 semaine minimum avant production  
- **Clés API verrouillées** : Stockage sécurisé, jamais dans le code
- **Surveillance active** : Monitoring quotidien recommandé
- **Sauvegarde automatique** : Base de données + configuration

### 📋 Checklist avant production
✅ Capital EUR suffisant (minimum 1000 EUR libre)  
✅ Exposition par asset <20% AVANT démarrage  
✅ Clés API Binance avec trading activé  
✅ Bot Telegram configuré pour alertes  
✅ VPS avec monitoring actif  
✅ Tests réussis sur compte sandbox

### 🚨 Signaux d'alerte à surveiller
- **Surexposition** : >20% sur un asset = vente forcée automatique
- **Capital EUR faible** : <500 EUR = réduire positions
- **Volatilité extrême** : >5% = surveillance manuelle requise
- **Erreurs répétées** : API timeout, connexion = investigation nécessaire

## 🔄 Changelog v3.0

### 🆕 Nouvelles fonctionnalités majeures
- ✨ **Protection surexposition 20%** avec correction automatique
- ✨ **Capital dynamique** incluant TOUTES les cryptos
- ✨ **RSI rebond confirmé** au lieu de simple survente
- ✨ **Trailing stop TP** : Take Profit suit aussi la progression
- ✨ **Position sizing adaptatif** selon volatilité temps réel
- ✨ **Unique Trade IDs** empêchant positions multiples
- ✨ **Vente forcée d'urgence** si surexposition détectée

### 🛠️ Améliorations techniques
- 🔧 **Timeout adaptatif** : Durée variable selon volatilité
- 🔧 **Sortie momentum faible** : Détection d'affaiblissement
- 🔧 **Google Sheets corrigé** : Capital avant/après précis
- 🔧 **Gestion soldes améliorée** : Fermeture virtuelle sécurisée
- 🔧 **Validation multi-niveau** : Vérifications exposition renforcées

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

> "Version 3.0 Enhanced Edition - Votre bot ultra-sécurisé pour conquérir les marchés avec une protection maximale et des gains optimisés !"

### 🏆 Stats actuelles du bot
- **Capital géré** : 19,650+ EUR 
- **Protections actives** : ✅ Surexposition BTC/ETH bloquée
- **Signaux détectés** : ✅ EMA + MACD + Bollinger convergents
- **Prêt au trading** : ✅ Attente volatilité >0.5% pour reprise
- **Sécurité** : 🛡️ Niveau maximum - Aucun risque de surexposition
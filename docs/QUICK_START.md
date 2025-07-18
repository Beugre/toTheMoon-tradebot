# 🚀 Guide de Démarrage Rapide - Bot de Trading Scalping

## ⚡ Installation Express

### 1. Installation automatique
```bash
# Installation des dépendances
pip install -r requirements.txt

# Test de l'installation
python test_install.py
```

### 2. Configuration des APIs

#### 🔑 Binance API
1. Créez un compte sur [Binance](https://binance.com)
2. API Management → Créer une API
3. Permissions nécessaires : **Spot & Margin Trading**
4. Ajoutez dans `.env` :
```
BINANCE_API_KEY=votre_api_key
BINANCE_SECRET_KEY=votre_secret_key
BINANCE_TESTNET=True  # Pour les tests
```

#### 📱 Telegram Bot
1. Créez un bot : [@BotFather](https://t.me/BotFather)
2. Commande : `/newbot`
3. Récupérez le token
4. Obtenez votre chat ID : [@userinfobot](https://t.me/userinfobot)
5. Ajoutez dans `.env` :
```
TELEGRAM_BOT_TOKEN=votre_bot_token
TELEGRAM_CHAT_ID=votre_chat_id
```

#### 📊 Google Sheets
1. [Google Cloud Console](https://console.cloud.google.com)
2. Créez un projet
3. Activez Google Sheets API
4. Créez un service account
5. Téléchargez `credentials.json`
6. Créez un spreadsheet
7. Partagez avec l'email du service account
8. Ajoutez dans `.env` :
```
GOOGLE_SHEETS_SPREADSHEET_ID=votre_spreadsheet_id
```

### 3. Lancement

#### Mode Test (Recommandé)
```bash
python run.py
```

#### Mode Production
```bash
# Modifiez .env
BINANCE_TESTNET=False

# Lancez
python run.py
```

## 🎯 Configuration Personnalisée

### Fichier .env
```bash
# === TRADING ===
DAILY_TARGET_PERCENT=1.0        # Objectif quotidien +1%
DAILY_STOP_LOSS_PERCENT=1.0     # Stop loss quotidien -1%
POSITION_SIZE_PERCENT=17.5      # Taille position 17.5%
MAX_OPEN_POSITIONS=3            # Max 3 positions simultanées

# === RISQUE ===
STOP_LOSS_PERCENT=0.5           # SL -0.5% par trade
TAKE_PROFIT_PERCENT=1.0         # TP +1% par trade
TRAILING_ACTIVATION_PERCENT=0.5 # Trailing à +0.5%
TRAILING_STEP_PERCENT=0.3       # Step trailing 0.3%

# === MARCHÉ ===
MIN_VOLUME_EUR=100000           # Volume min 100k EUR
MAX_SPREAD_PERCENT=0.2          # Spread max 0.2%
SCAN_INTERVAL=60                # Scan toutes les 60s
```

## 📊 Monitoring en Temps Réel

### Console
```
[10:12:45] ✅ Signal détecté : BTC/EUR (Score : 3.5/4)
[10:12:47] 📈 Achat à 25 320 € | SL : -0.5% | TP : +1%
[10:15:10] 🚀 TP atteint via trailing : +1.2% (+21,60 €)
```

### Telegram
- 🚀 Notifications de démarrage
- 📈 Ouverture/fermeture de trades
- 📊 Résumé quotidien
- ⚠️ Alertes d'erreur

### Google Sheets
- **Onglet Trades** : Historique détaillé
- **Onglet Performance** : Métriques quotidiennes
- **Onglet Dashboard** : Vue d'ensemble

## 🛡️ Sécurité & Risques

### Paramètres de Sécurité
- ✅ Stop Loss obligatoire (-0.5%)
- ✅ Take Profit automatique (+1%)
- ✅ Trailing Stop (+0.5%)
- ✅ Timeout 15 minutes
- ✅ Stop loss quotidien (-1%)
- ✅ Objectif quotidien (+1%)

### Limites
- 🛡️ Maximum 3 positions simultanées
- 🛡️ 15-20% du capital par trade
- 🛡️ Paires EUR uniquement
- 🛡️ Volume minimum 100k EUR
- 🛡️ Spread maximum 0.2%

## 🔧 Dépannage Express

### Erreurs Courantes
```bash
# Erreur : No module named 'talib'
python install_talib.py

# Erreur : Binance API
# Vérifiez vos clés dans .env
# Activez le trading sur Binance

# Erreur : Telegram
# Vérifiez token et chat ID
# Testez avec @BotFather

# Erreur : Google Sheets
# Vérifiez credentials.json
# Partagez le spreadsheet
```

### Commandes Utiles
```bash
# Test complet
python test_install.py

# Logs en temps réel
Get-Content logs/trading_bot.log -Tail 10 -Wait

# Nettoyage
Remove-Item logs/*.log
```

## 🚀 Lancement Rapide

### 1. Installation
```bash
git clone <repo>
cd toTheMoon_tradebot
pip install -r requirements.txt
python test_install.py
```

### 2. Configuration
```bash
# Copiez et éditez .env
copy .env.example .env
notepad .env

# Ajoutez vos clés API
```

### 3. Test
```bash
# Mode testnet
python run.py
```

### 4. Production
```bash
# Modifiez BINANCE_TESTNET=False dans .env
python run.py
```

## 📈 Stratégie Résumée

### Sélection Paires
- ✅ Paires EUR uniquement
- ✅ Volume > 100k EUR
- ✅ Spread < 0.2%
- ✅ Score : 60% volatilité + 40% volume

### Signaux d'Entrée (≥3 requis)
- ✅ EMA(9) > EMA(21)
- ✅ MACD > Signal
- ✅ RSI < 40
- ✅ Prix près Bollinger inf.

### Gestion Position
- 📈 Entrée : Market Order
- 🛑 SL : -0.5% automatique
- 🎯 TP : +1% automatique
- 🔄 Trailing : +0.5% activation
- ⏰ Timeout : 15 minutes

### Arrêt Auto
- ✅ +1% objectif atteint
- 🛑 -1% stop loss atteint
- 🔄 Fin de journée

## 📞 Support

- 📧 Logs : `logs/trading_bot.log`
- 📱 Telegram : Notifications temps réel
- 📊 Sheets : Données historiques
- 🔧 Test : `python test_install.py`

---

**⚠️ AVERTISSEMENT : Ce bot est fourni à des fins éducatives. Le trading comporte des risques. Utilisez uniquement des fonds que vous pouvez perdre.**

**🚀 Bon trading ! 📈**

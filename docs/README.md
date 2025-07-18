# Bot de Trading Scalping - ToTheMoon TradeBot

Un bot de trading automatisé spécialisé dans le scalping sur les paires EUR avec gestion dynamique du capital et analyse technique avancée.

## 🚀 Fonctionnalités

### 📊 Trading Automatisé
- **Gestion dynamique du capital** - Récupération en temps réel via API Binance
- **Multi-paires EUR** - Sélection automatique des meilleures paires
- **Signaux techniques** - EMA, MACD, RSI, Bollinger Bands
- **Gestion des risques** - Stop Loss, Take Profit, Trailing Stop
- **Objectif quotidien** - +1% du capital avec stop loss à -1%
- **Positions simultanées** - Maximum 3 positions ouvertes

### 🔍 Analyse Technique
- **Moyennes mobiles** - EMA 9 et EMA 21
- **MACD** - Momentum et signaux de croisement
- **RSI** - Zones de survente/surachat
- **Bollinger Bands** - Support/résistance dynamique
- **Volume** - Confirmation des signaux
- **Patterns chandeliers** - Détection automatique

### 🛡️ Gestion des Risques
- **Stop Loss** - -0.5% par trade
- **Take Profit** - +1% par trade
- **Trailing Stop** - Activation à +0.5%, step 0.3%
- **Timeout** - Sortie automatique après 15 minutes si < +0.2%
- **Diversification** - Évite les corrélations excessives

### 📱 Notifications & Logging
- **Telegram** - Notifications en temps réel
- **Google Sheets** - Suivi des performances
- **Console** - Logging détaillé avec couleurs
- **Fichiers** - Logs rotatifs pour audit

## 🛠️ Installation

### 1. Prérequis
```bash
# Python 3.9+ requis
python --version

# Installation des dépendances
pip install -r requirements.txt
```

### 2. Configuration des APIs

#### Binance API
1. Créez un compte sur [Binance](https://binance.com)
2. Générez une clé API avec permissions trading
3. Ajoutez vos clés dans `.env`

#### Telegram Bot
1. Créez un bot via [@BotFather](https://t.me/BotFather)
2. Récupérez le token
3. Obtenez votre chat ID
4. Ajoutez les informations dans `.env`

#### Google Sheets
1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com)
2. Activez l'API Google Sheets
3. Créez un compte de service
4. Téléchargez `credentials.json`
5. Créez un spreadsheet et partagez-le avec le service account

### 3. Configuration
```bash
# Copiez le fichier d'exemple
cp .env.example .env

# Éditez et remplissez vos clés API
nano .env
```

## 🚀 Utilisation

### Lancement Simple
```bash
python run.py
```

### Lancement avec Mode Debug
```bash
DEBUG=True python run.py
```

### Mode Testnet
```bash
BINANCE_TESTNET=True python run.py
```

## 📊 Stratégie de Trading

### Sélection des Paires
1. **Scan automatique** - Toutes les paires EUR
2. **Filtres** - Volume > 100k EUR, Spread < 0.2%
3. **Score de sélection** - 60% volatilité + 40% volume
4. **Top 5 paires** - Analysées en continu

### Conditions d'Entrée (≥ 3 requis)
- ✅ EMA(9) > EMA(21)
- ✅ MACD Line > Signal Line
- ✅ RSI < 40 (zone de rebond)
- ✅ Prix près de Bollinger Band inférieure

### Gestion des Positions
- **Taille** - 15-20% du capital disponible
- **Stop Loss** - -0.5% automatique
- **Take Profit** - +1% automatique
- **Trailing Stop** - Actif dès +0.5%
- **Timeout** - 15 minutes max

### Arrêt Automatique
- ✅ Objectif +1% atteint
- 🛑 Perte -1% atteinte
- 🔄 Fin de journée

## 📈 Monitoring

### Console
```
[10:12:45] ✅ Signal détecté : BTC/EUR (Score : 3.5/4)
[10:12:47] 📈 Achat à 25 320 € | SL : -0.5% | TP : +1%
[10:15:10] 🚀 TP atteint via trailing : +1.2% (+21,60 €)
[10:15:10] 🔄 Total journalier : +0.9%
```

### Telegram
- 🚀 Démarrage du bot
- 📈 Ouverture de trades
- 🚀 Fermeture de trades
- 📊 Résumé quotidien

### Google Sheets
- **Onglet Trades** - Historique détaillé
- **Onglet Performance** - Métriques quotidiennes
- **Onglet Dashboard** - Vue d'ensemble temps réel

## ⚙️ Configuration Avancée

### Paramètres Trading
```python
# config.py
DAILY_TARGET_PERCENT = 1.0      # Objectif quotidien
DAILY_STOP_LOSS_PERCENT = 1.0   # Stop loss quotidien
POSITION_SIZE_PERCENT = 17.5    # Taille position
MAX_OPEN_POSITIONS = 3          # Positions max
STOP_LOSS_PERCENT = 0.5         # SL par trade
TAKE_PROFIT_PERCENT = 1.0       # TP par trade
```

### Paramètres Techniques
```python
EMA_FAST_PERIOD = 9
EMA_SLOW_PERIOD = 21
RSI_PERIOD = 14
RSI_OVERSOLD_LEVEL = 40
BOLLINGER_PERIOD = 20
```

### Paramètres Marché
```python
MIN_VOLUME_EUR = 100000         # Volume minimum
MAX_SPREAD_PERCENT = 0.2        # Spread maximum
SCAN_INTERVAL = 60              # Scan toutes les 60s
```

## 🔒 Sécurité

### Bonnes Pratiques
- ✅ Clés API jamais en dur dans le code
- ✅ Variables d'environnement sécurisées
- ✅ Gestion d'erreurs robuste
- ✅ Validation des paramètres
- ✅ Logging complet pour audit

### Limitations
- 🛡️ Capital maximum par position
- 🛡️ Nombre maximum de positions
- 🛡️ Stop loss quotidien obligatoire
- 🛡️ Rate limiting API
- 🛡️ Timeout sur trades

## 🐛 Dépannage

### Erreurs Communes
1. **Clés API invalides** - Vérifiez vos credentials
2. **Permissions insuffisantes** - Activez le trading sur Binance
3. **Telegram non configuré** - Vérifiez token et chat ID
4. **Google Sheets** - Vérifiez credentials.json et partage

### Logs
```bash
# Logs détaillés
tail -f logs/trading_bot.log

# Erreurs uniquement
grep ERROR logs/trading_bot.log
```

## 📊 Performance

### Objectifs
- 🎯 **Rendement quotidien** - +1% du capital
- 🎯 **Win rate** - > 60%
- 🎯 **Profit factor** - > 1.5
- 🎯 **Max drawdown** - < 2%

### Métriques Suivies
- P&L quotidien (EUR et %)
- Nombre de trades
- Durée moyenne des trades
- Win rate et profit factor
- Drawdown maximum

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ⚠️ Avertissement

**Ce bot est fourni à des fins éducatives uniquement. Le trading comporte des risques importants et vous pouvez perdre tout votre capital. Utilisez uniquement des fonds que vous pouvez vous permettre de perdre. L'auteur n'est pas responsable des pertes financières.**

## 📞 Support

- 📧 Email: support@example.com
- 💬 Telegram: @tradingbot_support
- 📊 Suivi: [Google Sheets Template](https://docs.google.com/spreadsheets/d/your-template-id)

---

**Happy Trading! 🚀📈**

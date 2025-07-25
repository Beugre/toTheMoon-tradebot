# 🌐 SYSTÈME PROXY VPS BINANCE - DOCUMENTATION COMPLÈTE

## 🎯 Objectif

Résoudre le problème d'IP géographique entre Binance Europe et Streamlit Cloud USA en créant un système proxy sur VPS européen.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│                 │    │                  │    │                 │    │                  │
│  VPS (Europe)   │◄──►│  Binance API     │    │  Firebase       │◄──►│ Streamlit (USA)  │
│  - Proxy Service│    │  (Whitelisted)   │    │  - Collection   │    │  - Monitor UI    │
│  - Collecte 60s │    │  - IP EU OK      │    │  - binance_live │    │  - Lecture seule │
│                 │    │                  │    │                 │    │                  │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
```

## 📁 Structure du Projet

```
toTheMoon_tradebot/
├── utils/
│   └── binance_proxy_service.py     # 🔧 Service principal VPS
├── scripts/
│   ├── start_binance_proxy.py       # 🚀 Gestionnaire avec retry
│   └── deploy_vps_proxy.sh          # 📦 Déploiement automatique
├── monitor_realtime.py              # 🖥️ Interface Streamlit (modifiée)
└── PROXY_VPS_BINANCE_DOCS.md        # 📚 Cette documentation
```

## 🔧 Composants

### 1️⃣ **Service Proxy VPS** (`binance_proxy_service.py`)

**Responsabilités :**
- Collecte données Binance toutes les 60 secondes
- Stockage dans Firebase collection `binance_live`
- Gestion erreurs et reconnexion automatique
- Logging complet des opérations

**Données collectées :**
- **Account Info** : Balances, permissions trading
- **Recent Trades** : Historique 24h pour toutes les paires
- **Open Orders** : Ordres actifs sur toutes les paires

### 2️⃣ **Gestionnaire de Service** (`start_binance_proxy.py`)

**Fonctionnalités :**
- Restart automatique en cas d'erreur
- Gestion des signaux système (SIGINT, SIGTERM)
- Création service systemd automatique
- Health checks périodiques

### 3️⃣ **Interface Streamlit Modifiée** (`monitor_realtime.py`)

**Changements :**
- ❌ Plus d'appels directs Binance API
- ✅ Lecture données Firebase `binance_live`
- ✅ Alertes si données VPS obsolètes (> 5min)
- ✅ Comparaison Bot vs Binance (VPS)

## 🔥 Structure Firebase

### Collection `binance_live`

```javascript
binance_live: {
  // Informations compte (mise à jour 60s)
  account_info: {
    timestamp: "2025-01-25T10:30:00",
    balances: [
      {asset: "USDC", free: 1000.0, locked: 0.0, total: 1000.0},
      {asset: "BTC", free: 0.001, locked: 0.0, total: 0.001}
    ],
    canTrade: true,
    canWithdraw: true,
    accountType: "SPOT"
  },
  
  // Trades récents (mise à jour 60s)
  recent_trades: {
    timestamp: "2025-01-25T10:30:00",
    trades: [
      {
        symbol: "BTCUSDC",
        time: "2025-01-25T10:29:30",
        side: "BUY",
        price: 45000.0,
        qty: 0.001,
        quoteQty: 45.0,
        orderId: "123456789",
        commission: 0.045
      }
    ],
    pairs_monitored: ["BTCUSDC", "ETHUSDC", ...],
    total_trades: 5
  },
  
  // Ordres ouverts (mise à jour 60s)
  open_orders: {
    timestamp: "2025-01-25T10:30:00",
    orders: [
      {
        symbol: "BTCUSDC",
        orderId: "987654321",
        side: "SELL",
        type: "LIMIT",
        status: "NEW",
        price: 46000.0,
        origQty: 0.001,
        executedQty: 0.0
      }
    ],
    total_orders: 2
  }
}
```

## 🚀 Déploiement VPS

### 1️⃣ **Préparation**

```bash
# Sur votre machine locale
scp -r toTheMoon_tradebot/ root@your-vps-ip:/opt/
scp scripts/deploy_vps_proxy.sh root@your-vps-ip:/opt/toTheMoon_tradebot/
```

### 2️⃣ **Configuration**

```bash
# Sur le VPS
cd /opt/toTheMoon_tradebot

# Créer .env avec vos clés Binance
nano .env
```

**Contenu `.env` :**
```
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
```

```bash
# Copier firebase_credentials.json
scp firebase_credentials.json root@your-vps-ip:/opt/toTheMoon_tradebot/
```

### 3️⃣ **Déploiement Automatique**

```bash
# Sur le VPS
chmod +x scripts/deploy_vps_proxy.sh
./scripts/deploy_vps_proxy.sh
```

**Le script automatise :**
- ✅ Installation dépendances système
- ✅ Création environnement Python
- ✅ Installation packages requis
- ✅ Configuration service systemd
- ✅ Démarrage automatique

## 🎛️ Gestion du Service

### **Commandes Principales**

```bash
# Status du service
systemctl status binance-proxy

# Logs en temps réel
journalctl -u binance-proxy -f

# Redémarrer le service
systemctl restart binance-proxy

# Arrêter le service
systemctl stop binance-proxy

# Désactiver le service
systemctl disable binance-proxy
```

### **Logs Détaillés**

```bash
# Logs du service proxy
tail -f /opt/toTheMoon_tradebot/logs/binance_proxy.log

# Logs du gestionnaire
tail -f /opt/toTheMoon_tradebot/logs/proxy_manager.log
```

## 📊 Monitoring

### **Interface Streamlit**

L'interface modifiée affiche maintenant :
- 🟢 **Indicateur fraîcheur** données VPS
- 🔍 **Comparaison** Bot vs Binance (VPS)
- ⚠️ **Alertes** si données obsolètes (> 5min)
- 📊 **Métriques** identiques mais via proxy

### **Vérification Firebase**

```bash
# Vérifier la collection binance_live
# Les documents account_info, recent_trades, open_orders
# doivent être mis à jour toutes les 60 secondes
```

## 🔧 Dépannage

### **Service ne démarre pas**

```bash
# Vérifier les logs
journalctl -u binance-proxy -n 50

# Vérifier la configuration
python3 /opt/toTheMoon_tradebot/scripts/start_binance_proxy.py --check-env

# Test manuel
cd /opt/toTheMoon_tradebot
source venv/bin/activate
python3 utils/binance_proxy_service.py
```

### **Données obsolètes Firebase**

```bash
# Vérifier la connectivité Binance
curl -s https://api.binance.com/api/v3/ping

# Vérifier les clés API
grep BINANCE /opt/toTheMoon_tradebot/.env

# Redémarrer le service
systemctl restart binance-proxy
```

### **Erreurs de permissions**

```bash
# Corriger les permissions
chown -R root:root /opt/toTheMoon_tradebot
chmod -R 755 /opt/toTheMoon_tradebot
chmod -R 777 /opt/toTheMoon_tradebot/logs
```

## ⚡ Performance

### **Timing Optimisé**

- **Collecte** : 60 secondes (équilibre perf/fraîcheur)
- **Health Check** : 10 minutes
- **Cleanup** : 48 heures de rétention
- **Retry** : 5 tentatives max avec délai 30s

### **Ressources VPS**

- **RAM** : ~50 MB par instance
- **CPU** : Négligeable (collecte passive)
- **Réseau** : ~1-2 KB/minute
- **Stockage** : ~10 MB logs/jour

## 🔄 Maintenance

### **Mise à jour du Code**

```bash
# Sur votre machine locale
scp utils/binance_proxy_service.py root@vps:/opt/toTheMoon_tradebot/utils/

# Sur le VPS
systemctl restart binance-proxy
```

### **Rotation des Logs**

```bash
# Configurer logrotate
nano /etc/logrotate.d/binance-proxy
```

**Contenu logrotate :**
```
/opt/toTheMoon_tradebot/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
    postrotate
        systemctl reload binance-proxy
    endscript
}
```

## 🎯 Avantages du Système

### ✅ **Résolution IP**
- VPS Europe peut whitelister Binance
- Streamlit Cloud n'a plus de restrictions

### ✅ **Performance**
- Streamlit plus rapide (lecture Firebase vs API)
- Moins de limites de rate API

### ✅ **Fiabilité**
- Service indépendant sur VPS
- Restart automatique en cas d'erreur
- Données persistantes 48h

### ✅ **Sécurité**
- Clés API centralisées sur VPS
- Streamlit en lecture seule
- Logs détaillés pour audit

### ✅ **Scalabilité**
- Plusieurs clients peuvent lire les données
- Facilement extensible à d'autres exchanges
- Architecture microservice

---

## 🚀 **Le système est maintenant opérationnel !**

1. **VPS** collecte les données Binance Europe ✅
2. **Firebase** centralise les données ✅  
3. **Streamlit** lit les données sans restriction IP ✅
4. **Monitoring** complet avec alertes ✅

**Votre bot de trading peut maintenant fonctionner sans limitation géographique !** 🌍🎯

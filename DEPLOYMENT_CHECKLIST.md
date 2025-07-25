# 🚀 Checklist de Déploiement VPS Proxy Binance

## ✅ Validation pré-déploiement
- [x] Tests de découverte USDC (210 paires détectées)
- [x] Agrégation des trades dans monitor_realtime.py
- [x] Correction des erreurs Unicode Windows
- [x] 50 trades récents détectés (BNBUSDC + SAHARAUSDC)
- [x] 22k USDC balance confirmée

## 📂 Fichiers à copier sur le VPS

### Scripts principaux
- `utils/binance_proxy_service.py` - Service principal
- `scripts/start_binance_proxy.py` - Manager de service
- `scripts/deploy_vps_proxy.sh` - Script de déploiement
- `scripts/test_usdc_discovery.py` - Tests de validation

### Configuration
- `.env` - Variables d'environnement (BINANCE_API_KEY, BINANCE_SECRET_KEY)
- `firebase_credentials.json` - Clés Firebase
- `requirements.txt` - Dépendances Python

### Interface de monitoring
- `monitor_realtime.py` - Interface Streamlit modifiée pour proxy

## 🔧 Étapes de déploiement

### Étape 1: Connexion et préparation VPS
```bash
# Se connecter au VPS européen
ssh user@your-vps-ip

# Créer le répertoire de travail
sudo mkdir -p /opt/toTheMoon_tradebot
sudo chown $USER:$USER /opt/toTheMoon_tradebot
cd /opt/toTheMoon_tradebot
```

### Étape 2: Copie des fichiers
```bash
# Depuis votre machine locale
scp -r utils/ scripts/ user@your-vps-ip:/opt/toTheMoon_tradebot/
scp .env firebase_credentials.json requirements.txt user@your-vps-ip:/opt/toTheMoon_tradebot/
scp monitor_realtime.py user@your-vps-ip:/opt/toTheMoon_tradebot/
```

### Étape 3: Installation des dépendances
```bash
# Sur le VPS
cd /opt/toTheMoon_tradebot
python3 -m pip install -r requirements.txt
```

### Étape 4: Déploiement automatique
```bash
# Exécuter le script de déploiement
chmod +x scripts/deploy_vps_proxy.sh
./scripts/deploy_vps_proxy.sh
```

### Étape 5: Validation
```bash
# Test de fonctionnement
python3 scripts/test_usdc_discovery.py

# Vérifier le service systemd
sudo systemctl status binance-proxy
sudo journalctl -u binance-proxy -f
```

## 🔍 Monitoring post-déploiement

### Interface Streamlit (local)
- Modifier `monitor_realtime.py` pour utiliser les données Firebase du VPS
- Vérifier la réception des données en temps réel
- Valider l'agrégation des trades fragmentés

### Métriques à surveiller
- ✅ Fraîcheur des données VPS (< 5 min)
- ✅ Nombre de paires USDC surveillées (50)
- ✅ Ratio fragmentation des trades
- ✅ Correspondance Bot/Binance agrégé

## 🚨 Dépannage

### Service ne démarre pas
```bash
sudo journalctl -u binance-proxy --no-pager
python3 -c "from utils.binance_proxy_service import BinanceProxyService; BinanceProxyService()"
```

### Données Firebase vides
```bash
# Vérifier la connexion Firebase
python3 -c "import firebase_admin; print('Firebase OK')"
```

### Erreurs de clés API
```bash
# Vérifier les variables d'environnement
grep BINANCE /opt/toTheMoon_tradebot/.env
```

## ✅ Validation finale
- [ ] Service systemd actif
- [ ] Données Firebase mises à jour
- [ ] Interface Streamlit fonctionnelle
- [ ] 210 paires USDC détectées
- [ ] Monitoring en temps réel opérationnel

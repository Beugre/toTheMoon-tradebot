# 🚀 Déploiement Rapide - toTheMoon Bot

## ⚡ TL;DR - Déploiement en 3 commandes

### Sur le VPS:
```bash
# 1. Clone (première fois seulement)
git clone https://github.com/Beugre/toTheMoon-tradebot.git
cd toTheMoon-tradebot

# 2. Configuration (première fois seulement)
cp .env.firebase.template .env
nano .env  # Remplir vos clés API
# Uploader firebase_credentials.json

# 3. Déploiement
chmod +x deploy.sh && ./deploy.sh
```

### Mises à jour:
```bash
./update.sh
```

## 📊 Monitoring
```bash
# Status
sudo systemctl status toTheMoon-bot

# Logs temps réel  
sudo journalctl -u toTheMoon-bot -f
```

## 🔥 Firebase Analytics
- **Console**: https://console.firebase.google.com/
- **Projet**: `tothemoon-9e4d5`
- **Données**: Logs, trades, performances en temps réel

---

**📋 Guide complet**: Voir `DEPLOYMENT_GUIDE.md`

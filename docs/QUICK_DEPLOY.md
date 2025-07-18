# 🚀 GUIDE DE DÉPLOIEMENT RAPIDE - TOTHEMOON BOT

## ✅ PRÉ-REQUIS ACCOMPLIS
- ✅ Base de données SQLite intégrée
- ✅ Rapports d'investisseurs automatisés  
- ✅ Scripts de déploiement VPS complets
- ✅ Service systemd configuré
- ✅ Documentation complète

## 🎯 DÉPLOIEMENT EN 4 ÉTAPES

### 1. VÉRIFICATION PRÉ-DÉPLOIEMENT
```bash
python pre_deploy_check.py
```

### 2. DÉPLOIEMENT SUR VPS
```bash
# Windows
deploy.bat

# Linux/Mac  
./scripts/full_deploy.sh
```

### 3. CONFIGURATION SUR VPS
```bash
ssh root@213.199.41.168
cd /opt/toTheMoon_tradebot
nano .env
# Copier votre configuration .env locale
```

### 4. DÉMARRAGE DU SERVICE
```bash
systemctl start tothemoon-tradebot
systemctl status tothemoon-tradebot
journalctl -u tothemoon-tradebot -f
```

## 📊 COMMANDES DE MONITORING

### Service systemd
```bash
systemctl status tothemoon-tradebot    # Statut
systemctl restart tothemoon-tradebot   # Redémarrage
systemctl stop tothemoon-tradebot      # Arrêt
```

### Logs en temps réel
```bash
journalctl -u tothemoon-tradebot -f           # Logs service
journalctl -u tothemoon-tradebot --since today # Logs du jour
```

### Rapports d'investisseurs
```bash
cd /opt/toTheMoon_tradebot
source venv/bin/activate

python3 investor_report.py summary              # Résumé rapide
python3 investor_report.py report 30            # Rapport 30 jours
python3 investor_report.py report 90 custom.json # Rapport personnalisé
```

## 🔧 MAINTENANCE

### Mise à jour du bot
```bash
systemctl stop tothemoon-tradebot
rsync -avz --exclude='data/' --exclude='logs/' ./ root@213.199.41.168:/opt/toTheMoon_tradebot/
systemctl start tothemoon-tradebot
```

### Sauvegarde des données
```bash
scp root@213.199.41.168:/opt/toTheMoon_tradebot/data/trading_bot.db ./backup_$(date +%Y%m%d).db
```

### Vérification de santé
```bash
ssh root@213.199.41.168 "systemctl is-active tothemoon-tradebot && echo 'Bot actif' || echo 'Bot arrêté'"
```

## 📈 NOUVELLES FONCTIONNALITÉS

### Base de données SQLite
- 📊 Tous les trades enregistrés automatiquement
- 📈 Tracking des trailing stops en temps réel
- 📅 Performances journalières archivées
- ⚡ Métriques temps réel toutes les 10 minutes

### Rapports d'investisseurs
- 📋 Résumés de performance détaillés
- 📊 Métriques avancées (Sharpe ratio, max drawdown)
- 💾 Export JSON pour outils d'analyse
- 📈 Historique complet des trades

### Monitoring système
- 🔄 Service systemd avec redémarrage automatique
- 📝 Logs centralisés avec journalctl
- 🎯 Métriques de performance en continu
- 🚨 Notifications d'erreurs automatiques

## 🚨 POINTS D'ATTENTION

1. **Configuration .env** : Doit être identique à votre version locale
2. **Google Sheets** : Optionnel, credentials.json si activé
3. **Monitoring** : Surveiller les logs régulièrement
4. **Sauvegardes** : Base de données contient toutes les données importantes

## 📞 AIDE RAPIDE

### Problème de connexion SSH
```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id root@213.199.41.168
```

### Bot ne démarre pas
```bash
journalctl -u tothemoon-tradebot --no-pager | tail -50
# Vérifier la configuration .env et les permissions
```

### Performance lente
```bash
top -p $(pgrep -f tothemoon)
free -h
# Vérifier l'utilisation ressources
```

---

**🎉 LE BOT EST PRÊT POUR LA PRODUCTION !**

Votre bot ToTheMoon dispose maintenant de :
- ✅ Système de base de données professionnel
- ✅ Rapports automatisés pour investisseurs  
- ✅ Déploiement automatisé sur VPS
- ✅ Monitoring et maintenance simplifiés
- ✅ Métriques avancées de performance

**Commencez par :** `python pre_deploy_check.py` puis `deploy.bat`

# 🚀 ToTheMoon Trading Bot - Commandes Utiles

Ce fichier contient toutes les commandes essentielles pour gérer le bot de trading déployé sur le VPS.

## 🔧 Variables d'environnement
```bash
VPS_HOST="root@213.199.41.168"
BOT_DIR="/opt/toTheMoon_tradebot"
SERVICE_NAME="tothemoon-tradebot"
```

## 📡 Connexion SSH
```bash
# Connexion au VPS
ssh root@213.199.41.168

# Connexion directe dans le répertoire du bot
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && bash"
```

## 🚀 Déploiement

### Déploiement complet (depuis Windows)
```powershell
# Exécution du script de déploiement complet
./scripts/deploy_simple.ps1
```

### Déploiement complet (depuis Linux/Mac)
```bash
# Exécution du script de déploiement complet
./scripts/full_deploy.sh
```

### Mise à jour rapide du code
```bash
# Copie uniquement les fichiers modifiés
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='.env' \
    ./ root@213.199.41.168:/opt/toTheMoon_tradebot/

# Redémarrage du service après mise à jour
ssh root@213.199.41.168 "systemctl restart tothemoon-tradebot"
```

## ⚙️ Gestion du Service Systemd

### Statut du service
```bash
ssh root@213.199.41.168 "systemctl status tothemoon-tradebot"
```

### Démarrage du service
```bash
ssh root@213.199.41.168 "systemctl start tothemoon-tradebot"
```

### Arrêt du service
```bash
ssh root@213.199.41.168 "systemctl stop tothemoon-tradebot"
```

### Redémarrage du service
```bash
ssh root@213.199.41.168 "systemctl restart tothemoon-tradebot"
```

### Activation au démarrage
```bash
ssh root@213.199.41.168 "systemctl enable tothemoon-tradebot"
```

### Désactivation au démarrage
```bash
ssh root@213.199.41.168 "systemctl disable tothemoon-tradebot"
```

### Rechargement de la configuration
```bash
ssh root@213.199.41.168 "systemctl daemon-reload"
```

## 📊 Monitoring et Logs

### Logs en temps réel
```bash
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot -f"
```

### Logs des dernières 24h
```bash
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot --since '24 hours ago'"
```

### Logs avec nombre de lignes spécifique
```bash
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot -n 100"
```

### Logs d'erreur uniquement
```bash
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot -p err"
```

### Vérification des processus Python
```bash
ssh root@213.199.41.168 "ps aux | grep python"
```

### Utilisation des ressources
```bash
ssh root@213.199.41.168 "top -p \$(pgrep -f 'run.py')"
```

### Espace disque
```bash
ssh root@213.199.41.168 "df -h /opt/toTheMoon_tradebot"
```

## 🗄️ Base de Données SQLite

### Consultation de la base de données
```bash
# Connexion à la base de données
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && sqlite3 trading_bot.db"
```

### Requêtes SQL utiles
```sql
-- Voir les tables disponibles
.tables

-- Voir le schéma d'une table
.schema trades

-- Voir les derniers trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- Statistiques des trades par paire
SELECT symbol, COUNT(*) as nb_trades, 
       AVG(profit_loss) as avg_profit, 
       SUM(profit_loss) as total_profit
FROM trades 
WHERE profit_loss IS NOT NULL 
GROUP BY symbol;

-- Performance du jour
SELECT symbol, side, quantity, price, profit_loss, timestamp 
FROM trades 
WHERE DATE(timestamp) = DATE('now') 
ORDER BY timestamp DESC;

-- Trades les plus profitables
SELECT * FROM trades 
WHERE profit_loss > 0 
ORDER BY profit_loss DESC 
LIMIT 5;

-- Quitter SQLite
.quit
```

### Sauvegarde de la base de données
```bash
# Sauvegarde locale
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && cp trading_bot.db trading_bot_backup_\$(date +%Y%m%d_%H%M%S).db"

# Téléchargement de la sauvegarde
scp root@213.199.41.168:/opt/toTheMoon_tradebot/trading_bot.db ./backup_trading_bot.db
```

## 📱 Test et Debug

### Test en mode dry-run
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 run.py --test"
```

### Test des modules individuels
```bash
# Test de l'API Binance
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from binance.client import Client; print(\"✅ Binance OK\")'"

# Test de TA-Lib
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'import talib; print(\"✅ TA-Lib OK\")'"

# Test de Telegram
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from utils.telegram_notifier import TelegramNotifier; print(\"✅ Telegram OK\")'"
```

### Vérification de la configuration
```bash
# Voir le fichier .env (sans afficher les clés)
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && grep -v 'API_KEY\|SECRET\|TOKEN' .env"

# Vérifier les permissions
ssh root@213.199.41.168 "ls -la /opt/toTheMoon_tradebot/"
```

## 🔄 Mise à jour et Maintenance

### Mise à jour des dépendances Python
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && pip install --upgrade -r requirements.txt"
```

### Nettoyage des logs anciens
```bash
ssh root@213.199.41.168 "journalctl --vacuum-time=7d"
```

### Redémarrage complet du VPS
```bash
ssh root@213.199.41.168 "reboot"
```

## 📈 Rapports et Analyse

### Génération du rapport d'investisseur
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 investor_report.py"
```

### Consultation des métriques
```bash
# Voir les soldes actuels
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); print(bot.get_account_balance())'"
```

## 🚨 Gestion d'Urgence

### Arrêt d'urgence du bot
```bash
ssh root@213.199.41.168 "systemctl stop tothemoon-tradebot && pkill -f run.py"
```

### Fermeture de toutes les positions ouvertes
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); bot.close_all_positions()'"
```

### Vérification des positions ouvertes
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); print(bot.get_open_positions())'"
```

## 📋 Commandes de Débogage Rapide

### One-liner pour vérifier que tout va bien
```bash
ssh root@213.199.41.168 "systemctl is-active tothemoon-tradebot && echo '✅ Service actif' || echo '❌ Service arrêté'"
```

### Résumé complet du statut
```bash
ssh root@213.199.41.168 "
echo '🔍 STATUT DU BOT TOTHEMOON'
echo '========================='
echo '📊 Service:' \$(systemctl is-active tothemoon-tradebot)
echo '💾 Mémoire:' \$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -p \$(pgrep -f run.py) | tail -n +2)
echo '📁 Espace disque:' \$(df -h /opt/toTheMoon_tradebot | tail -1 | awk '{print \$4\" disponible\"}')
echo '🕐 Uptime:' \$(systemctl show tothemoon-tradebot --property=ActiveEnterTimestamp --value)
echo '📈 Dernière activité:'
journalctl -u tothemoon-tradebot -n 3 --no-pager
"
```

---

## 💡 Notes Importantes

1. **Sécurité** : Ne jamais partager les commandes contenant des clés API
2. **Backup** : Faire des sauvegardes régulières de la base de données
3. **Monitoring** : Surveiller les logs régulièrement
4. **Updates** : Tester les mises à jour en mode test avant déploiement
5. **Resources** : Surveiller l'utilisation mémoire et CPU

---

*Généré le $(date) - ToTheMoon Trading Bot v1.0*

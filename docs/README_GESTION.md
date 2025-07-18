# 🛠️ Guide d'Utilisation - Outils de Gestion du Bot

Ce dossier contient tous les outils nécessaires pour gérer votre bot de trading ToTheMoon déployé sur le VPS.

## 📋 Fichiers Disponibles

### 📖 Documentation
- **`commandes_utiles.md`** - Liste complète de toutes les commandes SSH utiles
- **`README_GESTION.md`** - Ce fichier (guide d'utilisation)

### 🚀 Scripts de Déploiement
- **`full_deploy.sh`** - Script de déploiement complet (Linux/Mac)
- **`deploy_simple.ps1`** - Script de déploiement simplifié (Windows)
- **`deploy_windows.ps1`** - Script de déploiement Windows avec fonctionnalités avancées

### 🎛️ Gestionnaires Interactifs
- **`gestionnaire_bot.ps1`** - Gestionnaire interactif pour Windows
- **`gestionnaire_bot.sh`** - Gestionnaire interactif pour Linux/Mac

### ⚙️ Scripts Utilitaires
- **`disable_old_bot.sh`** - Script pour désactiver d'anciens bots
- **`setup_systemd.sh`** - Configuration du service systemd
- **`tothemoon-tradebot.service`** - Fichier de service systemd

## 🚀 Démarrage Rapide

### Pour Windows (PowerShell)

1. **Gestionnaire interactif** (Recommandé)
   ```powershell
   .\scripts\gestionnaire_bot.ps1
   ```

2. **Déploiement complet**
   ```powershell
   .\scripts\deploy_simple.ps1
   ```

### Pour Linux/Mac (Bash)

1. **Rendre le script exécutable**
   ```bash
   chmod +x scripts/gestionnaire_bot.sh
   chmod +x scripts/full_deploy.sh
   ```

2. **Gestionnaire interactif** (Recommandé)
   ```bash
   ./scripts/gestionnaire_bot.sh
   ```

3. **Déploiement complet**
   ```bash
   ./scripts/full_deploy.sh
   ```

## 🎛️ Utilisation du Gestionnaire Interactif

Le gestionnaire interactif vous propose un menu avec toutes les options :

```
🚀 ToTheMoon Trading Bot - Gestionnaire VPS
=============================================

📊 MONITORING & STATUT:
  1. Statut du service
  2. Logs en temps réel  
  3. Logs des dernières 24h
  4. Résumé complet du statut

⚙️ GESTION DU SERVICE:
  5. Démarrer le bot
  6. Arrêter le bot
  7. Redémarrer le bot

🗄️ BASE DE DONNÉES:
  8. Voir les derniers trades
  9. Statistiques des trades
  10. Performance du jour
  11. Sauvegarder la base de données

🔄 DÉPLOIEMENT & MISE À JOUR:
  12. Déploiement complet
  13. Mise à jour rapide du code
  14. Test en mode dry-run

🚨 URGENCE:
  15. Arrêt d'urgence
  16. Fermer toutes les positions

  17. Connexion SSH directe
   0. Quitter
```

## 📊 Commandes de Monitoring Essentielles

### Vérification rapide du statut
```bash
ssh root@213.199.41.168 "systemctl status tothemoon-tradebot"
```

### Logs en temps réel
```bash
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot -f"
```

### Résumé complet
Le gestionnaire interactif option 4 vous donne un résumé complet avec :
- Statut du service
- Utilisation mémoire
- Espace disque
- Uptime
- Dernière activité

## 🗄️ Consultation de la Base de Données

### Via le gestionnaire interactif
- Option 8 : Derniers trades
- Option 9 : Statistiques par paire
- Option 10 : Performance du jour
- Option 11 : Sauvegarde automatique

### Via SSH direct
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && sqlite3 trading_bot.db"
```

Puis dans SQLite :
```sql
-- Voir les tables
.tables

-- Derniers trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- Performance par paire
SELECT symbol, COUNT(*) as trades, 
       ROUND(SUM(profit_loss), 4) as total_profit
FROM trades 
WHERE profit_loss IS NOT NULL 
GROUP BY symbol;
```

## 🔄 Mise à Jour du Code

### Mise à jour rapide (via gestionnaire)
Option 13 du gestionnaire interactif :
1. Synchronise les fichiers modifiés
2. Redémarre automatiquement le service
3. Exclut les fichiers sensibles (.env, logs, etc.)

### Mise à jour manuelle
```bash
# Synchronisation
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='.env' \
    ./ root@213.199.41.168:/opt/toTheMoon_tradebot/

# Redémarrage
ssh root@213.199.41.168 "systemctl restart tothemoon-tradebot"
```

## 🚨 Procédures d'Urgence

### Arrêt d'urgence (Option 15)
```bash
ssh root@213.199.41.168 "systemctl stop tothemoon-tradebot && pkill -f run.py"
```

### Fermeture de toutes les positions (Option 16)
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); bot.close_all_positions()'"
```

### Vérification des positions ouvertes
```bash
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); print(bot.get_open_positions())'"
```

## 📱 Notifications et Alertes

Le bot envoie automatiquement des notifications Telegram pour :
- Démarrage/Arrêt du service
- Trades exécutés
- Erreurs critiques
- Rapports de performance

## 🔐 Sécurité et Bonnes Pratiques

1. **Sauvegarde régulière** : Utilisez l'option 11 du gestionnaire
2. **Monitoring continu** : Surveillez les logs (option 2)
3. **Test avant déploiement** : Utilisez l'option 14 (dry-run)
4. **Mise à jour progressive** : Testez d'abord en local
5. **Arrêt propre** : Utilisez l'option 6 plutôt que l'arrêt d'urgence

## 🆘 Résolution de Problèmes

### Le service ne démarre pas
```bash
# Vérifiez les logs d'erreur
ssh root@213.199.41.168 "journalctl -u tothemoon-tradebot -p err"

# Vérifiez la configuration
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && source venv/bin/activate && python3 run.py --test"
```

### Erreurs de connexion API
```bash
# Vérifiez les clés API dans .env
ssh root@213.199.41.168 "cd /opt/toTheMoon_tradebot && grep -v 'API_KEY\|SECRET' .env"
```

### Problèmes de mémoire
```bash
# Vérifiez l'utilisation des ressources
ssh root@213.199.41.168 "ps aux | grep python | grep run.py"
ssh root@213.199.41.168 "free -h"
```

## 📞 Support

Pour toute question ou problème :

1. Consultez d'abord `commandes_utiles.md`
2. Utilisez l'option 4 du gestionnaire pour un diagnostic complet
3. Vérifiez les logs avec l'option 2 ou 3
4. En cas d'urgence, utilisez les options 15 ou 16

---

*Guide créé le $(date) - ToTheMoon Trading Bot v1.0*

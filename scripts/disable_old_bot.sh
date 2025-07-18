#!/bin/bash
# Script pour désactiver l'ancien bot sur le VPS

echo "🔄 Désactivation de l'ancien bot de trading..."

# Arrêt des services systemd liés au bot
echo "📋 Arrêt des services systemd..."
sudo systemctl stop trading-bot || echo "Service trading-bot non trouvé"
sudo systemctl stop scalping-bot || echo "Service scalping-bot non trouvé"
sudo systemctl stop crypto-bot || echo "Service crypto-bot non trouvé"
sudo systemctl stop binance-bot || echo "Service binance-bot non trouvé"

# Désactivation des services pour qu'ils ne redémarrent pas au boot
echo "🚫 Désactivation des services au démarrage..."
sudo systemctl disable trading-bot || echo "Service trading-bot non trouvé"
sudo systemctl disable scalping-bot || echo "Service scalping-bot non trouvé"
sudo systemctl disable crypto-bot || echo "Service crypto-bot non trouvé"
sudo systemctl disable binance-bot || echo "Service binance-bot non trouvé"

# Arrêt des processus Python liés au trading
echo "🔍 Recherche et arrêt des processus Python de trading..."
pkill -f "python.*trading" || echo "Aucun processus trading trouvé"
pkill -f "python.*scalping" || echo "Aucun processus scalping trouvé"
pkill -f "python.*bot" || echo "Aucun processus bot trouvé"
pkill -f "python.*binance" || echo "Aucun processus binance trouvé"

# Vérification des processus encore actifs
echo "🔎 Vérification des processus restants..."
echo "Processus Python actifs :"
ps aux | grep python | grep -v grep | grep -E "(trading|scalping|bot|binance)" || echo "Aucun processus trouvé"

# Nettoyage des tâches cron
echo "🧹 Nettoyage des tâches cron..."
crontab -l | grep -v -E "(trading|scalping|bot|binance)" | crontab - || echo "Pas de crontab à nettoyer"

# Affichage du statut des services
echo "📊 Statut final des services :"
systemctl is-active trading-bot scalping-bot crypto-bot binance-bot 2>/dev/null || echo "Tous les services sont arrêtés"

echo "✅ Désactivation de l'ancien bot terminée !"
echo ""
echo "📝 Actions recommandées :"
echo "   1. Vérifier qu'aucun processus de trading n'est actif"
echo "   2. Sauvegarder les logs de l'ancien bot si nécessaire"
echo "   3. Nettoyer les anciens fichiers si souhaité"
echo ""

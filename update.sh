#!/bin/bash

# Mise à jour rapide du bot - sans interruption longue
# Usage: ./update.sh

echo "⚡ MISE À JOUR RAPIDE - toTheMoon Bot"
echo "===================================="

# Variables
BOT_DIR="/home/$(whoami)/toTheMoon_tradebot"
SERVICE_NAME="toTheMoon-bot"

cd $BOT_DIR

# 1. Récupération des changements
echo "📥 Récupération des changements..."
git stash push -m "Auto-stash $(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
git pull origin main

# 2. Redémarrage rapide
echo "🔄 Redémarrage du bot..."
sudo systemctl restart $SERVICE_NAME

# 3. Vérification
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Bot redémarré avec succès!"
    echo "📊 Status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l | head -10
else
    echo "❌ Erreur de redémarrage"
    sudo journalctl -u $SERVICE_NAME --no-pager -n 10
fi

echo "📋 Logs temps réel: sudo journalctl -u $SERVICE_NAME -f"

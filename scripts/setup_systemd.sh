#!/bin/bash
# Script de configuration du service systemd pour le bot

SERVICE_NAME="tothemoon-tradebot"
BOT_DIR="/opt/toTheMoon_tradebot"

echo "⚙️ Configuration du service systemd pour le bot..."

# Copie du fichier de service
echo "📄 Installation du fichier de service..."
cp scripts/tothemoon-tradebot.service /etc/systemd/system/

# Rechargement de systemd
echo "🔄 Rechargement de systemd..."
systemctl daemon-reload

# Activation du service
echo "✅ Activation du service au démarrage..."
systemctl enable $SERVICE_NAME

# Test de la configuration
echo "🧪 Test de la configuration du service..."
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "📋 Commandes utiles pour gérer le service :"
echo "   systemctl start $SERVICE_NAME     # Démarrer"
echo "   systemctl stop $SERVICE_NAME      # Arrêter"
echo "   systemctl restart $SERVICE_NAME   # Redémarrer"
echo "   systemctl status $SERVICE_NAME    # Statut"
echo "   journalctl -u $SERVICE_NAME -f    # Logs en temps réel"
echo ""
echo "✅ Configuration systemd terminée !"
echo ""
echo "⚠️  N'oubliez pas de configurer le fichier .env avant de démarrer le service !"
echo ""

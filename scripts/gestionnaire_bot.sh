#!/bin/bash
# ToTheMoon Trading Bot - Gestionnaire VPS (Linux/Mac)

# Variables de configuration
VPS_HOST="root@213.199.41.168"
BOT_DIR="/opt/toTheMoon_tradebot"
SERVICE_NAME="tothemoon-tradebot"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function show_menu() {
    clear
    echo -e "${CYAN}🚀 ToTheMoon Trading Bot - Gestionnaire VPS${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
    echo -e "${YELLOW}📊 MONITORING & STATUT:${NC}"
    echo -e "  ${WHITE}1. Statut du service${NC}"
    echo -e "  ${WHITE}2. Logs en temps réel${NC}"
    echo -e "  ${WHITE}3. Logs des dernières 24h${NC}"
    echo -e "  ${WHITE}4. Résumé complet du statut${NC}"
    echo ""
    echo -e "${YELLOW}⚙️ GESTION DU SERVICE:${NC}"
    echo -e "  ${WHITE}5. Démarrer le bot${NC}"
    echo -e "  ${WHITE}6. Arrêter le bot${NC}"
    echo -e "  ${WHITE}7. Redémarrer le bot${NC}"
    echo ""
    echo -e "${YELLOW}🗄️ BASE DE DONNÉES:${NC}"
    echo -e "  ${WHITE}8. Voir les derniers trades${NC}"
    echo -e "  ${WHITE}9. Statistiques des trades${NC}"
    echo -e "  ${WHITE}10. Performance du jour${NC}"
    echo -e "  ${WHITE}11. Sauvegarder la base de données${NC}"
    echo ""
    echo -e "${YELLOW}🔄 DÉPLOIEMENT & MISE À JOUR:${NC}"
    echo -e "  ${WHITE}12. Déploiement complet${NC}"
    echo -e "  ${WHITE}13. Mise à jour rapide du code${NC}"
    echo -e "  ${WHITE}14. Test en mode dry-run${NC}"
    echo ""
    echo -e "${RED}🚨 URGENCE:${NC}"
    echo -e "  ${RED}15. Arrêt d'urgence${NC}"
    echo -e "  ${RED}16. Fermer toutes les positions${NC}"
    echo ""
    echo -e "  ${GREEN}17. Connexion SSH directe${NC}"
    echo -e "  ${NC}0. Quitter${NC}"
    echo ""
}

function ssh_command() {
    ssh $VPS_HOST "$1"
}

function show_service_status() {
    echo -e "${YELLOW}📊 Vérification du statut du service...${NC}"
    ssh_command "systemctl status $SERVICE_NAME"
}

function show_realtime_logs() {
    echo -e "${YELLOW}📊 Affichage des logs en temps réel (Ctrl+C pour arrêter)...${NC}"
    ssh_command "journalctl -u $SERVICE_NAME -f"
}

function show_recent_logs() {
    echo -e "${YELLOW}📊 Logs des dernières 24h...${NC}"
    ssh_command "journalctl -u $SERVICE_NAME --since '24 hours ago'"
}

function show_complete_status() {
    echo -e "${YELLOW}📊 Résumé complet du statut...${NC}"
    ssh_command "
echo '🔍 STATUT DU BOT TOTHEMOON'
echo '========================='
echo '📊 Service:' \$(systemctl is-active $SERVICE_NAME)
echo '💾 Mémoire:' \$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -p \$(pgrep -f run.py) | tail -n +2)
echo '📁 Espace disque:' \$(df -h $BOT_DIR | tail -1 | awk '{print \$4\" disponible\"}')
echo '🕐 Uptime:' \$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp --value)
echo '📈 Dernière activité:'
journalctl -u $SERVICE_NAME -n 5 --no-pager
"
}

function start_bot() {
    echo -e "${GREEN}🚀 Démarrage du bot...${NC}"
    ssh_command "systemctl start $SERVICE_NAME"
    echo -e "${GREEN}✅ Commande de démarrage envoyée${NC}"
}

function stop_bot() {
    echo -e "${RED}⏹️ Arrêt du bot...${NC}"
    ssh_command "systemctl stop $SERVICE_NAME"
    echo -e "${GREEN}✅ Commande d'arrêt envoyée${NC}"
}

function restart_bot() {
    echo -e "${YELLOW}🔄 Redémarrage du bot...${NC}"
    ssh_command "systemctl restart $SERVICE_NAME"
    echo -e "${GREEN}✅ Commande de redémarrage envoyée${NC}"
}

function show_recent_trades() {
    echo -e "${YELLOW}📈 Derniers trades...${NC}"
    ssh_command "cd $BOT_DIR && sqlite3 trading_bot.db 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;'"
}

function show_trade_stats() {
    echo -e "${YELLOW}📊 Statistiques des trades...${NC}"
    ssh_command "cd $BOT_DIR && sqlite3 trading_bot.db '
SELECT symbol, COUNT(*) as nb_trades, 
       ROUND(AVG(profit_loss), 4) as avg_profit, 
       ROUND(SUM(profit_loss), 4) as total_profit
FROM trades 
WHERE profit_loss IS NOT NULL 
GROUP BY symbol;'"
}

function show_today_performance() {
    echo -e "${YELLOW}📅 Performance du jour...${NC}"
    ssh_command "cd $BOT_DIR && sqlite3 trading_bot.db '
SELECT symbol, side, quantity, price, profit_loss, timestamp 
FROM trades 
WHERE DATE(timestamp) = DATE(\"now\") 
ORDER BY timestamp DESC;'"
}

function backup_database() {
    echo -e "${YELLOW}💾 Sauvegarde de la base de données...${NC}"
    
    # Créer le dossier backup s'il n'existe pas
    mkdir -p ./backup
    
    BACKUP_NAME="trading_bot_backup_$(date +%Y%m%d_%H%M%S).db"
    ssh_command "cd $BOT_DIR && cp trading_bot.db $BACKUP_NAME"
    
    # Téléchargement local
    echo -e "${YELLOW}📥 Téléchargement de la sauvegarde...${NC}"
    scp "${VPS_HOST}:${BOT_DIR}/${BACKUP_NAME}" "./backup/"
    echo -e "${GREEN}✅ Sauvegarde créée : ./backup/$BACKUP_NAME${NC}"
}

function deploy_complete() {
    echo -e "${CYAN}🚀 Déploiement complet...${NC}"
    ./scripts/full_deploy.sh
}

function update_code() {
    echo -e "${YELLOW}🔄 Mise à jour rapide du code...${NC}"
    
    # Copie des fichiers
    rsync -avz --progress \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.vscode' \
        --exclude='logs/' \
        --exclude='data/' \
        --exclude='.env' \
        ./ ${VPS_HOST}:${BOT_DIR}/
    
    # Redémarrage du service
    echo -e "${YELLOW}🔄 Redémarrage du service...${NC}"
    ssh_command "systemctl restart $SERVICE_NAME"
    echo -e "${GREEN}✅ Mise à jour terminée${NC}"
}

function test_dry_run() {
    echo -e "${CYAN}🧪 Test en mode dry-run...${NC}"
    ssh_command "cd $BOT_DIR && source venv/bin/activate && python3 run.py --test"
}

function emergency_stop() {
    echo -e "${RED}🚨 ARRÊT D'URGENCE...${NC}"
    ssh_command "systemctl stop $SERVICE_NAME && pkill -f run.py"
    echo -e "${RED}⚠️ Bot arrêté en urgence${NC}"
}

function close_all_positions() {
    echo -e "${RED}🚨 Fermeture de toutes les positions...${NC}"
    ssh_command "cd $BOT_DIR && source venv/bin/activate && python3 -c 'from main import ScalpingBot; bot = ScalpingBot(); bot.close_all_positions()'"
}

function connect_ssh() {
    echo -e "${GREEN}🔗 Connexion SSH directe...${NC}"
    ssh $VPS_HOST
}

function pause_for_input() {
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

# Boucle principale
while true; do
    show_menu
    read -p "Choisissez une option (0-17): " choice
    
    case $choice in
        1) show_service_status; pause_for_input ;;
        2) show_realtime_logs ;;
        3) show_recent_logs; pause_for_input ;;
        4) show_complete_status; pause_for_input ;;
        5) start_bot; pause_for_input ;;
        6) stop_bot; pause_for_input ;;
        7) restart_bot; pause_for_input ;;
        8) show_recent_trades; pause_for_input ;;
        9) show_trade_stats; pause_for_input ;;
        10) show_today_performance; pause_for_input ;;
        11) backup_database; pause_for_input ;;
        12) deploy_complete; pause_for_input ;;
        13) update_code; pause_for_input ;;
        14) test_dry_run; pause_for_input ;;
        15) emergency_stop; pause_for_input ;;
        16) close_all_positions; pause_for_input ;;
        17) connect_ssh ;;
        0) echo -e "${GREEN}Au revoir ! 👋${NC}"; exit 0 ;;
        *) echo -e "${RED}Option invalide !${NC}"; pause_for_input ;;
    esac
done

# Script de lancement du bot de trading
import asyncio
import os
import sys
from pathlib import Path

# Ajout du répertoire racine au path
sys.path.append(str(Path(__file__).parent))

from config import API_CONFIG
from main import ScalpingBot
from utils.logger import setup_colored_logger


def main():
    """Point d'entrée principal"""
    
    # Configuration du logger
    logger = setup_colored_logger("Launcher")
    
    # Vérification des variables d'environnement
    logger.info("🔍 Vérification de la configuration...")
    
    try:
        API_CONFIG.validate()
        logger.info("✅ Configuration validée")
    except ValueError as e:
        logger.error(f"❌ Erreur de configuration: {e}")
        logger.error("💡 Vérifiez votre fichier .env et les clés API")
        return 1
    
    # Création et lancement du bot
    bot = ScalpingBot()
    
    try:
        logger.info("🚀 Lancement du bot de trading scalping...")
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("\\n🛑 Arrêt du bot demandé par l'utilisateur")
        asyncio.run(bot.stop())
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

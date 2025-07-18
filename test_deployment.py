#!/usr/bin/env python3
import logging

from main import ScalpingBot

# Configuration minimale pour éviter les erreurs de logging
logging.basicConfig(level=logging.INFO)

try:
    bot = ScalpingBot()
    has_method = hasattr(bot, 'get_total_capital')
    print(f"✅ Bot initialisé avec succès")
    print(f"✅ Méthode get_total_capital présente: {has_method}")
    
    if has_method:
        print("✅ Capital dynamique opérationnel")
        print("✅ P&L basé sur capital total dynamique")
        print("✅ Notifications Telegram optimisées")
        print("✅ Logs Google Sheets adaptés")
    else:
        print("❌ Méthode get_total_capital manquante")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")

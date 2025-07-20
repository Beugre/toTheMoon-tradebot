#!/usr/bin/env python3
"""
🧪 TEST DES NOTIFICATIONS HORAIRES DE TRADING
Teste le système de notifications Telegram pour les horaires
"""

import asyncio
import os
import sys
from datetime import datetime

import pytz

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APIConfig, TradingConfig
from utils.telegram_notifier import TelegramNotifier
from utils.trading_hours_notifier import TradingHoursNotifier


async def test_notifications_horaires():
    """Test complet du système de notifications d'horaires"""
    print("🧪 DÉBUT DU TEST DES NOTIFICATIONS HORAIRES")
    print("=" * 60)
    
    # Configuration
    config = TradingConfig()
    api_config = APIConfig()
    
    # Validation des clés API
    if not api_config.TELEGRAM_BOT_TOKEN or not api_config.TELEGRAM_CHAT_ID:
        print("❌ Clés Telegram manquantes dans .env")
        print("📋 Vérifiez TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID")
        return
    
    # Heure française actuelle
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    print(f"🕐 Heure actuelle: {now.strftime('%H:%M:%S')} (France)")
    print(f"📅 Date: {now.strftime('%A %d %B %Y')}")
    print()
    
    # Configuration horaires
    print("⚙️ CONFIGURATION HORAIRES:")
    print(f"   🕘 Horaires trading: {config.TRADING_START_HOUR}h-{config.TRADING_END_HOUR}h")
    print(f"   🍽️ Pause déjeuner: {config.LUNCH_BREAK_START}h-{config.LUNCH_BREAK_END}h")
    print(f"   🌴 Week-end activé: {'✅' if config.WEEKEND_TRADING_ENABLED else '❌'}")
    if config.WEEKEND_TRADING_ENABLED:
        print(f"   🏖️ Horaires WE: {config.WEEKEND_START_HOUR}h-{config.WEEKEND_END_HOUR}h")
    print()
    
    # Initialisation des notificateurs
    print("🚀 INITIALISATION TELEGRAM...")
    telegram_notifier = TelegramNotifier(
        bot_token=api_config.TELEGRAM_BOT_TOKEN,
        chat_id=api_config.TELEGRAM_CHAT_ID,
        trading_config=config
    )
    
    hours_notifier = TradingHoursNotifier(telegram_notifier, config)
    print("✅ Notificateurs initialisés")
    print()
    
    # Menu de test
    while True:
        print("📋 MENU DE TEST:")
        print("1. 🌅 Test notification début de trading (9h)")
        print("2. 🍽️ Test notification lunch time (12h)")
        print("3. ⚡ Test notification retour lunch (14h)")
        print("4. 🇺🇸 Test notification power hour (21h)")
        print("5. 🌙 Test notification fin de trading (23h)")
        print("6. 🌴 Test notification mode week-end")
        print("7. ⚠️ Test notification fermeture proche (5min)")
        print("8. 📊 Test notification haute volatilité")
        print("9. 😴 Test notification faible volatilité")
        print("0. ❌ Quitter")
        print()
        
        try:
            choice = input("Votre choix (0-9): ").strip()
            
            if choice == "0":
                print("👋 Test terminé !")
                break
                
            elif choice == "1":
                print("🌅 Envoi notification début de trading...")
                await hours_notifier.send_trading_start_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "2":
                print("🍽️ Envoi notification lunch time...")
                await hours_notifier.send_lunch_time_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "3":
                print("⚡ Envoi notification retour lunch...")
                await hours_notifier.send_back_from_lunch_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "4":
                print("🇺🇸 Envoi notification power hour...")
                await hours_notifier.send_power_hour_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "5":
                print("🌙 Envoi notification fin de trading...")
                await hours_notifier.send_trading_end_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "6":
                print("🌴 Envoi notification mode week-end...")
                await hours_notifier.send_weekend_mode_notification()
                print("✅ Notification envoyée !")
                
            elif choice == "7":
                print("⚠️ Envoi notification fermeture proche...")
                await hours_notifier.send_market_closure_warning(5)
                print("✅ Notification envoyée !")
                
            elif choice == "8":
                print("📊 Envoi notification haute volatilité...")
                await hours_notifier.send_volatility_alert("HIGH")
                print("✅ Notification envoyée !")
                
            elif choice == "9":
                print("😴 Envoi notification faible volatilité...")
                await hours_notifier.send_volatility_alert("LOW")
                print("✅ Notification envoyée !")
                
            else:
                print("❌ Choix invalide, essayez encore")
            
            print()
            input("Appuyez sur Entrée pour continuer...")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Test interrompu par l'utilisateur")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            print()

async def test_verification_automatique():
    """Test de la vérification automatique des horaires"""
    print("\n🔄 TEST VÉRIFICATION AUTOMATIQUE")
    print("=" * 40)
    
    config = TradingConfig()
    api_config = APIConfig()
    
    telegram_notifier = TelegramNotifier(
        bot_token=api_config.TELEGRAM_BOT_TOKEN,
        chat_id=api_config.TELEGRAM_CHAT_ID,
        trading_config=config
    )
    
    hours_notifier = TradingHoursNotifier(telegram_notifier, config)
    
    print("🔍 Simulation de 10 vérifications automatiques...")
    for i in range(10):
        print(f"   Vérification {i+1}/10...")
        await hours_notifier.check_and_notify_schedule_changes()
        await asyncio.sleep(1)  # Pause de 1 seconde entre vérifications
    
    print("✅ Test de vérification automatique terminé")


async def main():
    """Fonction principale de test"""
    print("🎯 SYSTÈME DE NOTIFICATIONS HORAIRES - TESTS")
    print("=" * 60)
    
    try:
        # Test des notifications manuelles
        await test_notifications_horaires()
        
        # Test de vérification automatique
        await test_verification_automatique()
        
    except Exception as e:
        print(f"❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

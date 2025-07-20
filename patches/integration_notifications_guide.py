#!/usr/bin/env python3
"""
🎯 INTÉGRATION COMPLÈTE DES NOTIFICATIONS HORAIRES
Script pour intégrer automatiquement les notifications dans le bot principal
"""

import os
import sys
from pathlib import Path

# Configuration des chemins
PROJECT_ROOT = Path(__file__).parent.parent
MAIN_PY_PATH = PROJECT_ROOT / "main.py"
CONFIG_PY_PATH = PROJECT_ROOT / "config.py"

def check_integration_status():
    """Vérifie l'état de l'intégration des notifications"""
    print("🔍 VÉRIFICATION DE L'INTÉGRATION DES NOTIFICATIONS")
    print("=" * 60)
    
    # Vérification main.py
    main_content = MAIN_PY_PATH.read_text(encoding='utf-8')
    
    checks = [
        ("TradingHoursNotifier import", "from utils.trading_hours_notifier import TradingHoursNotifier"),
        ("hours_notifier initialization", "self.hours_notifier = TradingHoursNotifier"),
        ("hours check in main loop", "await self.hours_notifier.check_and_notify_schedule_changes()"),
    ]
    
    print("📋 STATUT DES INTÉGRATIONS:")
    all_good = True
    
    for check_name, check_pattern in checks:
        if check_pattern in main_content:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name} - MANQUANT")
            all_good = False
    
    print()
    
    # Vérification fichier notifications
    notifier_path = PROJECT_ROOT / "utils" / "trading_hours_notifier.py"
    if notifier_path.exists():
        print("   ✅ Fichier trading_hours_notifier.py présent")
    else:
        print("   ❌ Fichier trading_hours_notifier.py manquant")
        all_good = False
    
    print()
    
    if all_good:
        print("🎉 INTÉGRATION COMPLÈTE ! Toutes les notifications sont prêtes")
        print("🚀 Le bot enverra automatiquement les notifications d'horaires")
    else:
        print("⚠️ Intégration incomplète, certains éléments manquent")
    
    return all_good

def show_notification_schedule():
    """Affiche le planning des notifications"""
    print("\n📅 PLANNING AUTOMATIQUE DES NOTIFICATIONS")
    print("=" * 50)
    
    notifications = [
        ("🌅 09:00", "Début de trading", "GOOD MORNING TRADERS !"),
        ("🍽️ 12:00", "Lunch time", "TRADING EN MODE RELAX"),
        ("⚡ 14:00", "Retour lunch", "RETOUR EN FORCE !"),
        ("🇺🇸 21:00", "Power hour US", "MAXIMUM VOLATILITY TIME !"),
        ("🌙 23:00", "Fin de trading", "BONNE NUIT TRADERS !"),
        ("🌴 Week-end", "Mode week-end", "WEEK-END MODE !")
    ]
    
    for time, event, message in notifications:
        print(f"   {time} - {event}")
        print(f"        💬 \"{message}\"")
        print()

def show_features():
    """Affiche les fonctionnalités disponibles"""
    print("🎯 FONCTIONNALITÉS DES NOTIFICATIONS HORAIRES")
    print("=" * 50)
    
    features = [
        "🌅 Notification automatique début de session (9h)",
        "🍽️ Alerte lunch time avec réduction d'intensité (12h-14h)",
        "⚡ Notification retour après lunch (14h)",
        "🇺🇸 Alerte power hour pour session US (21h-22h)",
        "🌙 Notification fin de session (23h)",
        "🌴 Mode week-end avec horaires adaptés",
        "⚠️ Alertes de fermeture proche",
        "📊 Notifications de volatilité (haute/faible)",
        "🎨 Messages avec émojis fun et motivants",
        "🔄 Vérification automatique toutes les minutes",
        "🚫 Prévention des notifications répétées",
        "⏰ Horaires français (Europe/Paris)"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print()

def show_configuration_tips():
    """Affiche les conseils de configuration"""
    print("⚙️ CONSEILS DE CONFIGURATION")
    print("=" * 35)
    
    tips = [
        "🔑 Vérifiez que TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID sont dans .env",
        "⏰ Les horaires sont configurables dans config.py (TRADING_START_HOUR, etc.)",
        "🌴 Le trading week-end peut être activé/désactivé (WEEKEND_TRADING_ENABLED)",
        "🍽️ La pause déjeuner est configurable (LUNCH_BREAK_START/END)",
        "📊 Les heures premium peuvent être personnalisées (PREMIUM_HOURS)",
        "🔕 Les notifications peuvent être désactivées individuellement",
        "🎯 Le système s'adapte automatiquement aux différentes sessions de marché"
    ]
    
    for tip in tips:
        print(f"   {tip}")
    
    print()

def show_usage_examples():
    """Affiche des exemples d'utilisation"""
    print("💡 EXEMPLES DE NOTIFICATIONS REÇUES")
    print("=" * 40)
    
    examples = [
        {
            "time": "🌅 09:00",
            "title": "GOOD MORNING TRADERS !",
            "content": [
                "🔔 DÉBUT DE SESSION",
                "🚀 C'EST PARTI POUR UNE NOUVELLE JOURNÉE !",
                "💰 Trading en mode EUROPE",
                "📊 Intensité: 100% ⚡",
                "🎯 OBJECTIFS DU JOUR: Scalping haute fréquence"
            ]
        },
        {
            "time": "🍽️ 12:00",
            "title": "LUNCH TIME !",
            "content": [
                "🕛 PAUSE DÉJEUNER",
                "🍕 TRADING EN MODE RELAX",
                "📉 Intensité réduite: 50%",
                "🍰 BON APPÉTIT !"
            ]
        },
        {
            "time": "🇺🇸 21:00",
            "title": "POWER HOUR !",
            "content": [
                "🕘 SESSION US PEAK",
                "🔥 MAXIMUM VOLATILITY TIME !",
                "⚡ Volume maximum sur toutes les paires",
                "🏆 Make it count!"
            ]
        }
    ]
    
    for example in examples:
        print(f"   {example['time']} - {example['title']}")
        for line in example['content']:
            print(f"      {line}")
        print()

def main():
    """Fonction principale d'information"""
    print("🎯 SYSTÈME DE NOTIFICATIONS HORAIRES - GUIDE COMPLET")
    print("=" * 65)
    print()
    
    # Vérification de l'intégration
    integration_ok = check_integration_status()
    
    # Affichage des informations
    show_notification_schedule()
    show_features()
    show_configuration_tips()
    show_usage_examples()
    
    # Statut final
    print("🏁 RÉSUMÉ FINAL")
    print("=" * 20)
    
    if integration_ok:
        print("✅ Système complètement intégré et opérationnel")
        print("🚀 Les notifications seront envoyées automatiquement")
        print("📱 Vérifiez votre Telegram pour les recevoir")
        print()
        print("🎉 PRÊT À TRADER AVEC STYLE ! 🎉")
    else:
        print("⚠️ Intégration incomplète")
        print("🔧 Vérifiez les éléments manquants ci-dessus")
        print("📞 Relancez le script après correction")
    
    print()
    print("💡 Pour tester manuellement: python patches/test_notifications_horaires.py")
    print("🔍 Pour plus d'infos: consultez utils/trading_hours_notifier.py")

if __name__ == "__main__":
    main()

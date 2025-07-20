#!/usr/bin/env python3
"""
🧪 TEST DU SYSTÈME D'HORAIRES DE TRADING
Validation des fonctions de gestion des heures optimales
"""

from datetime import datetime

import pytz

from config import TradingConfig
from trading_hours import (get_current_session_info, get_current_trading_session,
                           get_hours_status_message, get_trading_intensity, is_trading_hours_active)


def test_trading_hours_system():
    """Test complet du système d'horaires"""
    print("🕐 === TEST SYSTÈME HORAIRES DE TRADING ===\n")
    
    config = TradingConfig()
    
    # 1. Status actuel
    print("📊 STATUS ACTUEL:")
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    
    print(f"   ⏰ Heure actuelle: {now.strftime('%H:%M:%S')} (Paris)")
    print(f"   📅 Jour: {now.strftime('%A %d/%m/%Y')}")
    print(f"   🎯 Horaires configurés: {config.TRADING_START_HOUR}h-{config.TRADING_END_HOUR}h")
    print(f"   ⚙️  Système activé: {config.TRADING_HOURS_ENABLED}")
    
    # 2. Fonctions principales
    is_active = is_trading_hours_active(config)
    intensity = get_trading_intensity(config)
    session = get_current_trading_session()
    status_msg = get_hours_status_message(config)
    session_info = get_current_session_info()
    
    print(f"\n🔍 ANALYSE:")
    print(f"   🚀 Trading actif: {'✅ OUI' if is_active else '❌ NON'}")
    print(f"   ⚡ Intensité: {intensity*100:.0f}%")
    print(f"   🌍 Session: {session}")
    print(f"   📋 Status: {status_msg}")
    
    # 3. Détails session
    print(f"\n📈 DÉTAILS SESSION:")
    for key, value in session_info.items():
        print(f"   {key}: {value}")
    
    # 4. Recommandations position sizing
    print(f"\n💰 IMPACT POSITION SIZING:")
    base_size = 1000  # 1000 USDC de base
    adjusted_size = base_size * intensity
    
    print(f"   📊 Taille de base: {base_size} USDC")
    print(f"   🎯 Taille ajustée: {adjusted_size:.0f} USDC")
    print(f"   📉 Réduction: {((base_size - adjusted_size) / base_size * 100):.1f}%")
    
    # 5. Heures premium
    print(f"\n🔥 HEURES PREMIUM:")
    for start, end in config.PREMIUM_HOURS:
        status = "🟢 ACTIF" if start <= now.hour < end else "⚪ Inactif"
        print(f"   {start}h-{end}h: {status}")
    
    # 6. Pause déjeuner
    print(f"\n🍽️  PAUSE DÉJEUNER:")
    lunch_active = config.LUNCH_BREAK_START <= now.hour < config.LUNCH_BREAK_END
    lunch_status = "🟡 ACTIF" if lunch_active else "⚪ Inactif"
    print(f"   {config.LUNCH_BREAK_START}h-{config.LUNCH_BREAK_END}h: {lunch_status}")
    print(f"   Facteur réduction: {config.LUNCH_REDUCTION_FACTOR*100:.0f}%")
    
    # 7. Week-end
    is_weekend = now.weekday() >= 5
    print(f"\n🎯 WEEK-END:")
    print(f"   Week-end: {'✅ OUI' if is_weekend else '❌ NON'}")
    print(f"   Trading WE autorisé: {'✅ OUI' if config.WEEKEND_TRADING_ENABLED else '❌ NON'}")
    if config.WEEKEND_TRADING_ENABLED:
        print(f"   Horaires WE: {config.WEEKEND_START_HOUR}h-{config.WEEKEND_END_HOUR}h")
        print(f"   Facteur WE: {config.WEEKEND_REDUCTION_FACTOR*100:.0f}%")
    
    # 8. Économies estimées
    print(f"\n💎 ÉCONOMIES POTENTIELLES:")
    if not is_active:
        print("   🛑 Trading suspendu = 100% d'économie sur les frais")
    elif intensity < 1.0:
        reduction = (1.0 - intensity) * 100
        print(f"   📉 Réduction d'intensité = {reduction:.0f}% d'économie sur les frais")
        print("   🎯 Évite les signaux de faible qualité des heures creuses")
    else:
        print("   🔥 Intensité maximale = Conditions optimales de trading")
    
    print(f"\n✅ Test terminé - Système d'horaires opérationnel!")

if __name__ == "__main__":
    test_trading_hours_system()

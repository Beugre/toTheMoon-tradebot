#!/usr/bin/env python3
"""
🕐 MODULE GESTION HORAIRES DE TRADING
Fonctions pour optimiser les heures de trading
"""

from datetime import datetime

import pytz

from config import TradingConfig


def is_trading_hours_active(config: TradingConfig) -> bool:
    """Vérifie si on est dans les horaires de trading autorisés"""
    if not config.TRADING_HOURS_ENABLED:
        return True  # Si désactivé, toujours actif
    
    # Heure française/européenne
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    current_hour = now.hour
    current_day = now.weekday()  # 0=Lundi, 6=Dimanche
    
    # Vérification week-end
    if current_day >= 5:  # Samedi (5) ou Dimanche (6)
        if not config.WEEKEND_TRADING_ENABLED:
            return False
        start_hour = config.WEEKEND_START_HOUR
        end_hour = config.WEEKEND_END_HOUR
    else:  # Semaine
        start_hour = config.TRADING_START_HOUR
        end_hour = config.TRADING_END_HOUR
    
    # Vérification horaires
    return start_hour <= current_hour < end_hour

def get_trading_intensity(config: TradingConfig) -> float:
    """Retourne l'intensité de trading selon l'heure (0.0 à 1.0)"""
    if not is_trading_hours_active(config):
        return 0.0  # Hors horaires = pas de trading
    
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    current_hour = now.hour
    current_day = now.weekday()
    
    # Week-end : intensité réduite
    if current_day >= 5:
        return config.WEEKEND_REDUCTION_FACTOR
    
    # Horaires premium (intensité maximale)
    for start, end in config.PREMIUM_HOURS:
        if start <= current_hour < end:
            return 1.0
    
    # Pause déjeuner (intensité réduite)
    if config.LUNCH_BREAK_START <= current_hour < config.LUNCH_BREAK_END:
        return config.LUNCH_REDUCTION_FACTOR
    
    # Horaires normaux (intensité standard)
    return 0.7

def get_current_trading_session() -> str:
    """Retourne la session de trading actuelle"""
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    current_hour = now.hour
    
    if 2 <= current_hour < 11:
        return "ASIE"
    elif 9 <= current_hour < 18:
        if 15 <= current_hour < 18:
            return "EU-US_OVERLAP"  # Golden hours
        return "EUROPE"
    elif 15 <= current_hour < 24:
        return "US"
    else:
        return "TRANSITION"

def should_reduce_position_size(config: TradingConfig) -> bool:
    """Indique si la taille de position doit être réduite"""
    intensity = get_trading_intensity(config)
    return intensity < 0.7  # Réduire si intensité < 70%

def get_hours_status_message(config: TradingConfig) -> str:
    """Retourne un message de status des horaires"""
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    current_hour = now.hour
    
    is_active = is_trading_hours_active(config)
    intensity = get_trading_intensity(config)
    session = get_current_trading_session()
    
    if not is_active:
        return f"🌙 HORS HORAIRES ({current_hour:02d}:xx) - Trading suspendu"
    
    status_emoji = "🔥" if intensity >= 1.0 else "⚡" if intensity >= 0.7 else "🟡"
    
    return f"{status_emoji} {session} ({current_hour:02d}:xx) - Intensité: {intensity*100:.0f}%"

def get_current_session_info() -> dict:
    """Retourne les informations détaillées de la session actuelle"""
    tz_fr = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_fr)
    current_hour = now.hour
    
    session = get_current_trading_session()
    is_active = is_trading_hours_active(TradingConfig())
    intensity = get_trading_intensity(TradingConfig())
    
    # Calcul de la prochaine ouverture
    if is_active:
        next_open = "En cours"
    else:
        # Si hors horaires, prochaine ouverture à 9h
        if current_hour < 9:
            next_open = f"{9 - current_hour}h"
        else:
            next_open = f"{24 - current_hour + 9}h (demain)"
    
    return {
        'session': session,
        'is_active': is_active,
        'intensity': intensity,
        'current_hour': current_hour,
        'next_open': next_open
    }

if __name__ == "__main__":
    # Test des fonctions
    config = TradingConfig()
    
    print("🕐 TEST GESTION HORAIRES:")
    print(f"   Status: {get_hours_status_message(config)}")
    print(f"   Trading actif: {is_trading_hours_active(config)}")
    print(f"   Intensité: {get_trading_intensity(config)*100:.0f}%")
    print(f"   Session: {get_current_trading_session()}")
    print(f"   Réduire position: {should_reduce_position_size(config)}")

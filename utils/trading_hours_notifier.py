#!/usr/bin/env python3
"""
🕐 NOTIFICATEUR HORAIRES DE TRADING
Notifications Telegram amusantes pour les changements d'horaires
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import pytz

from config import TradingConfig
from trading_hours import (get_current_trading_session, get_trading_intensity,
                           is_trading_hours_active)
from utils.telegram_notifier import TelegramNotifier


class TradingHoursNotifier:
    """Gestionnaire des notifications d'horaires de trading avec plein d'émojis fun ! 🎉"""
    
    def __init__(self, telegram_notifier: TelegramNotifier, config: TradingConfig):
        self.telegram = telegram_notifier
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Suivi des états pour éviter les notifications répétées
        self.last_notification_hour = None
        self.last_notification_state = None
        self.session_start_notified = False
        self.session_end_notified = False
        self.last_volatility_alert = None  # Dernier niveau de volatilité notifié
        
    async def check_and_notify_schedule_changes(self):
        """Vérifie et notifie les changements d'horaires de trading"""
        if not self.config.TRADING_HOURS_ENABLED:
            return
            
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        current_hour = now.hour
        current_minute = now.minute
        
        is_active = is_trading_hours_active(self.config)
        
        # Notification de début de session (9h00)
        if (current_hour == self.config.TRADING_START_HOUR and 
            current_minute <= 5 and 
            not self.session_start_notified):
            await self.send_trading_start_notification()
            self.session_start_notified = True
            
        # Notification de fin de session (23h00)
        elif (current_hour == self.config.TRADING_END_HOUR and 
              current_minute <= 5 and 
              not self.session_end_notified):
            await self.send_trading_end_notification()
            self.session_end_notified = True
            
        # Notification lunch time (12h-14h)
        elif current_hour == 12 and current_minute <= 5 and self.last_notification_hour != 12:
            await self.send_lunch_time_notification()
            self.last_notification_hour = 12
            
        # Notification retour lunch (14h)
        elif current_hour == 14 and current_minute <= 5 and self.last_notification_hour != 14:
            await self.send_back_from_lunch_notification()
            self.last_notification_hour = 14
            
        # Notification power hour (21h-22h pour session US)
        elif current_hour == 21 and current_minute <= 5 and self.last_notification_hour != 21:
            await self.send_power_hour_notification()
            self.last_notification_hour = 21
            
        # Reset des flags quotidiens à minuit
        if current_hour == 0 and current_minute <= 5:
            self.session_start_notified = False
            self.session_end_notified = False
            self.last_notification_hour = None

    async def send_trading_start_notification(self):
        """🌅 Notification de début de trading (9h00)"""
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        
        session_info = get_current_trading_session()
        intensity = get_trading_intensity(self.config)
        
        message = f"""
🌅 **GOOD MORNING TRADERS !** 🌅

🔔 **{now.strftime('%H:%M')} - DÉBUT DE SESSION** 🔔

🚀 **C'EST PARTI POUR UNE NOUVELLE JOURNÉE !** 🚀
💰 Trading en mode **{session_info}**
📊 Intensité: **{intensity:.0%}** ⚡

🎯 **OBJECTIFS DU JOUR:**
• 📈 Scalping haute fréquence
• 💎 Focus sur les paires USDC liquides
• 🛡️ Stop Loss à {self.config.STOP_LOSS_PERCENT}%
• 🎯 Take Profit à {self.config.TAKE_PROFIT_PERCENT}%

⏰ **PLANNING:**
• 🌅 **09h-12h**: Session EU matinale
• 🍽️ **12h-14h**: Lunch time (trading réduit)
• ⚡ **14h-18h**: Session EU après-midi
• 🌍 **18h-21h**: Transition EU→US
• 🇺🇸 **21h-23h**: Power Hour US

**LET'S MAKE SOME MONEY !** 💸💸💸

*{now.strftime('%A %d %B %Y')}* 📅
"""
        
        await self.telegram.send_message(message)
        self.logger.info("🌅 Notification début de trading envoyée")

    async def send_trading_end_notification(self):
        """🌙 Notification de fin de trading (23h00)"""
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        
        message = f"""
🌙 **BONNE NUIT TRADERS !** 🌙

🔕 **{now.strftime('%H:%M')} - FIN DE SESSION** 🔕

😴 **TRADING SUSPENDU JUSQU'À 9H** 😴

📊 **BILAN DE LA JOURNÉE:**
• ⏰ Session terminée après 14h de trading
• 🎯 Toutes les positions fermées
• 💤 Bot en veille jusqu'à demain 9h

🛏️ **REPOS BIEN MÉRITÉ !**
• 💡 Analyse des performances en cours
• 🔄 Préparation de demain
• 📈 Optimisation des stratégies

**À DEMAIN POUR DE NOUVEAUX PROFITS !** 🚀

🌟 **Sweet dreams & profitable tomorrows!** 🌟

*Prochaine session: {(now + timedelta(days=1)).strftime('%A %d %B')} à 09h00* ⏰
"""
        
        await self.telegram.send_message(message)
        self.logger.info("🌙 Notification fin de trading envoyée")

    async def send_lunch_time_notification(self):
        """🍽️ Notification lunch time (12h-14h)"""
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        
        reduced_intensity = get_trading_intensity(self.config) * 0.6  # Réduction lunch
        
        message = f"""
🍽️ **LUNCH TIME !** 🍽️

🕛 **{now.strftime('%H:%M')} - PAUSE DÉJEUNER** 🕛

🍕 **TRADING EN MODE RELAX** 🍕
• 📉 Intensité réduite: **{reduced_intensity:.0%}** (au lieu de 100%)
• 🧘 Volatilité généralement plus faible
• 🍔 Markets européens au ralenti

⚠️ **PARAMÈTRES AJUSTÉS:**
• 🎯 Seuils plus sélectifs
• ⏱️ Timeouts plus courts
• 🔒 Positions plus prudentes

🍰 **BON APPÉTIT !** 🍰
*Trading reprend à pleine intensité à 14h* ⚡

🍷 **Enjoy your meal!** 🍷
"""
        
        await self.telegram.send_message(message)
        self.logger.info("🍽️ Notification lunch time envoyée")

    async def send_back_from_lunch_notification(self):
        """⚡ Notification retour de lunch (14h)"""
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        
        message = f"""
⚡ **RETOUR EN FORCE !** ⚡

🕐 **{now.strftime('%H:%M')} - SESSION APRÈS-MIDI** 🕐

🔥 **LUNCH TIME IS OVER !** 🔥
• 📈 Intensité maximale: **100%** 🚀
• ⚡ Volatilité en hausse
• 💪 Markets européens réactivés

🎯 **OBJECTIFS APRÈS-MIDI:**
• 🏃 Profiter du regain d'activité
• 📊 Exploiter les mouvements EU
• 🌍 Préparer la transition vers les US

⏰ **PROCHAINES ÉTAPES:**
• **14h-18h**: Session EU productive
• **18h-21h**: Transition EU→US
• **21h-23h**: Power Hour finale

**BACK TO BUSINESS !** 💼💰

🚀 **Let's scalp some profits!** 🚀
"""
        
        await self.telegram.send_message(message)
        self.logger.info("⚡ Notification retour de lunch envoyée")

    async def send_power_hour_notification(self):
        """🇺🇸 Notification power hour US (21h-22h)"""
        tz_fr = pytz.timezone('Europe/Paris')
        now = datetime.now(tz_fr)
        
        message = f"""
🇺🇸 **POWER HOUR !** 🇺🇸

🕘 **{now.strftime('%H:%M')} - SESSION US PEAK** 🕘

🔥 **MAXIMUM VOLATILITY TIME !** 🔥
• 🚀 Markets US à pleine puissance
• ⚡ Volume maximum sur toutes les paires
• 💎 Opportunités premium disponibles

📊 **CONDITIONS OPTIMALES:**
• 🌊 Liquidité maximum
• 📈 Spreads minimum
• ⚡ Signaux de qualité supérieure

🎯 **STRATÉGIE POWER HOUR:**
• 💰 Positions plus agressives possibles
• 🎯 Take profits plus rapides
• 🔄 Rotation active des positions

⏰ **DERNIÈRE LIGNE DROITE !**
*Plus que 2h avant la fermeture à 23h* 

**THIS IS THE MOMENT !** 💪💸

🏆 **Make it count!** 🏆
"""
        
        await self.telegram.send_message(message)
        self.logger.info("🇺🇸 Notification power hour envoyée")

    async def send_weekend_mode_notification(self):
        """🌴 Notification mode week-end"""
        if not self.config.WEEKEND_TRADING_ENABLED:
            message = f"""
🌴 **WEEK-END MODE !** 🌴

🏖️ **REPOS TOTAL** 🏖️
• 😴 Trading complètement suspendu
• 🌊 Markets fermés
• 🍹 Time to relax!

📅 **REPRISE LUNDI 9H** 📅

**ENJOY YOUR WEEK-END !** 🎉
"""
        else:
            reduced_intensity = self.config.WEEKEND_REDUCTION_FACTOR
            message = f"""
🌴 **WEEK-END MODE !** 🌴

🏖️ **TRADING RELAX** 🏖️
• 📉 Intensité réduite: **{reduced_intensity:.0%}**
• 🌊 Volatilité plus faible
• 😌 Mode tranquille activé

⏰ **HORAIRES WEEK-END:**
• 🕘 **{self.config.WEEKEND_START_HOUR}h-{self.config.WEEKEND_END_HOUR}h**
• 🧘 Trading zen et décontracté

**WEEK-END PROFITS !** 💰🌴
"""
        
        await self.telegram.send_message(message)
        self.logger.info("🌴 Notification mode week-end envoyée")

    async def send_market_closure_warning(self, minutes_until_close: int):
        """⚠️ Notification d'approche de fermeture"""
        message = f"""
⚠️ **ATTENTION - FERMETURE PROCHE !** ⚠️

⏰ **Plus que {minutes_until_close} minutes** avant fermeture !

🔄 **ACTIONS EN COURS:**
• 📊 Vérification des positions ouvertes
• 🛡️ Sécurisation des profits
• 🔒 Préparation de la fermeture

**DERNIÈRE CHANCE POUR LES TRADES !** ⚡
"""
        
        await self.telegram.send_message(message)
        self.logger.info(f"⚠️ Notification fermeture -{minutes_until_close}min envoyée")

    async def send_volatility_alert(self, volatility_level: str):
        """📊 Notification d'alerte volatilité"""
        # Éviter les notifications répétées
        if self.last_volatility_alert == volatility_level:
            return
            
        self.last_volatility_alert = volatility_level
        
        if volatility_level == "HIGH":
            emoji = "🔥"
            message = f"""
{emoji} **VOLATILITÉ ÉLEVÉE DÉTECTÉE !** {emoji}

⚡ **OPPORTUNITÉS PREMIUM** ⚡
• 🚀 Mouvements rapides en cours
• 💎 Signaux de qualité maximale
• ⚡ Profits potentiels élevés
• 📈 Spreads potentiellement plus larges

🎯 **STRATÉGIE RECOMMANDÉE:**
• 🎯 Take profits plus rapides
• 🛡️ Stop loss plus serrés
• ⚡ Réactivité maximale
• 💰 Positions possiblement plus petites

**SOYEZ PRÊTS POUR L'ACTION !** 🎯
"""
        elif volatility_level == "LOW":
            emoji = "😴"
            message = f"""
{emoji} **VOLATILITÉ FAIBLE** {emoji}

🧘 **MARCHÉ CALME** 🧘
• 📉 Mouvements réduits
• ⏱️ Timeouts plus courts activés
• 🔒 Seuils plus sélectifs
• 🌊 Spreads généralement plus serrés

🎯 **STRATÉGIE ADAPTÉE:**
• ⏳ Patience requise
• 🎯 Take profits plus patients
• 📊 Focus sur les signaux de qualité
• 🔍 Attendre les meilleures opportunités

**PATIENCE, LES BONNES CHOSES ARRIVENT...** ⏳
"""
        else:  # NORMAL
            return  # Pas de notification pour volatilité normale
            
        await self.telegram.send_message(message)
        self.logger.info(f"📊 Notification volatilité {volatility_level} envoyée")

    async def check_volatility_and_notify(self, current_volatility: float):
        """Vérifie la volatilité et envoie des notifications si nécessaire"""
        # Seuils de volatilité (à ajuster selon les données historiques)
        HIGH_VOLATILITY_THRESHOLD = 2.0  # 2% de volatilité = élevée
        LOW_VOLATILITY_THRESHOLD = 0.5   # 0.5% de volatilité = faible
        
        if current_volatility > HIGH_VOLATILITY_THRESHOLD:
            await self.send_volatility_alert("HIGH")
        elif current_volatility < LOW_VOLATILITY_THRESHOLD:
            await self.send_volatility_alert("LOW")
        # Si entre les deux seuils, c'est "NORMAL" et on ne notifie pas

    async def reset_daily_notifications(self):
        """Remet à zéro les flags de notification quotidiens"""
        self.session_start_notified = False
        self.session_end_notified = False
        self.last_notification_hour = None
        self.last_volatility_alert = None
        self.logger.info("🔄 Flags de notification quotidiens remis à zéro")


async def main():
    """Test du notificateur d'horaires"""
    from config import APIConfig, TradingConfig
    
    config = TradingConfig()
    api_config = APIConfig()
    
    # Créer le notificateur Telegram
    telegram_notifier = TelegramNotifier(
        bot_token=api_config.TELEGRAM_BOT_TOKEN,
        chat_id=api_config.TELEGRAM_CHAT_ID
    )
    
    # Créer le notificateur d'horaires
    hours_notifier = TradingHoursNotifier(telegram_notifier, config)
    
    print("🧪 Test des notifications d'horaires...")
    
    # Test notification de début
    print("🌅 Test notification début de trading...")
    await hours_notifier.send_trading_start_notification()
    
    await asyncio.sleep(2)
    
    # Test notification lunch
    print("🍽️ Test notification lunch time...")
    await hours_notifier.send_lunch_time_notification()
    
    await asyncio.sleep(2)
    
    # Test notification power hour
    print("🇺🇸 Test notification power hour...")
    await hours_notifier.send_power_hour_notification()
    
    await asyncio.sleep(2)
    
    # Test notification fin
    print("🌙 Test notification fin de trading...")
    await hours_notifier.send_trading_end_notification()
    
    print("✅ Tests terminés !")


if __name__ == "__main__":
    asyncio.run(main())

"""
Notificateur Telegram pour le bot de trading
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

try:
    import telegram
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("⚠️ python-telegram-bot non installé. Installez avec: pip install python-telegram-bot")
    telegram = None

@dataclass
class NotificationConfig:
    """Configuration des notifications"""
    send_start: bool = True
    send_trade_open: bool = True
    send_trade_close: bool = True
    send_daily_summary: bool = True
    send_errors: bool = True
    send_signals: bool = False  # Peut être verbeux

class TelegramNotifier:
    """Gestionnaire de notifications Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str, config: Optional[NotificationConfig] = None, trading_config=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.config = config or NotificationConfig()
        self.trading_config = trading_config  # Configuration de trading pour les valeurs dynamiques
        self.logger = logging.getLogger(__name__)
        
        # Initialisation du bot
        self.bot = None
        if telegram and bot_token and chat_id:
            try:
                self.bot = Bot(token=bot_token) # type: ignore
                self.logger.info("📱 Notificateur Telegram initialisé")
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation Telegram: {e}")
        else:
            self.logger.warning("⚠️ Telegram non configuré ou module manquant")

    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Envoie un message Telegram"""
        if not self.bot:
            self.logger.debug("Telegram non configuré - message non envoyé")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            ) # type: ignore
            return True
        except TelegramError as e: # type: ignore
            self.logger.error(f"❌ Erreur envoi Telegram: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur inattendue Telegram: {e}")
            return False

    async def send_start_notification(self, capital: float):
        """Notification de démarrage du bot"""
        if not self.config.send_start:
            return
        
        # Valeurs dynamiques basées sur la configuration de trading
        daily_target_percent = self.trading_config.DAILY_TARGET_PERCENT if self.trading_config else 1.0
        daily_stop_percent = self.trading_config.DAILY_STOP_LOSS_PERCENT if self.trading_config else 1.0
        position_size_percent = self.trading_config.POSITION_SIZE_PERCENT if self.trading_config else 15
        max_positions = self.trading_config.MAX_OPEN_POSITIONS if self.trading_config else 3
        
        message = f"""
🚀 **Bot de Trading Scalping Démarré**

💰 **Capital initial:** {capital:.2f} EUR
🎯 **Objectif quotidien:** +{daily_target_percent}% = +{capital * daily_target_percent / 100:.2f} EUR
🛑 **Stop loss quotidien:** -{daily_stop_percent}% = -{capital * daily_stop_percent / 100:.2f} EUR
📊 **Taille position:** {position_size_percent}% du capital
🔢 **Max positions:** {max_positions} simultanées

⏰ **Heure de démarrage:** {datetime.now().strftime('%H:%M:%S')}

*Bonne chance pour cette session de trading ! 🍀*
"""
        
        await self.send_message(message)
        self.logger.info("📱 Notification de démarrage envoyée")

    async def send_trade_open_notification(self, trade, capital_engaged: float):
        """Notification d'ouverture de trade"""
        if not self.config.send_trade_open:
            return
        
        # Valeurs dynamiques basées sur la configuration
        stop_loss_percent = self.trading_config.STOP_LOSS_PERCENT if self.trading_config else 0.5
        take_profit_percent = self.trading_config.TAKE_PROFIT_PERCENT if self.trading_config else 1.0
        trailing_stop_percent = self.trading_config.TRAILING_STOP_PERCENT if self.trading_config else 0.5
        
        message = f"""
📈 **Trade Ouvert - {trade.pair}**

💰 **Prix d'entrée:** {trade.entry_price:.4f} EUR
📊 **Quantité:** {trade.size:.6f}
💵 **Capital engagé:** {capital_engaged:.2f} EUR

🛑 **Stop Loss:** {trade.stop_loss:.4f} EUR (-{stop_loss_percent}%)
🎯 **Take Profit:** {trade.take_profit:.4f} EUR (+{take_profit_percent}%)
🔄 **Trailing Stop:** Actif à +{trailing_stop_percent}%

⏰ **Ouverture:** {trade.timestamp.strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)
        self.logger.info(f"📱 Notification ouverture trade {trade.pair} envoyée")

    async def send_trade_close_notification(self, trade, pnl_amount: float, pnl_percent: float, daily_pnl: float, total_capital: float):
        """Notification de fermeture de trade"""
        if not self.config.send_trade_close:
            return
        
        # Emoji selon le résultat
        result_emoji = "🚀" if pnl_amount > 0 else "📉"
        
        # Calcul du pourcentage journalier basé sur le capital total dynamique
        daily_pnl_percent = daily_pnl / total_capital * 100
        
        message = f"""
{result_emoji} **Trade Fermé - {trade.pair}**

💰 **Prix de sortie:** {trade.exit_price:.4f} EUR
📊 **Résultat:** {pnl_amount:+.2f} EUR ({pnl_percent:+.2f}%)
⏱️ **Durée:** {trade.duration}
🔄 **Raison:** {trade.exit_reason}

📈 **Total journalier:** {daily_pnl:+.2f} EUR
💎 **Performance:** {daily_pnl_percent:+.2f}% (capital dynamique)

⏰ **Fermeture:** {trade.exit_timestamp.strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)
        self.logger.info(f"📱 Notification fermeture trade {trade.pair} envoyée")

    async def send_signal_notification(self, pair: str, signal_type: str, conditions: list, score: float):
        """Notification de signal détecté"""
        if not self.config.send_signals:
            return
        
        message = f"""
✅ **Signal Détecté - {pair}**

🎯 **Type:** {signal_type}
📊 **Score:** {score:.1f}/4

**Conditions remplies:**
"""
        
        for condition in conditions:
            message += f"• {condition}\n"
        
        message += f"\n⏰ **Détection:** {datetime.now().strftime('%H:%M:%S')}"
        
        await self.send_message(message)
        self.logger.info(f"📱 Notification signal {pair} envoyée")

    async def send_daily_summary(self, status: str, daily_pnl: float, trades_count: int, total_capital: float):
        """Notification de résumé quotidien"""
        if not self.config.send_daily_summary:
            return
        
        pnl_percent = daily_pnl / total_capital * 100
        status_emoji = "✅" if daily_pnl > 0 else "🛑"
        
        message = f"""
{status_emoji} **Résumé Quotidien - {status}**

💰 **P&L:** {daily_pnl:+.2f} EUR ({pnl_percent:+.2f}%)
📊 **Trades exécutés:** {trades_count}
💵 **Capital total:** {total_capital:.2f} EUR
💎 **Capital final:** {total_capital:.2f} EUR

📈 **Performance:** {pnl_percent:+.2f}% de rendement

⏰ **Fin de session:** {datetime.now().strftime('%H:%M:%S')}

*Excellente session de trading ! 🎉*
"""
        
        await self.send_message(message)
        self.logger.info("📱 Notification résumé quotidien envoyée")

    async def send_error_notification(self, error: str, context: str = ""):
        """Notification d'erreur"""
        if not self.config.send_errors:
            return
        
        message = f"""
⚠️ **Erreur Bot Trading**

🔥 **Erreur:** {error}
📍 **Contexte:** {context}
⏰ **Heure:** {datetime.now().strftime('%H:%M:%S')}

*Vérifiez les logs pour plus de détails.*
"""
        
        await self.send_message(message)
        self.logger.info("📱 Notification erreur envoyée")

    async def send_warning_notification(self, warning: str):
        """Notification d'avertissement"""
        message = f"""
⚠️ **Avertissement**

{warning}

⏰ **Heure:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)
        self.logger.info("📱 Notification avertissement envoyée")

    async def send_market_analysis(self, pair: str, analysis: str):
        """Notification d'analyse de marché"""
        message = f"""
📊 **Analyse de Marché - {pair}**

{analysis}

⏰ **Analyse:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)

    async def send_risk_alert(self, risk_level: str, details: str):
        """Notification d'alerte de risque"""
        message = f"""
🚨 **Alerte de Risque - {risk_level}**

{details}

⏰ **Alerte:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)
        self.logger.info("📱 Notification alerte risque envoyée")

    async def send_position_update(self, pair: str, current_pnl: float, trailing_stop: float):
        """Notification de mise à jour de position"""
        pnl_emoji = "📈" if current_pnl > 0 else "📉"
        
        message = f"""
{pnl_emoji} **Mise à jour Position - {pair}**

💰 **P&L actuel:** {current_pnl:+.2f} EUR
🔄 **Trailing Stop:** {trailing_stop:.4f} EUR

⏰ **Mise à jour:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)

    async def send_custom_notification(self, title: str, content: str, emoji: str = "ℹ️"):
        """Notification personnalisée"""
        message = f"""
{emoji} **{title}**

{content}

⏰ **Heure:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(message)

    async def test_connection(self) -> bool:
        """Test la connexion Telegram"""
        if not self.bot:
            return False
        
        try:
            await self.bot.get_me() # type: ignore
            await self.send_message("🤖 Test de connexion - Bot de Trading Scalping")
            return True
        except Exception as e:
            self.logger.error(f"❌ Test connexion Telegram échoué: {e}")
            return False

    def configure_notifications(self, config: NotificationConfig):
        """Configure les types de notifications"""
        self.config = config
        self.logger.info("📱 Configuration notifications mise à jour")

    async def send_heartbeat(self):
        """Envoie un signal de vie du bot"""
        message = f"""
💓 **Bot en vie**

⏰ **Heure:** {datetime.now().strftime('%H:%M:%S')}
🔄 **Statut:** Actif et surveillant le marché
"""
        
        await self.send_message(message)

# Exemple d'utilisation
async def main():
    """Test du notificateur"""
    # Configuration à mettre dans les variables d'environnement
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"
    
    notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)
    
    # Test de connexion
    if await notifier.test_connection():
        print("✅ Connexion Telegram OK")
    else:
        print("❌ Connexion Telegram échouée")

if __name__ == "__main__":
    asyncio.run(main())

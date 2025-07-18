"""
Utilitaires pour le logging
"""

import logging
import logging.config
import os
from datetime import datetime

from config import LOGGING_CONFIG


def setup_logger(name: str) -> logging.Logger:
    """Configure et retourne un logger"""
    
    # Création du dossier logs si nécessaire
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configuration du logging
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Création du logger
    logger = logging.getLogger(name)
    
    return logger

class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour la console"""
    
    # Codes couleur ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Vert
        'WARNING': '\033[33m',  # Jaune
        'ERROR': '\033[31m',    # Rouge
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_colored_logger(name: str) -> logging.Logger:
    """Configure un logger avec couleurs pour la console"""
    
    # Création du dossier logs si nécessaire
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configuration du logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Handler console avec couleurs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    colored_formatter = ColoredFormatter(
        fmt="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(colored_formatter)
    
    # Handler fichier
    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/trading_bot.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Ajout des handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

class TradingLogger:
    """Logger spécialisé pour le trading"""
    
    def __init__(self, name: str):
        self.logger = setup_colored_logger(name)
    
    def log_signal(self, pair: str, signal_type: str, conditions: list, score: float):
        """Log un signal de trading"""
        self.logger.info(f"✅ Signal {signal_type} détecté: {pair} (Score: {score:.1f})")
        for condition in conditions:
            self.logger.info(f"   - {condition}")
    
    def log_trade_open(self, trade_data: dict):
        """Log l'ouverture d'un trade"""
        self.logger.info(f"📈 Trade ouvert: {trade_data['pair']}")
        self.logger.info(f"   💰 Prix: {trade_data['price']:.4f} EUR")
        self.logger.info(f"   📊 Quantité: {trade_data['quantity']:.6f}")
        self.logger.info(f"   🛑 SL: {trade_data['stop_loss']:.4f} EUR")
        self.logger.info(f"   🎯 TP: {trade_data['take_profit']:.4f} EUR")
        self.logger.info(f"   💵 Capital: {trade_data['capital']:.2f} EUR")
    
    def log_trade_close(self, trade_data: dict):
        """Log la fermeture d'un trade"""
        pnl_symbol = "🚀" if trade_data['pnl'] > 0 else "📉"
        self.logger.info(f"{pnl_symbol} Trade fermé: {trade_data['pair']} ({trade_data['reason']})")
        self.logger.info(f"   💰 Prix: {trade_data['exit_price']:.4f} EUR")
        self.logger.info(f"   📊 P&L: {trade_data['pnl']:+.2f} EUR ({trade_data['pnl_percent']:+.2f}%)")
        self.logger.info(f"   ⏱️ Durée: {trade_data['duration']}")
        self.logger.info(f"   🔄 Total: {trade_data['daily_pnl']:+.2f} EUR")
    
    def log_pair_scan(self, pairs: list):
        """Log le scan des paires"""
        self.logger.info(f"🔎 Scan des paires: {len(pairs)} paires analysées")
        for i, pair in enumerate(pairs[:3]):  # Top 3
            self.logger.info(f"   {i+1}. {pair['symbol']} - Score: {pair['score']:.2f}")
    
    def log_daily_summary(self, summary: dict):
        """Log le résumé quotidien"""
        status_emoji = "✅" if summary['success'] else "🛑"
        self.logger.info(f"{status_emoji} Résumé quotidien:")
        self.logger.info(f"   💰 P&L: {summary['pnl']:+.2f} EUR ({summary['pnl_percent']:+.2f}%)")
        self.logger.info(f"   📊 Trades: {summary['trades']}")
        self.logger.info(f"   🎯 Capital final: {summary['final_capital']:.2f} EUR")
    
    def log_error(self, error: str, context: str = ""):
        """Log une erreur"""
        if context:
            self.logger.error(f"❌ {context}: {error}")
        else:
            self.logger.error(f"❌ {error}")
    
    def log_warning(self, warning: str):
        """Log un warning"""
        self.logger.warning(f"⚠️ {warning}")
    
    def log_info(self, info: str):
        """Log une information"""
        self.logger.info(f"ℹ️ {info}")
    
    def log_debug(self, debug: str):
        """Log du debug"""
        self.logger.debug(f"🔍 {debug}")

"""
Configuration du bot de trading scalping
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

@dataclass
class TradingConfig:
    """Configuration des paramètres de trading"""
    
    # Paramètres de capital
    DAILY_TARGET_PERCENT: float = 1.0  # Objectif quotidien +1%
    DAILY_STOP_LOSS_PERCENT: float = 1.0  # Stop loss quotidien -1%
    POSITION_SIZE_PERCENT: float = 17.5  # Taille position 15-20% (moyenne 17.5%)
    
    # Paramètres de position
    MAX_OPEN_POSITIONS: int = 3
    STOP_LOSS_PERCENT: float = 0.5  # SL -0.5%
    TAKE_PROFIT_PERCENT: float = 1.0  # TP +1%
    TRAILING_ACTIVATION_PERCENT: float = 0.5  # Activation trailing à +0.5%
    TRAILING_STEP_PERCENT: float = 0.3  # Step trailing 0.3%
    
    # Paramètres de timeout
    TRADE_TIMEOUT_MINUTES: int = 15
    MIN_PROFIT_BEFORE_TIMEOUT: float = 0.2  # +0.2% minimum avant timeout
    
    # Paramètres de sélection des paires
    MIN_VOLUME_EUR: float = 100000  # Volume minimum 100k EUR
    MAX_SPREAD_PERCENT: float = 0.2  # Spread maximum 0.2%
    MAX_PAIRS_TO_ANALYZE: int = 5  # Top 5 paires à analyser
    
    # Paramètres de timing
    SCAN_INTERVAL: int = 60  # Scan toutes les 60 secondes
    TIMEFRAME: str = "1MINUTE"  # Timeframe des bougies
    
    # Paramètres techniques
    EMA_FAST_PERIOD: int = 9
    EMA_SLOW_PERIOD: int = 21
    RSI_PERIOD: int = 14
    RSI_OVERSOLD_LEVEL: int = 40
    MACD_FAST_PERIOD: int = 12
    MACD_SLOW_PERIOD: int = 26
    MACD_SIGNAL_PERIOD: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD_DEV: int = 2
    
    # Seuils de signal
    MIN_SIGNAL_CONDITIONS: int = 3  # Minimum 3 conditions pour signal

@dataclass
class APIConfig:
    """Configuration des APIs"""
    
    # Binance API
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")
    TESTNET: bool = os.getenv("BINANCE_TESTNET", "False").lower() == "true"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    ENABLE_GOOGLE_SHEETS: bool = os.getenv("ENABLE_GOOGLE_SHEETS", "True").lower() == "true"
    
    def validate(self) -> bool:
        """Valide que toutes les clés API sont présentes"""
        required_keys = [
            "BINANCE_API_KEY",
            "BINANCE_SECRET_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "GOOGLE_SHEETS_SPREADSHEET_ID"
        ]
        
        for key in required_keys:
            if not getattr(self, key):
                raise ValueError(f"Clé API manquante: {key}")
        
        return True

# Configuration globale
API_CONFIG = APIConfig()

# Paires blacklistées (à exclure du trading)
BLACKLISTED_PAIRS = [
    "USDCEUR",  # Stablecoin
    "BUSDEUR",  # Stablecoin
    "TUSDEUR",  # Stablecoin
    "PAXGEUR",  # Or tokenisé
]

# Configuration du logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "console": {
            "format": "[%(asctime)s] %(levelname)s - %(message)s",
            "datefmt": "%H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "console",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filename": "logs/trading_bot.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

"""
Configuration du bot de trading scalping - CAPITAL ÉLEVÉ (15 480€)
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

@dataclass
class TradingConfig:
    """Configuration des paramètres de trading - Capital élevé optimisé"""
    
    # Paramètres de capital
    DAILY_TARGET_PERCENT: float = 1.0  # Objectif quotidien +1%
    DAILY_STOP_LOSS_PERCENT: float = 2.0  # Stop loss quotidien étendu pour capital élevé
    BASE_POSITION_SIZE_PERCENT: float = 12.0  # Taille de base (sera ajustée selon volatilité)
    
    # Paramètres de position - Configuration optimisée post-perte
    MAX_OPEN_POSITIONS: int = 5  # Plus d'opportunités simultanées
    MAX_TRADES_PER_PAIR: int = 2  # Limite par paire pour éviter surlevier caché
    MAX_EXPOSURE_PER_ASSET_PERCENT: float = 20.0  # Exposition max par crypto (20% du capital)
    STOP_LOSS_PERCENT: float = 0.25  # SL plus serré pour limiter pertes
    TAKE_PROFIT_PERCENT: float = 0.8  # TP légèrement plus conservateur
    TRAILING_ACTIVATION_PERCENT: float = 0.1  # Activation trailing dès 0.1%
    TRAILING_STEP_PERCENT: float = 0.2  # Step trailing plus fin
    
    # Paramètres de timeout adaptatifs
    TRADE_TIMEOUT_LOW_VOLATILITY: int = 20  # Timeout si volatilité faible
    TRADE_TIMEOUT_HIGH_VOLATILITY: int = 30  # Timeout si volatilité forte
    MIN_TIMEOUT_PROFIT_RANGE: tuple = (-0.2, 0.2)  # Range P&L pour timeout
    MIN_PROFIT_BEFORE_TIMEOUT: float = 0.1  # Sortie plus rapide si petit profit
    
    # Paramètres de sélection des paires - Critères renforcés
    MIN_VOLUME_EUR: float = 100000  # Volume minimum 100k EUR
    MAX_SPREAD_PERCENT: float = 0.15  # Spread plus strict pour capital élevé
    MAX_PAIRS_TO_ANALYZE: int = 5  # Top 5 paires à analyser
    MIN_VOLATILITY_1H_PERCENT: float = 0.5  # Volatilité minimum 1h requise
    
    # Position sizing adaptatif
    BASE_POSITION_SIZE_PERCENT: float = 12.0  # Taille de base
    VOLATILITY_REDUCTION_FACTOR: float = 0.5  # Réduction si volatilité élevée
    HIGH_VOLATILITY_THRESHOLD: float = 3.0  # Seuil volatilité élevée (%)
    LOW_VOLATILITY_THRESHOLD: float = 1.0   # Seuil volatilité faible (%)
    
    # Paramètres de timing
    SCAN_INTERVAL: int = 40  # Scan plus fréquent pour capital élevé
    TIMEFRAME: str = "1MINUTE"  # Timeframe des bougies
    
    # Paramètres techniques
    EMA_FAST_PERIOD: int = 9
    EMA_SLOW_PERIOD: int = 21
    RSI_PERIOD: int = 14
    RSI_OVERSOLD_LEVEL: int = 30  # Seuil de survente pour rebond
    RSI_BOUNCE_CONFIRM_LEVEL: int = 35  # Seuil de confirmation du rebond
    MACD_FAST_PERIOD: int = 12
    MACD_SLOW_PERIOD: int = 26
    MACD_SIGNAL_PERIOD: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD_DEV: int = 2
    
    # Seuils de signal - Plus sélectif pour capital élevé
    MIN_SIGNAL_CONDITIONS: int = 4
    
    # Paramètres de gestion des positions et soldes
    PHANTOM_POSITION_THRESHOLD: float = 0.00001  # Seuil position fantôme
    BALANCE_SAFETY_MARGIN: float = 0.999  # Marge de sécurité pour soldes (99.9%)
    BALANCE_TOLERANCE: float = 0.001  # Tolérance erreurs d'arrondi
    
    # Paramètres de sortie momentum faible
    ENABLE_MOMENTUM_EXIT: bool = True  # Activer sortie momentum faible
    MOMENTUM_PNL_RANGE: tuple = (-0.2, 0.2)  # Range P&L pour sortie momentum
    MOMENTUM_RSI_THRESHOLD: int = 45  # RSI max pour sortie momentum
    MOMENTUM_MACD_NEGATIVE: bool = True  # MACD histogram négatif requis

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

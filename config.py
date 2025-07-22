"""
Configuration du bot de trading scalping - CAPITAL ÉLEVÉ EN USDC
Optimisé pour liquidité et volume maximum
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

@dataclass
class TradingConfig:
    """Configuration des paramètres de trading - Capital USDC optimisé"""
    
    # Paramètres de capital USDC
    DAILY_TARGET_PERCENT: float = 1.0  # Objectif quotidien +1%
    DAILY_STOP_LOSS_PERCENT: float = 2.0  # Stop loss quotidien étendu pour capital élevé
    BASE_POSITION_SIZE_PERCENT: float = 25.0  # 25% du capital USDC
    MIN_POSITION_SIZE_USDC: float = 500.0  # Taille minimale 500$ par trade
    MAX_POSITION_SIZE_USDC: float = 5000.0  # Taille maximale 5000$ par trade
    
    # Paramètres de position - Anti-fragmentation
    MAX_OPEN_POSITIONS: int = 3  # Moins de positions mais plus grosses
    MAX_TRADES_PER_PAIR: int = 1  # UN SEUL trade par paire max
    MAX_EXPOSURE_PER_ASSET_PERCENT: float = 30.0  # Exposition max par crypto (30% pour haute liquidité)
    STOP_LOSS_PERCENT: float = 0.25  # SL plus serré pour limiter pertes
    TAKE_PROFIT_PERCENT: float = 1.2  # TP optimisé pour USDC haute liquidité
    TRAILING_ACTIVATION_PERCENT: float = 0.5  # OPTIMISÉ: Activation trailing à +0.5% (plus conservateur)
    TRAILING_STEP_PERCENT: float = 0.2  # Step trailing plus fin
    
    # Paramètres anti-fragmentation - OPTIMISÉS ANTI-SURTRADING
    MIN_TRADE_INTERVAL_SECONDS: int = 300  # OPTIMISÉ: Minimum 5 minutes entre trades
    MAX_TRADES_PER_HOUR: int = 2  # OPTIMISÉ: Maximum 2 trades par heure
    CONSOLIDATE_SMALL_TRADES: bool = True  # Consolider les petits trades
    
    # Paramètres de timeout adaptatifs
    TRADE_TIMEOUT_LOW_VOLATILITY: int = 20  # Timeout si volatilité faible
    TRADE_TIMEOUT_HIGH_VOLATILITY: int = 30  # Timeout si volatilité forte
    MIN_TIMEOUT_PROFIT_RANGE: tuple = (-0.2, 0.2)  # Range P&L pour timeout
    MIN_PROFIT_BEFORE_TIMEOUT: float = 0.1  # Sortie plus rapide si petit profit
    
    # Paramètres de sélection des paires USDC - Critères renforcés OPTIMISÉS
    MIN_VOLUME_USDC: float = 100000000  # OPTIMISÉ: Volume minimum 100M$ (ultra-liquide)
    MAX_SPREAD_PERCENT: float = 0.15  # OPTIMISÉ: Spread plus strict 0.15% pour éviter slippage
    MAX_PAIRS_TO_ANALYZE: int = 6  # OPTIMISÉ: Moins de paires, meilleures uniquement
    MIN_VOLATILITY_1H_PERCENT: float = 0.5  # Volatilité minimum 1h requise
    
    # Horaires de trading optimisés (heure française/européenne)
    TRADING_HOURS_ENABLED: bool = True  # Activer restriction horaires
    TRADING_START_HOUR: int = 9   # 09:00 - Début session EU
    TRADING_END_HOUR: int = 23    # 23:00 - Fin session US
    
    # Horaires premium (intensité maximale)
    PREMIUM_HOURS: list = field(default_factory=lambda: [
        (9, 12),   # 09:00-12:00 Session EU morning
        (15, 18),  # 15:00-18:00 Golden hours EU-US
        (18, 21),  # 18:00-21:00 Session US prime
    ])
    
    # Pause déjeuner (activité réduite)
    LUNCH_BREAK_START: int = 12   # 12:00
    LUNCH_BREAK_END: int = 14     # 14:00
    LUNCH_REDUCTION_FACTOR: float = 0.5  # 50% moins de trades
    
    # Week-end (trading réduit)
    WEEKEND_TRADING_ENABLED: bool = True
    WEEKEND_START_HOUR: int = 10  # 10:00
    WEEKEND_END_HOUR: int = 22    # 22:00
    WEEKEND_REDUCTION_FACTOR: float = 0.3  # 70% moins de trades
    
    # Position sizing adaptatif USDC - ANTI-FRAGMENTATION
    BASE_POSITION_SIZE_PERCENT: float = 25.0  # 25% capital USDC
    VOLATILITY_REDUCTION_FACTOR: float = 0.8  # Réduction moins agressive
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
    MIN_SIGNAL_CONDITIONS: int = 4  # R7: Garder 4 conditions minimum
    
    # OPTIMISÉ R2: Confirmation de cassure pour éviter faux signaux
    ENABLE_BREAKOUT_CONFIRMATION: bool = True  # Activer confirmation cassure
    BREAKOUT_CONFIRMATION_PERCENT: float = 0.1  # Cassure confirmée si price > last_high + 0.1%
    
    # Paramètres de gestion des positions et soldes
    PHANTOM_POSITION_THRESHOLD: float = 0.00001  # Seuil position fantôme
    DUST_BALANCE_THRESHOLD_USDC: float = 5.0  # Ignorer les soldes < 5$ USDC pour exposition
    BALANCE_SAFETY_MARGIN: float = 0.999  # Marge de sécurité pour soldes (99.9%)
    BALANCE_TOLERANCE: float = 0.001  # Tolérance erreurs d'arrondi
    
    # Paramètres de sortie momentum faible
    ENABLE_MOMENTUM_EXIT: bool = True  # Activer sortie momentum faible
    MOMENTUM_PNL_RANGE: tuple = (-0.1, 0.1)  # Range P&L pour sortie momentum (plus restrictif)
    MOMENTUM_RSI_THRESHOLD: int = 35  # RSI max pour sortie momentum (vraiment faible)
    MOMENTUM_MACD_NEGATIVE: bool = True  # MACD histogram négatif requis
    MOMENTUM_MIN_DURATION_MINUTES: int = 3  # Durée minimale avant sortie momentum (3 min)
    
    # OPTIMISÉ: Protection contre les pertes consécutives
    MAX_CONSECUTIVE_LOSSES: int = 3  # Arrêt automatique après 3 pertes consécutives
    ENABLE_CONSECUTIVE_LOSS_PROTECTION: bool = True  # Activer protection pertes consécutives
    CONSECUTIVE_LOSS_PAUSE_MINUTES: int = 60  # Pause en minutes après pertes consécutives
    AUTO_RESUME_AFTER_PAUSE: bool = True  # Reprendre automatiquement après pause

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
    _credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
    # Conversion en chemin absolu si c'est un chemin relatif
    if not os.path.isabs(_credentials_path):
        GOOGLE_SHEETS_CREDENTIALS: str = os.path.join(os.path.dirname(__file__), _credentials_path)
    else:
        GOOGLE_SHEETS_CREDENTIALS: str = _credentials_path
    
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

# Paires blacklistées USDC (à exclure du trading)
BLACKLISTED_PAIRS = [
    "USDCUSDC",  # Conversion directe
    "USDCUSDT", # Autre stablecoin
    "BUSDUSDC", # Stablecoin deprecated
    "TUSDUSDC", # Stablecoin
    "PAXGUSDC", # Or tokenisé
    "XRPUSDC",  # Mauvaise performance (-6.12 USDC)
    "DOGEUSDC", # Mauvaise performance (-5.31 USDC)
    "ADAUSDC",  # Mauvaise performance (-15.58 USDC)
    "SUIUSDC",   # Mauvaise performance (-13.47 USDC)
    "SOLUSDC",  # Mauvaise performance (-77 USDC)
]

# Paires prioritaires USDC (haute liquidité) - OPTIMISÉES
PRIORITY_USDC_PAIRS = [
    'BTCUSDC',   # 2B$ volume/jour - Meilleure performance
    'ETHUSDC',   # 1.5B$ volume/jour - Acceptable
    'MATICUSDC', # 150M$ volume/jour
    'LTCUSDC',   # 150M$ volume/jour
    'LINKUSDC',  # 100M$ volume/jour
    'DOTUSDC',   # 80M$ volume/jour
    # Paires BLACKLISTÉES pour mauvaises performances:
    # 'XRPUSDC',   # -6.12 USDC (2 trades) - BLACKLISTÉ
    # 'DOGEUSDC',  # -5.31 USDC (1 trade) - BLACKLISTÉ
    # 'ADAUSDC',   # -15.58 USDC (4 trades) - BLACKLISTÉ
    # 'SUIUSDC',   # -13.47 USDC (5 trades) - BLACKLISTÉ
    # 'SOLUSDC',   # - 77 USDC (3 trades) - BLACKLISTÉ
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

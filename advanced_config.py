"""
Configuration avancée du bot de trading - Exemple personnalisé
Copiez ce fichier vers custom_config.py pour personnaliser
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from config import APIConfig, TradingConfig


@dataclass
class CustomTradingConfig(TradingConfig):
    """Configuration personnalisée pour trading avancé"""
    
    # === PARAMÈTRES AVANCÉS ===
    
    # Gestion du capital dynamique
    ADAPTIVE_POSITION_SIZE: bool = True  # Ajuste la taille selon performance
    MIN_POSITION_SIZE_PERCENT: float = 10.0  # Minimum 10%
    MAX_POSITION_SIZE_PERCENT: float = 25.0  # Maximum 25%
    
    # Gestion des corrélations
    MAX_CORRELATION_EXPOSURE: float = 0.7  # Max 70% exposition corrélée
    CORRELATION_PAIRS: Optional[Dict[str, List[str]]] = None  # Définir les corrélations
    
    # Filtres avancés
    MIN_MARKET_CAP: float = 1000000000  # 1 milliard EUR minimum
    VOLATILITY_FILTER: bool = True  # Filtre volatilité excessive
    MAX_VOLATILITY_PERCENT: float = 15.0  # Max 15% volatilité 24h
    
    # Horaires de trading
    TRADING_HOURS_ENABLED: bool = False  # Activer restriction horaire
    TRADING_START_HOUR: int = 8  # Début 8h
    TRADING_END_HOUR: int = 20  # Fin 20h
    WEEKEND_TRADING: bool = True  # Trading weekend (crypto 24/7)
    
    # Gestion des news
    NEWS_FILTER_ENABLED: bool = False  # Éviter trading pendant news
    HIGH_IMPACT_NEWS_PAUSE: int = 30  # Pause 30 min après news importante
    
    # Stratégies multiples
    MULTI_STRATEGY_ENABLED: bool = False  # Activer stratégies multiples
    SCALPING_WEIGHT: float = 0.6  # 60% scalping
    MOMENTUM_WEIGHT: float = 0.4  # 40% momentum
    
    # Optimisation performance
    PERFORMANCE_BASED_SIZING: bool = True  # Ajuster selon performance
    DRAWDOWN_REDUCTION_THRESHOLD: float = 0.5  # Réduire à -0.5% drawdown
    WINNING_STREAK_BOOST: bool = True  # Augmenter après série gagnante
    
    # Machine Learning (future)
    ML_ENABLED: bool = False  # Activer ML (à développer)
    ML_MODEL_PATH: str = "models/trading_model.pkl"
    
    def __post_init__(self):
        """Initialisation post-création"""
        if self.CORRELATION_PAIRS is None:
            self.CORRELATION_PAIRS = {
                'BTC': ['BCH', 'BSV', 'LTC'],
                'ETH': ['ETC', 'EOS', 'ADA'],
                'BNB': ['CAKE', 'TWT', 'BAKE'],
                'DOT': ['KSM', 'ATOM', 'AVAX'],
                'LINK': ['BAND', 'API3', 'GRT']
            }

@dataclass
class AggressiveConfig(TradingConfig):
    """Configuration agressive - Rendement élevé, risque élevé"""
    
    DAILY_TARGET_PERCENT: float = 2.0  # Objectif +2%
    DAILY_STOP_LOSS_PERCENT: float = 2.0  # Stop loss -2%
    POSITION_SIZE_PERCENT: float = 25.0  # 25% par position
    MAX_OPEN_POSITIONS: int = 4  # 4 positions max
    
    STOP_LOSS_PERCENT: float = 0.8  # SL -0.8%
    TAKE_PROFIT_PERCENT: float = 1.5  # TP +1.5%
    TRAILING_ACTIVATION_PERCENT: float = 0.7  # Trailing à +0.7%
    
    MIN_VOLUME_EUR: float = 500000  # 500k EUR minimum
    MAX_SPREAD_PERCENT: float = 0.3  # 0.3% spread max
    SCAN_INTERVAL: int = 30  # Scan toutes les 30s
    
    MIN_SIGNAL_CONDITIONS: int = 2  # Seulement 2 conditions requises

@dataclass
class ConservativeConfig(TradingConfig):
    """Configuration conservative - Risque faible, rendement modéré"""
    
    DAILY_TARGET_PERCENT: float = 0.5  # Objectif +0.5%
    DAILY_STOP_LOSS_PERCENT: float = 0.5  # Stop loss -0.5%
    POSITION_SIZE_PERCENT: float = 10.0  # 10% par position
    MAX_OPEN_POSITIONS: int = 2  # 2 positions max
    
    STOP_LOSS_PERCENT: float = 0.3  # SL -0.3%
    TAKE_PROFIT_PERCENT: float = 0.6  # TP +0.6%
    TRAILING_ACTIVATION_PERCENT: float = 0.3  # Trailing à +0.3%
    
    MIN_VOLUME_EUR: float = 1000000  # 1M EUR minimum
    MAX_SPREAD_PERCENT: float = 0.1  # 0.1% spread max
    SCAN_INTERVAL: int = 120  # Scan toutes les 2 minutes
    
    MIN_SIGNAL_CONDITIONS: int = 4  # 4 conditions requises

@dataclass
class DayTradingConfig(TradingConfig):
    """Configuration day trading - Active pendant journée"""
    
    DAILY_TARGET_PERCENT: float = 1.5  # Objectif +1.5%
    DAILY_STOP_LOSS_PERCENT: float = 1.0  # Stop loss -1%
    POSITION_SIZE_PERCENT: float = 20.0  # 20% par position
    MAX_OPEN_POSITIONS: int = 3  # 3 positions max
    
    STOP_LOSS_PERCENT: float = 0.6  # SL -0.6%
    TAKE_PROFIT_PERCENT: float = 1.2  # TP +1.2%
    TRAILING_ACTIVATION_PERCENT: float = 0.4  # Trailing à +0.4%
    
    # Horaires de trading
    TRADING_HOURS_ENABLED: bool = True
    TRADING_START_HOUR: int = 9  # 9h
    TRADING_END_HOUR: int = 17  # 17h
    
    # Timeframe plus court
    TIMEFRAME: str = "1MINUTE"
    SCAN_INTERVAL: int = 45  # Scan toutes les 45s

@dataclass
class ScalpingProConfig(TradingConfig):
    """Configuration scalping professionnel - Très actif"""
    
    DAILY_TARGET_PERCENT: float = 3.0  # Objectif +3%
    DAILY_STOP_LOSS_PERCENT: float = 1.5  # Stop loss -1.5%
    POSITION_SIZE_PERCENT: float = 30.0  # 30% par position
    MAX_OPEN_POSITIONS: int = 5  # 5 positions max
    
    STOP_LOSS_PERCENT: float = 0.4  # SL -0.4%
    TAKE_PROFIT_PERCENT: float = 0.8  # TP +0.8%
    TRAILING_ACTIVATION_PERCENT: float = 0.3  # Trailing à +0.3%
    TRAILING_STEP_PERCENT: float = 0.2  # Step 0.2%
    
    # Très actif
    SCAN_INTERVAL: int = 15  # Scan toutes les 15s
    TRADE_TIMEOUT_MINUTES: int = 5  # Timeout 5 minutes
    MIN_PROFIT_BEFORE_TIMEOUT: float = 0.1  # +0.1% minimum
    
    # Filtres stricts
    MIN_VOLUME_EUR: float = 2000000  # 2M EUR minimum
    MAX_SPREAD_PERCENT: float = 0.05  # 0.05% spread max
    MIN_SIGNAL_CONDITIONS: int = 4  # 4 conditions requises

# === CONFIGURATIONS PRÉDÉFINIES ===

TRADING_PROFILES = {
    'default': TradingConfig(),
    'aggressive': AggressiveConfig(),
    'conservative': ConservativeConfig(),
    'daytrading': DayTradingConfig(),
    'scalping_pro': ScalpingProConfig(),
    'custom': CustomTradingConfig()
}

# === FONCTIONS UTILITAIRES ===

def get_config_by_profile(profile_name: str) -> TradingConfig:
    """Récupère une configuration par nom de profil"""
    if profile_name not in TRADING_PROFILES:
        raise ValueError(f"Profil inconnu: {profile_name}")
    return TRADING_PROFILES[profile_name]

def list_available_profiles() -> List[str]:
    """Liste les profils disponibles"""
    return list(TRADING_PROFILES.keys())

def create_custom_config(**kwargs) -> TradingConfig:
    """Crée une configuration personnalisée"""
    base_config = TradingConfig()
    
    # Mise à jour avec les paramètres personnalisés
    for key, value in kwargs.items():
        if hasattr(base_config, key):
            setattr(base_config, key, value)
        else:
            print(f"⚠️ Paramètre ignoré: {key}")
    
    return base_config

# === EXEMPLE D'UTILISATION ===

if __name__ == "__main__":
    # Affichage des profils disponibles
    print("📊 Profils de trading disponibles:")
    for profile in list_available_profiles():
        config = get_config_by_profile(profile)
        print(f"  - {profile}: Objectif {config.DAILY_TARGET_PERCENT}%, SL {config.DAILY_STOP_LOSS_PERCENT}%")
    
    # Exemple configuration personnalisée
    my_config = create_custom_config(
        DAILY_TARGET_PERCENT=1.5,
        POSITION_SIZE_PERCENT=15.0,
        MAX_OPEN_POSITIONS=2,
        STOP_LOSS_PERCENT=0.4,
        TAKE_PROFIT_PERCENT=0.8
    )
    
    print(f"\\n🎯 Configuration personnalisée créée:")
    print(f"  Objectif: {my_config.DAILY_TARGET_PERCENT}%")
    print(f"  Position: {my_config.BASE_POSITION_SIZE_PERCENT}%")
    print(f"  SL: {my_config.STOP_LOSS_PERCENT}%")
    print(f"  TP: {my_config.TAKE_PROFIT_PERCENT}%")

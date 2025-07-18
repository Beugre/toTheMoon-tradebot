"""
Utilitaires divers pour le bot de trading
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Union


def retry(max_attempts: int = 3, delay: float = 1, backoff: float = 2):
    """Décorateur pour retry automatique"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        logging.warning(f"Tentative {attempt + 1} échouée: {e}. Retry dans {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logging.error(f"Toutes les tentatives échouées: {e}")
            
            raise last_exception # type: ignore
        return wrapper
    return decorator

class ConfigManager:
    """Gestionnaire de configuration dynamique"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            logging.error(f"Erreur chargement config: {e}")
            self.config = self.get_default_config()
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Erreur sauvegarde config: {e}")
    
    def get_default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            "trading": {
                "daily_target_percent": 1.0,
                "daily_stop_loss_percent": 1.0,
                "position_size_percent": 17.5,
                "max_open_positions": 3,
                "stop_loss_percent": 0.5,
                "take_profit_percent": 1.0,
                "trailing_activation_percent": 0.5,
                "trailing_step_percent": 0.3
            },
            "market": {
                "min_volume_eur": 100000,
                "max_spread_percent": 0.2,
                "max_pairs_to_analyze": 5,
                "scan_interval": 60,
                "timeframe": "1MINUTE"
            },
            "notifications": {
                "send_start": True,
                "send_trade_open": True,
                "send_trade_close": True,
                "send_daily_summary": True,
                "send_errors": True,
                "send_signals": False
            }
        }
    
    def get(self, key: str, default=None):
        """Récupère une valeur de configuration"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value):
        """Définit une valeur de configuration"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()

class PerformanceTracker:
    """Suivi des performances en temps réel"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'api_calls': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'avg_trade_duration': 0.0
        }
        self.trade_durations = []
    
    def increment_api_calls(self):
        """Incrémente le compteur d'appels API"""
        self.metrics['api_calls'] += 1
    
    def add_trade_result(self, pnl: float, duration: timedelta, success: bool):
        """Ajoute le résultat d'un trade"""
        if success:
            self.metrics['successful_trades'] += 1
        else:
            self.metrics['failed_trades'] += 1
        
        self.metrics['total_pnl'] += pnl
        self.trade_durations.append(duration.total_seconds())
        
        # Calcul du win rate
        total_trades = self.metrics['successful_trades'] + self.metrics['failed_trades']
        if total_trades > 0:
            self.metrics['win_rate'] = self.metrics['successful_trades'] / total_trades * 100
        
        # Calcul durée moyenne
        if self.trade_durations:
            self.metrics['avg_trade_duration'] = sum(self.trade_durations) / len(self.trade_durations)
    
    def get_performance_summary(self) -> Dict:
        """Retourne un résumé des performances"""
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime': str(uptime),
            'api_calls': self.metrics['api_calls'],
            'total_trades': self.metrics['successful_trades'] + self.metrics['failed_trades'],
            'successful_trades': self.metrics['successful_trades'],
            'failed_trades': self.metrics['failed_trades'],
            'win_rate': self.metrics['win_rate'],
            'total_pnl': self.metrics['total_pnl'],
            'avg_trade_duration': self.metrics['avg_trade_duration'],
            'api_calls_per_minute': self.metrics['api_calls'] / max(uptime.total_seconds() / 60, 1)
        }

class RateLimiter:
    """Limiteur de taux pour les appels API"""
    
    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """Acquiert un token pour un appel API"""
        now = time.time()
        
        # Nettoyage des anciens appels
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Vérification de la limite
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.calls.append(now)

class CircuitBreaker:
    """Circuit breaker pour protection contre les échecs"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        """Décorateur pour circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker ouvert")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e
        
        return wrapper

class DataValidator:
    """Validateur de données"""
    
    @staticmethod
    def validate_trade_data(trade_data: Dict) -> bool:
        """Valide les données d'un trade"""
        required_fields = ['pair', 'size', 'entry_price', 'stop_loss', 'take_profit']
        
        for field in required_fields:
            if field not in trade_data:
                return False
        
        # Vérification des valeurs numériques
        numeric_fields = ['size', 'entry_price', 'stop_loss', 'take_profit']
        for field in numeric_fields:
            if not isinstance(trade_data[field], (int, float)) or trade_data[field] <= 0:
                return False
        
        # Vérification logique SL/TP
        if trade_data['stop_loss'] >= trade_data['entry_price']:
            return False
        
        if trade_data['take_profit'] <= trade_data['entry_price']:
            return False
        
        return True
    
    @staticmethod
    def validate_pair_data(pair_data: Dict) -> bool:
        """Valide les données d'une paire"""
        required_fields = ['symbol', 'price', 'volume']
        
        for field in required_fields:
            if field not in pair_data:
                return False
        
        # Vérification du format du symbole
        if not pair_data['symbol'].endswith('EUR'):
            return False
        
        return True

class FileManager:
    """Gestionnaire de fichiers"""
    
    @staticmethod
    def ensure_directory(path: str):
        """Crée un répertoire s'il n'existe pas"""
        if not os.path.exists(path):
            os.makedirs(path)
    
    @staticmethod
    def save_json(data: Dict, filepath: str):
        """Sauvegarde des données JSON"""
        try:
            FileManager.ensure_directory(os.path.dirname(filepath))
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Erreur sauvegarde JSON: {e}")
    
    @staticmethod
    def load_json(filepath: str) -> Optional[Dict]:
        """Charge des données JSON"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Erreur chargement JSON: {e}")
        return None
    
    @staticmethod
    def backup_file(filepath: str):
        """Crée une sauvegarde d'un fichier"""
        try:
            if os.path.exists(filepath):
                backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(filepath, backup_path)
        except Exception as e:
            logging.error(f"Erreur backup: {e}")

class TimeUtils:
    """Utilitaires de temps"""
    
    @staticmethod
    def is_market_open() -> bool:
        """Vérifie si le marché crypto est ouvert (24/7)"""
        return True
    
    @staticmethod
    def get_next_market_open() -> datetime:
        """Retourne la prochaine ouverture du marché"""
        return datetime.now()  # Marché crypto ouvert 24/7
    
    @staticmethod
    def format_duration(duration: timedelta) -> str:
        """Formate une durée en string lisible"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @staticmethod
    def is_weekend() -> bool:
        """Vérifie si c'est le weekend (pas pertinent pour crypto)"""
        return False  # Marché crypto ouvert 24/7

class MathUtils:
    """Utilitaires mathématiques"""
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calcule le pourcentage de changement"""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def round_to_precision(value: float, precision: int) -> float:
        """Arrondit à la précision spécifiée"""
        return round(value, precision)
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Limite une valeur entre min et max"""
        return max(min_val, min(max_val, value))
    
    @staticmethod
    def calculate_position_size(capital: float, risk_percent: float, 
                             entry_price: float, stop_loss: float) -> float:
        """Calcule la taille de position basée sur le risque"""
        risk_amount = capital * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
        
        return risk_amount / price_diff

class MemoryManager:
    """Gestionnaire de mémoire"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.data_store = {}
    
    def add_data(self, key: str, data: any): # type: ignore
        """Ajoute des données avec limitation de taille"""
        if key not in self.data_store:
            self.data_store[key] = []
        
        self.data_store[key].append(data)
        
        # Limitation de la taille
        if len(self.data_store[key]) > self.max_history:
            self.data_store[key] = self.data_store[key][-self.max_history:]
    
    def get_data(self, key: str) -> List:
        """Récupère les données"""
        return self.data_store.get(key, [])
    
    def clear_data(self, key: str):
        """Efface les données pour une clé"""
        if key in self.data_store:
            del self.data_store[key]
    
    def get_memory_usage(self) -> Dict:
        """Retourne l'utilisation mémoire"""
        return {
            'keys': len(self.data_store),
            'total_items': sum(len(data) for data in self.data_store.values())
        }

# Décorateurs utiles
def measure_time(func):
    """Décorateur pour mesurer le temps d'exécution"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        logging.info(f"{func.__name__} executé en {end_time - start_time:.2f}s")
        return result
    return wrapper

def log_function_call(func):
    """Décorateur pour logger les appels de fonction"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging.debug(f"Appel de {func.__name__} avec args={args}, kwargs={kwargs}")
        result = await func(*args, **kwargs)
        logging.debug(f"{func.__name__} retourne: {result}")
        return result
    return wrapper

"""
Gestionnaire de risques pour le trading
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from config import TradingConfig


@dataclass
class RiskMetrics:
    """Métriques de risque"""
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

class RiskManager:
    """Gestionnaire de risques avancé"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Métriques de risque
        self.metrics = RiskMetrics()
        
        # Historique des trades
        self.trade_history = []
        
        # État du risque
        self.daily_loss_limit_reached = False
        self.max_positions_reached = False
        
        # Capital tracking
        self.initial_capital = 0.0
        self.current_capital = 0.0
        self.peak_capital = 0.0
        
        # Contrôle des corrélations
        self.open_positions = {}
        
        self.logger.info("🛡️ Gestionnaire de risques initialisé")

    def set_initial_capital(self, capital: float):
        """Définit le capital initial"""
        self.initial_capital = capital
        self.current_capital = capital
        self.peak_capital = capital
        self.logger.info(f"💰 Capital initial: {capital:.2f} EUR")

    def can_open_position(self, pair: str, position_size: float, current_positions: int) -> Tuple[bool, str]:
        """Vérifie si une position peut être ouverte"""
        
        # Vérification du nombre maximum de positions
        if current_positions >= self.config.MAX_OPEN_POSITIONS:
            return False, "Nombre maximum de positions atteint"
        
        # Vérification du capital disponible
        if position_size > self.current_capital:
            return False, "Capital insuffisant"
        
        # Vérification de la taille de position
        max_position_size = self.current_capital * self.config.BASE_POSITION_SIZE_PERCENT / 100
        if position_size > max_position_size * 1.1:  # 10% de marge
            return False, f"Taille de position trop importante (max: {max_position_size:.2f} EUR)"
        
        # Vérification position déjà ouverte sur la même paire
        if pair in self.open_positions:
            return False, "Position déjà ouverte sur cette paire"
        
        # Vérification du stop loss quotidien
        if self.daily_loss_limit_reached:
            return False, "Limite de perte quotidienne atteinte"
        
        # Vérification du drawdown maximum
        if self.metrics.current_drawdown > self.config.DAILY_STOP_LOSS_PERCENT * 1.5:
            return False, "Drawdown maximum atteint"
        
        return True, "OK"

    def calculate_position_size(self, capital: float, risk_level: float = 1.0) -> float:
        """Calcule la taille optimale de position"""
        
        # Taille de base
        base_size = capital * self.config.BASE_POSITION_SIZE_PERCENT / 100
        
        # Ajustement selon le niveau de risque
        adjusted_size = base_size * risk_level
        
        # Vérification des limites
        min_size = capital * 0.10  # Minimum 10%
        max_size = capital * 0.25  # Maximum 25%
        
        adjusted_size = max(min_size, min(max_size, adjusted_size))
        
        return adjusted_size

    def calculate_stop_loss(self, entry_price: float, direction: str = "LONG") -> float:
        """Calcule le stop loss"""
        if direction == "LONG":
            return entry_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
        else:
            return entry_price * (1 + self.config.STOP_LOSS_PERCENT / 100)

    def calculate_take_profit(self, entry_price: float, direction: str = "LONG") -> float:
        """Calcule le take profit"""
        if direction == "LONG":
            return entry_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
        else:
            return entry_price * (1 - self.config.TAKE_PROFIT_PERCENT / 100)

    def update_trailing_stop(self, entry_price: float, current_price: float, 
                           current_stop: float, direction: str = "LONG") -> float:
        """Met à jour le trailing stop"""
        
        if direction == "LONG":
            # Vérification activation du trailing
            activation_price = entry_price * (1 + self.config.TRAILING_ACTIVATION_PERCENT / 100)
            
            if current_price >= activation_price:
                # Nouveau stop loss
                new_stop = current_price * (1 - self.config.TRAILING_STEP_PERCENT / 100)
                return max(current_stop, new_stop)
        
        return current_stop

    def register_position_open(self, pair: str, size: float, entry_price: float):
        """Enregistre l'ouverture d'une position"""
        self.open_positions[pair] = {
            'size': size,
            'entry_price': entry_price,
            'timestamp': datetime.now()
        }
        
        # Mise à jour du capital
        self.current_capital -= size
        
        self.logger.info(f"📊 Position ouverte: {pair} - Taille: {size:.2f} EUR")

    def register_position_close(self, pair: str, exit_price: float, pnl: float):
        """Enregistre la fermeture d'une position"""
        if pair in self.open_positions:
            position = self.open_positions[pair]
            
            # Calcul des métriques
            self.update_metrics(pnl, position['size'])
            
            # Mise à jour du capital
            self.current_capital += position['size'] + pnl
            
            # Mise à jour du peak capital
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
            
            # Calcul du drawdown
            self.metrics.current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital * 100
            
            # Mise à jour du drawdown maximum
            if self.metrics.current_drawdown > self.metrics.max_drawdown:
                self.metrics.max_drawdown = self.metrics.current_drawdown
            
            # Suppression de la position
            del self.open_positions[pair]
            
            # Ajout à l'historique
            self.trade_history.append({
                'pair': pair,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl': pnl,
                'timestamp': datetime.now(),
                'duration': datetime.now() - position['timestamp']
            })
            
            self.logger.info(f"📊 Position fermée: {pair} - P&L: {pnl:+.2f} EUR")

    def update_metrics(self, pnl: float, position_size: float):
        """Met à jour les métriques de risque"""
        self.metrics.total_trades += 1
        
        if pnl > 0:
            self.metrics.winning_trades += 1
            self.metrics.avg_win = (self.metrics.avg_win * (self.metrics.winning_trades - 1) + pnl) / self.metrics.winning_trades
        else:
            self.metrics.losing_trades += 1
            self.metrics.avg_loss = (self.metrics.avg_loss * (self.metrics.losing_trades - 1) + abs(pnl)) / self.metrics.losing_trades
        
        # Calcul du win rate
        self.metrics.win_rate = self.metrics.winning_trades / self.metrics.total_trades * 100
        
        # Calcul du profit factor
        total_wins = self.metrics.winning_trades * self.metrics.avg_win
        total_losses = self.metrics.losing_trades * self.metrics.avg_loss
        
        if total_losses > 0:
            self.metrics.profit_factor = total_wins / total_losses
        else:
            self.metrics.profit_factor = float('inf')

    def check_daily_limits(self) -> bool:
        """Vérifie les limites quotidiennes"""
        daily_pnl_percent = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        # Objectif quotidien atteint
        if daily_pnl_percent >= self.config.DAILY_TARGET_PERCENT:
            self.logger.info("🎯 Objectif quotidien atteint")
            return True
        
        # Stop loss quotidien atteint
        if daily_pnl_percent <= -self.config.DAILY_STOP_LOSS_PERCENT:
            self.daily_loss_limit_reached = True
            self.logger.warning("🛑 Stop loss quotidien atteint")
            return True
        
        return False

    def get_risk_assessment(self) -> Dict:
        """Retourne une évaluation du risque"""
        return {
            'daily_pnl_percent': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'current_drawdown': self.metrics.current_drawdown,
            'max_drawdown': self.metrics.max_drawdown,
            'win_rate': self.metrics.win_rate,
            'profit_factor': self.metrics.profit_factor,
            'total_trades': self.metrics.total_trades,
            'open_positions': len(self.open_positions),
            'capital_utilization': (self.initial_capital - self.current_capital) / self.initial_capital * 100
        }

    def get_correlation_risk(self, new_pair: str) -> float:
        """Calcule le risque de corrélation avec les positions ouvertes"""
        if not self.open_positions:
            return 0.0
        
        # Analyse simple basée sur les crypto de base
        base_crypto = new_pair.replace('EUR', '').replace('USD', '')
        
        correlation_count = 0
        for open_pair in self.open_positions.keys():
            open_base = open_pair.replace('EUR', '').replace('USD', '')
            
            # Corrélation directe
            if base_crypto == open_base:
                correlation_count += 1
            
            # Corrélations connues (à étendre selon besoins)
            correlated_pairs = {
                'BTC': ['BCH', 'BSV'],
                'ETH': ['ETC', 'LTC'],
                'BNB': ['CAKE', 'TWT']
            }
            
            for main_crypto, correlated in correlated_pairs.items():
                if base_crypto == main_crypto and open_base in correlated:
                    correlation_count += 0.5
                elif base_crypto in correlated and open_base == main_crypto:
                    correlation_count += 0.5
        
        return min(correlation_count, 1.0)  # Maximum 100%

    def should_reduce_position_size(self, pair: str) -> bool:
        """Détermine si la taille de position doit être réduite"""
        
        # Réduction si drawdown important
        if self.metrics.current_drawdown > self.config.DAILY_STOP_LOSS_PERCENT * 0.5:
            return True
        
        # Réduction si série de pertes
        if len(self.trade_history) >= 3:
            recent_trades = self.trade_history[-3:]
            if all(trade['pnl'] < 0 for trade in recent_trades):
                return True
        
        # Réduction si corrélation élevée
        if self.get_correlation_risk(pair) > 0.7:
            return True
        
        return False

    def get_risk_level(self, pair: str) -> float:
        """Retourne le niveau de risque pour une paire (0.5 à 1.5)"""
        risk_level = 1.0
        
        # Réduction si conditions défavorables
        if self.should_reduce_position_size(pair):
            risk_level *= 0.7
        
        # Réduction si beaucoup de positions ouvertes
        if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS - 1:
            risk_level *= 0.8
        
        # Augmentation si performance positive
        if self.metrics.win_rate > 60 and self.metrics.total_trades > 5:
            risk_level *= 1.1
        
        return max(0.5, min(1.5, risk_level))

    def log_risk_status(self):
        """Log le statut du risque"""
        assessment = self.get_risk_assessment()
        
        self.logger.info("🛡️ Statut du risque:")
        self.logger.info(f"   📊 P&L quotidien: {assessment['daily_pnl_percent']:+.2f}%")
        self.logger.info(f"   📉 Drawdown actuel: {assessment['current_drawdown']:.2f}%")
        self.logger.info(f"   🎯 Win rate: {assessment['win_rate']:.1f}%")
        self.logger.info(f"   💰 Profit factor: {assessment['profit_factor']:.2f}")
        self.logger.info(f"   🔄 Positions ouvertes: {assessment['open_positions']}/{self.config.MAX_OPEN_POSITIONS}")

    def reset_daily_metrics(self):
        """Remet à zéro les métriques quotidiennes"""
        self.daily_loss_limit_reached = False
        self.trade_history = []
        self.metrics = RiskMetrics()
        self.logger.info("🔄 Métriques quotidiennes réinitialisées")

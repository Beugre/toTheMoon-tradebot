"""
Bot de Trading Scalping Automatisé - CAPITAL DYNAMIQUE
Stratégie multi-paires EUR avec gestion avancée des risques
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Trading & APIs
import ccxt
import gspread
import numpy as np
import pandas as pd
import talib
# Notifications & Logging
import telegram
from binance.client import Client
from binance.enums import (ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET, SIDE_BUY, SIDE_SELL,
                           TIME_IN_FORCE_GTC)
from binance.exceptions import BinanceAPIException, BinanceOrderException
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot

# Configuration
from config import API_CONFIG, TradingConfig
from utils.database import TradingDatabase
from utils.logger import setup_logger
from utils.risk_manager import RiskManager
from utils.sheets_logger import SheetsLogger
from utils.technical_indicators import TechnicalAnalyzer
from utils.telegram_notifier import TelegramNotifier


class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

@dataclass
class Trade:
    id: str
    pair: str
    direction: TradeDirection
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    trailing_stop: float
    timestamp: datetime
    status: TradeStatus = TradeStatus.OPEN
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: float = 0.0
    duration: Optional[timedelta] = None
    exit_reason: str = ""
    db_id: Optional[int] = None

@dataclass
class PairScore:
    pair: str
    volatility: float
    volume: float
    score: float
    spread: float
    atr: float = 0.0

class ScalpingBot:
    def __init__(self):
        self.logger = setup_logger("ScalpingBot")
        self.config = TradingConfig()
        
        # Initialize APIs
        self.binance_client = Client(
            API_CONFIG.BINANCE_API_KEY,
            API_CONFIG.BINANCE_SECRET_KEY,
            testnet=API_CONFIG.TESTNET
        )
        
        # Initialize utilities
        self.risk_manager = RiskManager(self.config)
        self.technical_analyzer = TechnicalAnalyzer()
        self.telegram_notifier = TelegramNotifier(
            API_CONFIG.TELEGRAM_BOT_TOKEN, 
            API_CONFIG.TELEGRAM_CHAT_ID, 
            trading_config=self.config
        )
        
        # Initialize Google Sheets optionally
        if API_CONFIG.ENABLE_GOOGLE_SHEETS:
            try:
                self.sheets_logger = SheetsLogger(
                    API_CONFIG.GOOGLE_SHEETS_CREDENTIALS, 
                    API_CONFIG.GOOGLE_SHEETS_SPREADSHEET_ID
                )
                logging.info(f"📊 Google Sheets activé - ID: {API_CONFIG.GOOGLE_SHEETS_SPREADSHEET_ID}")
            except Exception as e:
                logging.error(f"❌ Erreur Google Sheets: {e}")
                self.sheets_logger = None
        else:
            self.sheets_logger = None
            logging.info("📊 Google Sheets désactivé")
        
        # Bot state
        self.is_running = False
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.open_positions: Dict[str, Trade] = {}  # Une position par ID unique
        self.start_capital = 0.0
        self.current_capital = 0.0
        self.daily_target_reached = False
        self.daily_stop_loss_hit = False
        
        # Base de données
        self.database = TradingDatabase()
        
        # Compteur pour métriques temps réel
        self.metrics_counter = 0
        
        self.logger.info("🚀 Bot de Trading Scalping initialisé")

    async def start(self):
        """Lance le bot de trading"""
        self.logger.info("🟢 [STARTING] Démarrage du bot...")
        
        # Initialisation de la base de données
        await self.database.initialize_database()
        
        # Nettoyage des positions fantômes
        await self.cleanup_phantom_positions()
        
        # Initialisation du capital
        await self.initialize_capital()
        
        # Notification de démarrage
        await self.telegram_notifier.send_start_notification(self.start_capital)
        
        self.is_running = True
        self.logger.info("🟢 [RUNNING] Bot lancé avec succès")
        
        # Boucle principale
        await self.main_loop()

    def detect_phantom_positions(self) -> List[str]:
        """Détecte les positions fantômes (positions ouvertes sans solde correspondant)"""
        phantom_positions = []
        
        for trade_id, trade in self.open_positions.items():
            symbol = trade.pair
            try:
                base_asset = symbol.replace('EUR', '')
                available_balance = self.get_asset_balance(base_asset)
                
                # Position fantôme si solde pratiquement nul mais position ouverte
                if available_balance < self.config.PHANTOM_POSITION_THRESHOLD and trade.size > 0.001:
                    phantom_positions.append(trade_id)
                    self.logger.warning(f"👻 Position fantôme détectée: {symbol}")
                    self.logger.warning(f"   Position size: {trade.size:.8f} {base_asset}")
                    self.logger.warning(f"   Solde disponible: {available_balance:.8f} {base_asset}")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur vérification position fantôme {symbol}: {e}")
                
        return phantom_positions
    
    async def cleanup_phantom_positions(self):
        """Nettoie automatiquement les positions fantômes"""
        phantom_positions = self.detect_phantom_positions()
        
        if phantom_positions:
            self.logger.info(f"🧹 Nettoyage de {len(phantom_positions)} position(s) fantôme(s)")
            
            for trade_id in phantom_positions:
                try:
                    trade = self.open_positions[trade_id]
                    symbol = trade.pair
                    ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    await self.close_position_virtually(trade_id, current_price, "PHANTOM_CLEANUP")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur nettoyage position fantôme {trade_id}: {e}")
                    
        return len(phantom_positions)

    async def initialize_capital(self):
        """Initialise le capital à partir de l'API Binance (EUR + valeur crypto)"""
        try:
            account_info = self.binance_client.get_account()
            eur_balance = 0.0
            crypto_value = 0.0
            significant_balances = []
            self.logger.info("💰 Soldes disponibles:")
            for balance in account_info['balances']:
                free_balance = float(balance['free'])
                asset = balance['asset']
                if free_balance > 0:
                    if asset == 'EUR':
                        eur_balance = free_balance
                        self.logger.info(f"   💶 {asset}: {free_balance:.2f}")
                    elif free_balance > 0.001:
                        # Conversion en EUR pour le capital initial
                        try:
                            symbol = asset + 'EUR'
                            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                            price_eur = float(ticker['price'])
                            value_eur = free_balance * price_eur
                            crypto_value += value_eur
                            significant_balances.append(f"{asset}: {free_balance:.8f} ({value_eur:.2f} EUR)")
                        except Exception:
                            significant_balances.append(f"{asset}: {free_balance:.8f}")
            if significant_balances:
                self.logger.info(f"   🪙 Autres: {', '.join(significant_balances[:5])}")
            if eur_balance == 0.0 and crypto_value == 0.0:
                raise ValueError("Aucun solde EUR ou crypto trouvé dans le compte")
            total_capital = eur_balance + crypto_value
            self.start_capital = total_capital
            self.current_capital = total_capital
            self.logger.info(f"💰 Capital initial total: {self.start_capital:.2f} EUR (EUR: {eur_balance:.2f}, Crypto: {crypto_value:.2f})")
            self.logger.info(f"📊 Taille de position configurée: {self.config.BASE_POSITION_SIZE_PERCENT}% = {self.calculate_position_size():.2f} EUR")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation capital: {e}")
            raise

    async def main_loop(self):
        """Boucle principale du bot"""
        while self.is_running:
            try:
                # Vérification des conditions d'arrêt quotidien
                if self.should_stop_daily_trading():
                    await self.handle_daily_stop()
                    break
                
                # Scan des paires EUR
                top_pairs = await self.scan_eur_pairs()
                
                # Recherche de signaux
                for pair_info in top_pairs:
                    if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS:
                        break
                    
                    signal = await self.analyze_pair(pair_info.pair)
                    if signal:
                        await self.execute_trade(pair_info.pair, signal)
                
                # Gestion des positions ouvertes
                await self.manage_open_positions()
                
                # Enregistrement périodique des métriques (toutes les 10 itérations)
                self.metrics_counter += 1
                if self.metrics_counter % 10 == 0:
                    await self.save_realtime_metrics()
                
                # Vérification de cohérence des positions (toutes les 50 itérations)
                if self.metrics_counter % 50 == 0:
                    await self.check_positions_consistency()
                
                # Pause avant le prochain scan
                await asyncio.sleep(self.config.SCAN_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans la boucle principale: {e}")
                await asyncio.sleep(5)

    async def scan_eur_pairs(self) -> List[PairScore]:
        """Scanne et classe les paires EUR par score"""
        try:
            self.logger.info("🔎 Scan des paires EUR en cours...")
            
            # Récupération des tickers
            tickers = self.binance_client.get_ticker()
            eur_pairs = [t for t in tickers if t['symbol'].endswith('EUR')]
            
            pair_scores = []
            
            for ticker in eur_pairs:
                symbol = ticker['symbol']
                
                # Vérification volume minimum
                volume_eur = float(ticker['quoteVolume'])
                if volume_eur < self.config.MIN_VOLUME_EUR:
                    continue
                
                # Calcul spread
                bid = float(ticker['bidPrice'])
                ask = float(ticker['askPrice'])
                spread = (ask - bid) / bid * 100
                
                if spread > self.config.MAX_SPREAD_PERCENT:
                    continue
                
                # Calcul volatilité
                price_change = abs(float(ticker['priceChangePercent']))
                
                # Calcul ATR (optionnel)
                atr = await self.calculate_atr(symbol)
                
                # Score de sélection
                score = (0.6 * price_change + 0.4 * (volume_eur / 1000000))
                
                pair_scores.append(PairScore(
                    pair=symbol,
                    volatility=price_change,
                    volume=volume_eur,
                    score=score,
                    spread=spread,
                    atr=atr
                ))
            
            # Tri par score décroissant
            pair_scores.sort(key=lambda x: x.score, reverse=True)
            top_pairs = pair_scores[:self.config.MAX_PAIRS_TO_ANALYZE]
            
            self.logger.info(f"📊 Top {len(top_pairs)} paires sélectionnées:")
            for i, pair in enumerate(top_pairs):
                self.logger.info(f"  {i+1}. {pair.pair} - Score: {pair.score:.2f} - Vol: {pair.volatility:.2f}% - Volume: {pair.volume/1000000:.1f}M EUR")
            
            return top_pairs
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du scan des paires: {e}")
            return []

    async def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calcule l'ATR pour une paire"""
        try:
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=period + 1
            )
            
            if len(klines) < period:
                return 0.0
            
            high = np.array([float(k[2]) for k in klines])
            low = np.array([float(k[3]) for k in klines])
            close = np.array([float(k[4]) for k in klines])
            
            atr = talib.ATR(high, low, close, timeperiod=period) # type: ignore
            return atr[-1] if not np.isnan(atr[-1]) else 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul ATR pour {symbol}: {e}")
            return 0.0

    async def analyze_pair(self, symbol: str) -> Optional[TradeDirection]:
        """Analyse technique d'une paire pour détecter un signal"""
        try:
            # Récupération des données
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=getattr(Client, f'KLINE_INTERVAL_{self.config.TIMEFRAME}'),
                limit=100
            )
            
            if len(klines) < 50:
                return None
            
            # Préparation des données
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades_count', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Calcul des indicateurs techniques
            signal_score = 0
            conditions = []
            
            # EMA 9 et 21
            ema9 = talib.EMA(df['close'], timeperiod=9) # type: ignore
            ema21 = talib.EMA(df['close'], timeperiod=21) # type: ignore
            
            if ema9.iloc[-1] > ema21.iloc[-1]:
                signal_score += 1
                conditions.append("EMA(9) > EMA(21)")
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(df['close']) # type: ignore
            if not np.isnan(macd.iloc[-1]) and not np.isnan(macdsignal.iloc[-1]):
                if macd.iloc[-1] > macdsignal.iloc[-1]:
                    signal_score += 1
                    conditions.append("MACD > Signal")
            
            # RSI - Détection de rebond confirmé
            rsi = talib.RSI(df['close'], timeperiod=self.config.RSI_PERIOD) # type: ignore
            if not np.isnan(rsi.iloc[-1]) and not np.isnan(rsi.iloc[-2]):
                # Rebond confirmé : RSI était en survente et remonte
                if (rsi.iloc[-2] < self.config.RSI_OVERSOLD_LEVEL and 
                    rsi.iloc[-1] > self.config.RSI_BOUNCE_CONFIRM_LEVEL):
                    signal_score += 1
                    conditions.append(f"RSI rebond confirmé ({rsi.iloc[-2]:.1f} -> {rsi.iloc[-1]:.1f})")
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2) # type: ignore
            current_price = df['close'].iloc[-1]
            
            if not np.isnan(bb_lower.iloc[-1]):
                if current_price <= bb_lower.iloc[-1] * 1.002:  # 0.2% de marge
                    signal_score += 1
                    conditions.append("Prix proche Bollinger inf.")
            
            # Signal valide si >= 3 conditions
            if signal_score >= 3:
                self.logger.info(f"✅ Signal détecté : {symbol} (Score : {signal_score}/4)")
                for condition in conditions:
                    self.logger.info(f"   - {condition}")
                return TradeDirection.LONG
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse {symbol}: {e}")
            return None

    async def execute_trade(self, symbol: str, direction: TradeDirection):
        """Exécute un trade"""
        try:
            # Calculer la volatilité pour cette paire
            volatility = self.calculate_volatility_1h(symbol)
            
            # Vérifications avant entrée avec nouveaux critères
            can_open, reason = self.can_open_position_enhanced(symbol, volatility)
            if not can_open:
                self.logger.info(f"❌ Trade {symbol} refusé: {reason}")
                return
            
            # Informations d'allocation avant trade
            total_capital = self.get_total_capital()
            eur_balance = self.get_asset_balance('EUR')
            base_asset = symbol.replace('EUR', '')
            current_exposure = self.get_asset_exposure(base_asset)
            
            # Calcul de la taille de position avec sizing adaptatif
            position_size = self.calculate_position_size(symbol, volatility)
            
            self.logger.info(f"💰 Allocation avant trade {symbol}:")
            self.logger.info(f"   📊 Capital total: {total_capital:.2f} EUR")
            self.logger.info(f"   💶 EUR disponible: {eur_balance:.2f} EUR")
            self.logger.info(f"   🎯 Taille position: {position_size:.2f} EUR (volatilité: {volatility:.2f}%)")
            self.logger.info(f"   📈 Exposition {base_asset} actuelle: {current_exposure:.2f} EUR")
            self.logger.info(f"   🏦 Positions ouvertes: {len(self.open_positions)}")
            
            # Récupération du prix actuel
            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Calcul SL et TP
            stop_loss = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
            take_profit = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
            trailing_stop = current_price * (1 + self.config.TRAILING_ACTIVATION_PERCENT / 100)
            
            # Calcul de la quantité
            quantity = position_size / current_price
            
            # Validation et ajustement de la quantité
            is_valid, validation_msg, adjusted_quantity = self.validate_order_quantity(symbol, quantity, current_price)
            
            if not is_valid:
                self.logger.warning(f"⚠️ Quantité invalide pour {symbol}: {validation_msg}")
                # Utilisation de la quantité ajustée si possible
                if adjusted_quantity > 0:
                    quantity = adjusted_quantity
                    position_size = quantity * current_price  # Recalcul du capital engagé
                    self.logger.info(f"🔧 Quantité ajustée: {quantity:.8f} (capital: {position_size:.2f} EUR)")
                else:
                    self.logger.error(f"❌ Impossible de trader {symbol}: quantité minimale non respectée")
                    return
            
            # Arrondi final selon les règles de la paire
            quantity = self.round_quantity(symbol, quantity)
            
            # Vérification finale de la valeur notionnelle
            final_notional = quantity * current_price
            if final_notional < 10.0:  # Minimum Binance général
                self.logger.warning(f"⚠️ Valeur notionnelle trop faible pour {symbol}: {final_notional:.2f} EUR < 10 EUR")
                return
            
            # Capital avant trade (AVANT l'achat)
            capital_before_trade = self.get_total_capital()
            
            # Passage de l'ordre
            order = self.binance_client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            # Création du trade
            trade = Trade(
                id=order['orderId'],
                pair=symbol,
                direction=direction,
                size=quantity,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                trailing_stop=trailing_stop,
                timestamp=datetime.now()
            )
            
            # Ajout aux positions ouvertes avec ID unique
            trade_id = f"{symbol}_{trade.id}_{int(datetime.now().timestamp())}"
            self.open_positions[trade_id] = trade
            
            # Mise à jour du capital
            self.current_capital -= position_size
            
            # Logging
            self.logger.info(f"📈 Trade ouvert : {symbol}")
            self.logger.info(f"   💰 Prix d'entrée: {current_price:.4f} EUR")
            self.logger.info(f"   📊 Quantité: {quantity:.6f}")
            self.logger.info(f"   🛑 Stop Loss: {stop_loss:.4f} EUR (-{self.config.STOP_LOSS_PERCENT}%)")
            self.logger.info(f"   🎯 Take Profit: {take_profit:.4f} EUR (+{self.config.TAKE_PROFIT_PERCENT}%)")
            self.logger.info(f"   💵 Capital engagé: {position_size:.2f} EUR")
            
            # Notification Telegram
            await self.telegram_notifier.send_trade_open_notification(trade, position_size)
            
            # Log dans Google Sheets (si activé)
            if self.sheets_logger:
                # Capital après = EUR total + crypto existant APRÈS l'achat
                capital_after_trade = self.get_total_capital()
                
                self.logger.info(f"📊 Google Sheets - Capital avant: {capital_before_trade:.2f} EUR, après: {capital_after_trade:.2f} EUR (différence: {capital_after_trade - capital_before_trade:+.2f} EUR)")
                await self.sheets_logger.log_trade(trade, "OPEN", capital_before_trade, capital_after_trade)
            
            # Enregistrement en base de données
            try:
                trade_data = {
                    'symbol': symbol,
                    'side': 'BUY',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'trailing_stop': trailing_stop,
                    'entry_time': datetime.now(),
                    'capital_engaged': position_size,
                    'signals_detected': {
                        'direction': direction.value,
                        'position_size': position_size
                    }
                }
                trade_id = await self.database.insert_trade(trade_data)
                trade.db_id = trade_id  # Stockage de l'ID DB dans le trade
                self.logger.info(f"📊 Trade enregistré en base (ID: {trade_id})")
            except Exception as e:
                self.logger.error(f"❌ Erreur enregistrement DB: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'exécution du trade {symbol}: {e}")

    def can_open_position(self, symbol: str) -> bool:
        """Vérifie si on peut ouvrir une position"""
        # Vérification nombre de positions
        if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS:
            self.logger.debug(f"❌ Limite max positions atteinte: {len(self.open_positions)}")
            return False
        
        # Vérification position déjà ouverte sur la paire
        trades_on_pair = [trade for trade_id, trade in self.open_positions.items() if trade.pair == symbol]
        if len(trades_on_pair) >= self.config.MAX_TRADES_PER_PAIR:
            self.logger.debug(f"❌ Limite trades par paire atteinte: {len(trades_on_pair)}/{self.config.MAX_TRADES_PER_PAIR}")
            return False
        
        # Vérification capital EUR disponible (pas le total avec crypto!)
        position_size = self.calculate_position_size()
        eur_balance = self.get_asset_balance('EUR')
        if eur_balance < position_size:
            self.logger.debug(f"❌ Capital EUR insuffisant: {eur_balance:.2f} < {position_size:.2f}")
            return False
        
        # Vérification exposition maximale par asset de base
        base_asset = symbol.replace('EUR', '')
        current_exposure = self.get_asset_exposure(base_asset)
        max_exposure_per_asset = self.get_total_capital() * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
        
        if current_exposure + position_size > max_exposure_per_asset:
            self.logger.debug(f"❌ Exposition {base_asset} trop élevée: {current_exposure:.2f} + {position_size:.2f} > {max_exposure_per_asset:.2f}")
            return False
        
        # Vérification objectif/stop loss quotidien
        if self.daily_target_reached or self.daily_stop_loss_hit:
            self.logger.debug(f"❌ Objectif/stop loss quotidien atteint")
            return False
        
        return True
    
    def get_asset_exposure(self, base_asset: str) -> float:
        """Calcule l'exposition actuelle sur un asset de base (positions ouvertes + soldes existants)"""
        total_exposure = 0.0
        
        # 1. Exposition des positions ouvertes tracées par le bot
        for trade_id, trade in self.open_positions.items():
            if trade.pair.replace('EUR', '') == base_asset:
                try:
                    ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                    current_price = float(ticker['price'])
                    position_value = trade.size * current_price
                    total_exposure += position_value
                except Exception as e:
                    self.logger.error(f"❌ Erreur calcul exposition position {trade.pair}: {e}")
                    # Fallback sur le prix d'entrée
                    position_value = trade.size * trade.entry_price
                    total_exposure += position_value
        
        # 2. Exposition des soldes crypto existants (CRITIQUE!)
        try:
            existing_balance = self.get_asset_balance(base_asset)
            if existing_balance > 0.00001:  # Seuil pour éviter les poussières
                symbol = base_asset + 'EUR'
                ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                existing_value = existing_balance * current_price
                total_exposure += existing_value
                
                self.logger.debug(f"💎 Exposition {base_asset}: Positions ouvertes: {total_exposure - existing_value:.2f} EUR + Solde existant: {existing_value:.2f} EUR = Total: {total_exposure:.2f} EUR")
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul exposition solde existant {base_asset}: {e}")
        
        return total_exposure

    def calculate_position_size(self, pair: Optional[str] = None, volatility: Optional[float] = None) -> float:
        """Calcule la taille de position avec sizing adaptatif basé sur la volatilité"""
        total_capital = self.get_total_capital()
        base_size = total_capital * self.config.BASE_POSITION_SIZE_PERCENT / 100
        
        # Si pas de volatilité fournie, utiliser la taille de base
        if volatility is None:
            return base_size
        
        # Position sizing adaptatif selon la volatilité
        if volatility > self.config.HIGH_VOLATILITY_THRESHOLD:
            # Réduire la taille pour paires très volatiles
            reduction_factor = min(0.5, self.config.VOLATILITY_REDUCTION_FACTOR * (volatility / self.config.HIGH_VOLATILITY_THRESHOLD))
            adjusted_size = base_size * (1 - reduction_factor)
            self.logger.info(f"📊 Position réduite pour {pair} (volatilité {volatility:.2f}%): {adjusted_size:.2f} EUR")
            return adjusted_size
        elif volatility < self.config.LOW_VOLATILITY_THRESHOLD:
            # Augmenter légèrement pour paires peu volatiles (plus sûres)
            adjusted_size = base_size * 1.1
            self.logger.info(f"📊 Position augmentée pour {pair} (faible volatilité {volatility:.2f}%): {adjusted_size:.2f} EUR")
            return adjusted_size
        else:
            # Volatilité normale, taille de base
            return base_size

    def round_quantity(self, symbol: str, quantity: float) -> float:
        """Arrondit la quantité selon les règles de la paire"""
        try:
            info = self.binance_client.get_symbol_info(symbol)
            for filter_item in info['filters']: # type: ignore
                if filter_item['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_item['stepSize'])
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    return round(quantity, precision)
            return round(quantity, 6)
        except:
            return round(quantity, 6)
    
    def get_symbol_filters(self, symbol: str) -> dict:
        """Récupère les filtres de trading pour un symbole"""
        try:
            info = self.binance_client.get_symbol_info(symbol)
            filters = {}
            
            for filter_item in info['filters']: # type: ignore
                if filter_item['filterType'] == 'LOT_SIZE':
                    filters['min_qty'] = float(filter_item['minQty'])
                    filters['max_qty'] = float(filter_item['maxQty'])
                    filters['step_size'] = float(filter_item['stepSize'])
                elif filter_item['filterType'] == 'MIN_NOTIONAL':
                    filters['min_notional'] = float(filter_item['minNotional'])
                elif filter_item['filterType'] == 'PRICE_FILTER':
                    filters['min_price'] = float(filter_item['minPrice'])
                    filters['max_price'] = float(filter_item['maxPrice'])
                    filters['tick_size'] = float(filter_item['tickSize'])
            
            return filters
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération filtres {symbol}: {e}")
            return {}
    
    def validate_order_quantity(self, symbol: str, quantity: float, price: float) -> tuple[bool, str, float]:
        """Valide et ajuste une quantité d'ordre"""
        try:
            filters = self.get_symbol_filters(symbol)
            
            if not filters:
                return True, "Pas de filtres disponibles", quantity
            
            # Vérification quantité minimale
            min_qty = filters.get('min_qty', 0)
            if quantity < min_qty:
                return False, f"Quantité {quantity:.8f} < minimum {min_qty:.8f}", min_qty
            
            # Vérification quantité maximale
            max_qty = filters.get('max_qty', float('inf'))
            if quantity > max_qty:
                return False, f"Quantité {quantity:.8f} > maximum {max_qty:.8f}", max_qty
            
            # Arrondi selon step_size
            step_size = filters.get('step_size', 0)
            if step_size > 0:
                quantity = round(quantity / step_size) * step_size
            
            # Vérification valeur notionnelle minimale
            min_notional = filters.get('min_notional', 0)
            notional_value = quantity * price
            if notional_value < min_notional:
                # Calcul de la quantité minimale pour respecter min_notional
                min_qty_for_notional = min_notional / price
                if step_size > 0:
                    min_qty_for_notional = round(min_qty_for_notional / step_size) * step_size
                return False, f"Valeur notionnelle {notional_value:.2f} < minimum {min_notional:.2f}", min_qty_for_notional
            
            return True, "OK", quantity
            
        except Exception as e:
            self.logger.error(f"❌ Erreur validation quantité {symbol}: {e}")
            return True, f"Erreur validation: {e}", quantity
    
    def get_asset_balance(self, asset: str) -> float:
        """Récupère le solde disponible d'un asset"""
        try:
            account_info = self.binance_client.get_account()
            for balance in account_info['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération solde {asset}: {e}")
            return 0.0

    def get_total_capital(self) -> float:
        """Calcule le capital total dynamique (EUR + valeur de TOUTES les cryptos du compte)"""
        try:
            account_info = self.binance_client.get_account()
            total_capital = 0.0
            
            # Solde EUR
            eur_balance = 0.0
            crypto_value = 0.0
            
            for balance in account_info['balances']:
                free_balance = float(balance['free'])
                asset = balance['asset']
                
                if free_balance > 0:
                    if asset == 'EUR':
                        eur_balance = free_balance
                        total_capital += eur_balance
                    elif free_balance > 0.00001:  # Seuil pour éviter les poussières
                        # Conversion en EUR pour tous les autres assets
                        try:
                            symbol = asset + 'EUR'
                            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                            price_eur = float(ticker['price'])
                            value_eur = free_balance * price_eur
                            crypto_value += value_eur
                            total_capital += value_eur
                            self.logger.debug(f"💎 {asset}: {free_balance:.8f} x {price_eur:.4f} = {value_eur:.2f} EUR")
                        except Exception:
                            # Si pas de paire EUR pour cet asset, on ignore
                            self.logger.debug(f"⚠️ Pas de conversion EUR pour {asset}")
                            continue
            
            self.logger.debug(f"💰 Capital total: {total_capital:.2f} EUR (EUR libre: {eur_balance:.2f}, Toutes cryptos: {crypto_value:.2f})")
            return total_capital
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul capital total: {e}")
            # Fallback sur le capital courant
            return self.current_capital

    async def manage_open_positions(self):
        """Gère les positions ouvertes et la surexposition"""
        for trade_id, trade in list(self.open_positions.items()):
            try:
                # Récupération du prix actuel
                ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                current_price = float(ticker['price'])

                # Calcul du P&L
                pnl_percent = (current_price - trade.entry_price) / trade.entry_price * 100

                # Vérification surexposition dynamique
                base_asset = trade.pair.replace('EUR', '')
                current_exposure = self.get_asset_exposure(base_asset)
                max_exposure_per_asset = self.get_total_capital() * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
                if current_exposure > max_exposure_per_asset * 1.01:  # tolérance 1%
                    self.logger.warning(f"⚠️ Surexposition détectée sur {base_asset}: {current_exposure:.2f} EUR > {max_exposure_per_asset:.2f} EUR ({self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)")
                    await self.close_position(trade_id, current_price, "SUREXPOSITION_AUTO")
                    continue

                # Vérification timeout adaptatif
                volatility = self.calculate_volatility_1h(trade.pair)
                should_timeout, timeout_reason = self.should_timeout_position(trade, current_price, volatility)
                if should_timeout:
                    self.logger.info(f"⏱️ {timeout_reason}")
                    await self.close_position(trade_id, current_price, timeout_reason)
                    continue

                # Sortie momentum faible (optionnelle)
                if self.config.ENABLE_MOMENTUM_EXIT:
                    should_exit_momentum, momentum_reason = await self.check_momentum_exit(trade, current_price, pnl_percent)
                    if should_exit_momentum:
                        self.logger.info(f"📉 {momentum_reason}")
                        await self.close_position(trade_id, current_price, "MOMENTUM_FAIBLE")
                        continue

                # Vérification Stop Loss
                if current_price <= trade.stop_loss:
                    await self.close_position(trade_id, current_price, "STOP_LOSS")
                    continue

                # Vérification Take Profit
                if current_price >= trade.take_profit:
                    await self.close_position(trade_id, current_price, "TAKE_PROFIT")
                    continue

                # Trailing Stop
                if current_price >= trade.trailing_stop:
                    # Mise à jour du trailing stop
                    new_stop = current_price * (1 - self.config.TRAILING_STEP_PERCENT / 100)
                    if new_stop > trade.stop_loss:
                        old_stop = trade.stop_loss
                        old_tp = trade.take_profit
                        
                        # Mise à jour du Stop Loss
                        trade.stop_loss = new_stop
                        
                        # Mise à jour du Take Profit pour qu'il suive la progression
                        # Nouveau TP = prix actuel + même écart relatif que le TP initial
                        new_take_profit = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
                        trade.take_profit = new_take_profit
                        
                        self.logger.info(f"📈 Trailing Stop mis à jour pour {trade.pair}:")
                        self.logger.info(f"   🛑 Nouveau SL: {new_stop:.4f} EUR (ancien: {old_stop:.4f})")
                        self.logger.info(f"   🎯 Nouveau TP: {new_take_profit:.4f} EUR (ancien: {old_tp:.4f})")

                        # Enregistrement en base de données
                        try:
                            trailing_data = {
                                'trade_id': trade.db_id,
                                'symbol': trade.pair,
                                'old_stop_loss': old_stop,
                                'new_stop_loss': new_stop,
                                'old_take_profit': old_tp,
                                'new_take_profit': new_take_profit,
                                'trigger_price': current_price,
                                'timestamp': datetime.now(),
                                'profit_percent': (current_price - trade.entry_price) / trade.entry_price * 100
                            }
                            await self.database.insert_trailing_stop(trailing_data)
                        except Exception as e:
                            self.logger.error(f"❌ Erreur enregistrement trailing stop: {e}")

            except Exception as e:
                self.logger.error(f"❌ Erreur gestion position {trade_id}: {e}")

    async def close_position(self, trade_id: str, exit_price: float, reason: str):
        """Ferme une position"""
        try:
            trade = self.open_positions[trade_id]
            symbol = trade.pair
            
            # Récupération de l'asset de base (ex: ETH pour ETHEUR)
            base_asset = symbol.replace('EUR', '')
            
            # Vérification du solde disponible
            available_balance = self.get_asset_balance(base_asset)
            quantity_to_sell = trade.size
            
            # Gestion du solde insuffisant avec tolérance
            tolerance = self.config.BALANCE_TOLERANCE  # Tolérance pour les erreurs d'arrondi
            if available_balance < (quantity_to_sell - tolerance):
                self.logger.warning(f"⚠️ Solde insuffisant pour {symbol}")
                self.logger.warning(f"   Solde disponible: {available_balance:.8f} {base_asset}")
                self.logger.warning(f"   Quantité à vendre: {quantity_to_sell:.8f} {base_asset}")
                self.logger.warning(f"   Différence: {quantity_to_sell - available_balance:.8f} {base_asset}")
                
                # Vérification si c'est une position fantôme
                if available_balance <= self.config.PHANTOM_POSITION_THRESHOLD:  # Pratiquement zéro
                    self.logger.error(f"❌ Position fantôme détectée pour {symbol}, nettoyage virtuel")
                    await self.close_position_virtually(symbol, exit_price, f"{reason}_PHANTOM")
                    return
                
                # Ajustement intelligent du solde
                usable_balance = available_balance * self.config.BALANCE_SAFETY_MARGIN  # Marge de sécurité
                if usable_balance > 0:
                    quantity_to_sell = self.round_quantity(symbol, usable_balance)
                    self.logger.info(f"🔧 Ajustement quantité de vente: {quantity_to_sell:.8f} {base_asset}")
                    
                    # Vérification que la quantité ajustée est valide
                    if quantity_to_sell <= 0:
                        self.logger.error(f"❌ Quantité ajustée invalide pour {symbol}, fermeture virtuelle")
                        await self.close_position_virtually(symbol, exit_price, f"{reason}_INVALID_QTY")
                        return
                else:
                    self.logger.error(f"❌ Aucun solde utilisable pour {symbol}, position fermée virtuellement")
                    await self.close_position_virtually(symbol, exit_price, f"{reason}_NO_BALANCE")
                    return
            
            # Validation finale de la quantité
            is_valid, validation_msg, adjusted_quantity = self.validate_order_quantity(symbol, quantity_to_sell, exit_price)
            
            if not is_valid:
                self.logger.warning(f"⚠️ Quantité de vente invalide: {validation_msg}")
                if adjusted_quantity > 0 and adjusted_quantity <= available_balance:
                    quantity_to_sell = adjusted_quantity
                    self.logger.info(f"🔧 Quantité de vente ajustée: {quantity_to_sell:.8f}")
                else:
                    self.logger.error(f"❌ Impossible de vendre {symbol}, fermeture virtuelle")
                    await self.close_position_virtually(symbol, exit_price, reason)
                    return
            
            # Passage de l'ordre de vente avec gestion d'erreur améliorée
            try:
                # Vérification finale avant l'ordre
                final_balance = self.get_asset_balance(base_asset)
                if final_balance < quantity_to_sell:
                    self.logger.warning(f"⚠️ Solde changé entre les vérifications pour {symbol}")
                    self.logger.warning(f"   Nouveau solde: {final_balance:.8f} {base_asset}")
                    quantity_to_sell = min(quantity_to_sell, final_balance * self.config.BALANCE_SAFETY_MARGIN)
                    quantity_to_sell = self.round_quantity(symbol, quantity_to_sell)
                
                if quantity_to_sell <= 0:
                    self.logger.error(f"❌ Quantité finale invalide pour {symbol}, fermeture virtuelle")
                    await self.close_position_virtually(symbol, exit_price, f"{reason}_FINAL_CHECK_FAILED")
                    return
                
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity_to_sell
                )
                
                self.logger.info(f"✅ Ordre de vente exécuté: {quantity_to_sell:.8f} {base_asset}")
                
            except BinanceAPIException as e:
                error_code = getattr(e, 'code', 'UNKNOWN')
                error_msg = str(e)
                
                if "insufficient balance" in error_msg.lower() or error_code == -2010:
                    self.logger.error(f"❌ Erreur solde insuffisant confirmée par Binance pour {symbol}")
                    self.logger.error(f"   Code erreur: {error_code}")
                    self.logger.error(f"   Message: {error_msg}")
                    
                    # Actualisation forcée des soldes après erreur
                    # Force une nouvelle lecture des soldes
                    time.sleep(1)  # Attente pour synchronisation Binance
                    
                    # Fermeture virtuelle avec détail de l'erreur
                    await self.close_position_virtually(symbol, exit_price, f"{reason}_BINANCE_INSUFFICIENT_BALANCE")
                    return
                elif "min notional" in error_msg.lower() or error_code == -1013:
                    self.logger.error(f"❌ Valeur notionnelle trop faible pour {symbol}")
                    self.logger.error(f"   Quantité: {quantity_to_sell:.8f}, Prix: {exit_price:.8f}")
                    self.logger.error(f"   Valeur: {quantity_to_sell * exit_price:.2f} EUR")
                    await self.close_position_virtually(symbol, exit_price, f"{reason}_MIN_NOTIONAL")
                    return
                else:
                    # Autres erreurs - on relance l'exception
                    self.logger.error(f"❌ Erreur inattendue lors de la vente {symbol}: {error_msg}")
                    raise e
            
            # Mise à jour du trade
            trade.status = TradeStatus.CLOSED
            trade.exit_price = exit_price
            trade.exit_timestamp = datetime.now()
            trade.duration = trade.exit_timestamp - trade.timestamp
            trade.exit_reason = reason
            
            # Calcul P&L
            pnl_amount = (exit_price - trade.entry_price) * trade.size
            pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
            trade.pnl = pnl_amount
            
            # Mise à jour des totaux
            self.current_capital += (trade.entry_price * trade.size) + pnl_amount
            self.daily_pnl += pnl_amount
            self.daily_trades += 1
            
            # Suppression de la position ouverte
            del self.open_positions[trade_id]
            
            # Logging
            pnl_symbol = "🚀" if pnl_amount > 0 else "📉"
            self.logger.info(f"{pnl_symbol} Trade fermé : {symbol} ({reason})")
            self.logger.info(f"   💰 Prix de sortie: {exit_price:.4f} EUR")
            self.logger.info(f"   📊 P&L: {pnl_amount:+.2f} EUR ({pnl_percent:+.2f}%)")
            self.logger.info(f"   ⏱️ Durée: {trade.duration}")
            total_capital = self.get_total_capital()
            daily_pnl_percent = self.daily_pnl / total_capital * 100
            self.logger.info(f"   🔄 Total journalier: {self.daily_pnl:+.2f} EUR ({daily_pnl_percent:+.2f}%)")
            
            # Notification Telegram
            total_capital = self.get_total_capital()
            await self.telegram_notifier.send_trade_close_notification(trade, pnl_amount, pnl_percent, self.daily_pnl, total_capital)
            
            # Log dans Google Sheets (si activé)
            if self.sheets_logger:
                capital_before_close = total_capital - pnl_amount  # Capital avant fermeture
                await self.sheets_logger.log_trade(trade, "CLOSE", capital_before_close, total_capital)
            
            # Mise à jour en base de données
            if trade.db_id:
                try:
                    exit_data = {
                        'exit_price': exit_price,
                        'exit_time': datetime.now(),
                        'exit_reason': reason,
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent
                    }
                    await self.database.update_trade_exit(trade.db_id, exit_data)
                    self.logger.info(f"📊 Trade mis à jour en base (ID: {trade.db_id})")
                except Exception as e:
                    self.logger.error(f"❌ Erreur mise à jour DB: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture position {trade_id}: {e}")
    
    async def close_position_virtually(self, trade_id: str, exit_price: float, reason: str):
        """Ferme une position virtuellement (sans ordre réel) en cas de problème"""
        try:
            trade = self.open_positions[trade_id]
            symbol = trade.pair
            
            self.logger.warning(f"🔄 Fermeture virtuelle de {symbol} à {exit_price:.4f} EUR")
            
            # Mise à jour du trade
            trade.status = TradeStatus.CLOSED
            trade.exit_price = exit_price
            trade.exit_timestamp = datetime.now()
            trade.duration = trade.exit_timestamp - trade.timestamp
            trade.exit_reason = f"{reason}_VIRTUAL"
            
            # Calcul P&L (peut être inexact à cause du solde insuffisant)
            pnl_amount = (exit_price - trade.entry_price) * trade.size
            pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
            trade.pnl = pnl_amount
            
            # Mise à jour des totaux (ajustement conservateur)
            self.current_capital += (trade.entry_price * trade.size) + pnl_amount
            self.daily_pnl += pnl_amount
            self.daily_trades += 1
            
            # Suppression de la position ouverte
            del self.open_positions[trade_id]
            
            # Logging spécial pour fermeture virtuelle
            pnl_symbol = "⚠️" 
            self.logger.warning(f"{pnl_symbol} Trade fermé virtuellement : {symbol} ({reason})")
            self.logger.warning(f"   💰 Prix de sortie: {exit_price:.4f} EUR")
            self.logger.warning(f"   📊 P&L théorique: {pnl_amount:+.2f} EUR ({pnl_percent:+.2f}%)")
            self.logger.warning(f"   ⏱️ Durée: {trade.duration}")
            self.logger.warning(f"   ⚠️ ATTENTION: Fermeture virtuelle - vérifiez manuellement")
            
            # Notification Telegram avec avertissement
            total_capital = self.get_total_capital()
            await self.telegram_notifier.send_trade_close_notification(
                trade, pnl_amount, pnl_percent, self.daily_pnl, total_capital
            )
            
            # Log dans Google Sheets (si activé) avec mention spéciale
            if self.sheets_logger:
                capital_before_virtual = total_capital - pnl_amount  # Capital avant fermeture virtuelle
                await self.sheets_logger.log_trade(trade, "CLOSE_VIRTUAL", capital_before_virtual, total_capital)
            
            # Mise à jour en base de données
            if trade.db_id:
                try:
                    exit_data = {
                        'exit_price': exit_price,
                        'exit_time': datetime.now(),
                        'exit_reason': f"{reason}_VIRTUAL",
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent
                    }
                    await self.database.update_trade_exit(trade.db_id, exit_data)
                    self.logger.info(f"📊 Trade virtuel mis à jour en base (ID: {trade.db_id})")
                except Exception as e:
                    self.logger.error(f"❌ Erreur mise à jour DB virtuelle: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture virtuelle {trade_id}: {e}")
    
    def should_stop_daily_trading(self) -> bool:
        """Vérifie si on doit arrêter le trading pour la journée"""
        total_capital = self.get_total_capital()
        daily_pnl_percent = self.daily_pnl / total_capital * 100
        
        # Objectif atteint
        if daily_pnl_percent >= self.config.DAILY_TARGET_PERCENT:
            self.daily_target_reached = True
            return True
        
        # Stop loss atteint
        if daily_pnl_percent <= -self.config.DAILY_STOP_LOSS_PERCENT:
            self.daily_stop_loss_hit = True
            return True
        
        return False

    async def handle_daily_stop(self):
        """Gère l'arrêt quotidien du bot"""
        self.logger.info("🛑 Conditions d'arrêt quotidien atteintes")
        
        # Fermeture des positions ouvertes
        for trade_id in list(self.open_positions.keys()):
            trade = self.open_positions[trade_id]
            ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
            current_price = float(ticker['price'])
            reason = "DAILY_TARGET" if self.daily_target_reached else "DAILY_STOP_LOSS"
            await self.close_position(trade_id, current_price, reason)
        
        # Notification finale
        status = "✅ Objectif atteint" if self.daily_target_reached else "🛑 Stop loss quotidien atteint"
        total_capital = self.get_total_capital()
        await self.telegram_notifier.send_daily_summary(
            status, self.daily_pnl, self.daily_trades, total_capital
        )
        
        # Log performance quotidienne (si activé)
        if self.sheets_logger:
            total_capital = self.get_total_capital()
            await self.sheets_logger.log_daily_performance(
                total_capital, self.daily_pnl, self.daily_trades, status
            )
        
        # Enregistrement des performances journalières en base de données
        await self.save_daily_performance()
        
        self.is_running = False
        self.logger.info("🟢 [STOPPED] Bot arrêté pour la journée")
    
    async def save_daily_performance(self):
        """Enregistre les performances journalières en base de données"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Calcul des métriques basé sur le capital total dynamique
            total_capital = self.get_total_capital()
            daily_pnl_percent = (self.daily_pnl / total_capital) * 100
            winning_trades = 0
            losing_trades = 0
            
            # Récupération des trades du jour depuis la base
            trades_today = await self.database.get_trades_history(limit=100)
            trades_today = [t for t in trades_today if t.get('entry_time', '').startswith(today)]
            
            for trade in trades_today:
                if trade.get('pnl_amount', 0) > 0:
                    winning_trades += 1
                elif trade.get('pnl_amount', 0) < 0:
                    losing_trades += 1
            
            total_trades = winning_trades + losing_trades
            win_rate = (winning_trades / max(total_trades, 1)) * 100
            
            # Données de performance
            perf_data = {
                'date': today,
                'start_capital': total_capital,  # Capital total dynamique
                'end_capital': total_capital,  # Capital total dynamique actuel
                'daily_pnl': self.daily_pnl,
                'daily_pnl_percent': daily_pnl_percent,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'max_drawdown': min(0, daily_pnl_percent),  # Approximation
                'status': 'COMPLETED'
            }
            
            await self.database.insert_daily_performance(perf_data)
            self.logger.info(f"📊 Performances journalières enregistrées en base")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur enregistrement performances journalières: {e}")
    
    async def save_realtime_metrics(self):
        """Enregistre les métriques en temps réel"""
        try:
            # Calcul du win rate actuel
            if self.daily_trades > 0:
                # Approximation basée sur le P&L positif
                win_rate = max(0, (self.daily_pnl / self.daily_trades) * 50)  # Approximation
            else:
                win_rate = 0
            
            metrics = {
                'timestamp': datetime.now(),
                'current_capital': self.get_total_capital(),  # Capital total dynamique
                'open_positions': len(self.open_positions),
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.get_total_capital() - self.start_capital,  # P&L total par rapport au capital initial EUR
                'win_rate': win_rate,
                'pairs_analyzed': [trade.pair for trade in self.open_positions.values()],
                'top_pair': list(self.open_positions.values())[0].pair if self.open_positions else None
            }
            
            await self.database.insert_realtime_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur enregistrement métriques temps réel: {e}")
    
    async def check_positions_consistency(self):
        """Vérifie la cohérence entre les positions en mémoire et les soldes Binance + gère la surexposition"""
        try:
            account_info = self.binance_client.get_account()
            balances = {b['asset']: float(b['free']) for b in account_info['balances']}
            total_capital = self.get_total_capital()
            max_exposure_per_asset = total_capital * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
            
            # 1. Vérification des incohérences de positions tracées
            if self.open_positions:
                inconsistent_positions = []
                for trade_id, trade in self.open_positions.items():
                    base_asset = trade.pair.replace('EUR', '')
                    available_balance = balances.get(base_asset, 0)
                    
                    # Vérification si le solde est cohérent avec la position
                    if available_balance < trade.size * 0.95:  # Tolérance de 5%
                        inconsistent_positions.append({
                            'trade_id': trade_id,
                            'symbol': trade.pair,
                            'expected': trade.size,
                            'actual': available_balance,
                            'difference': trade.size - available_balance
                        })
                
                if inconsistent_positions:
                    self.logger.warning(f"⚠️ {len(inconsistent_positions)} positions incohérentes détectées:")
                    for pos in inconsistent_positions:
                        self.logger.warning(f"   {pos['symbol']}: attendu {pos['expected']:.8f}, réel {pos['actual']:.8f} (diff: {pos['difference']:.8f})")
            
            # 2. VÉRIFICATION CRITIQUE : Surexposition sur soldes existants
            overexposed_assets = []
            for asset, balance in balances.items():
                if asset == 'EUR' or balance <= 0.00001:
                    continue
                    
                try:
                    # Calcul exposition actuelle de cet asset
                    current_exposure = self.get_asset_exposure(asset)
                    
                    if current_exposure > max_exposure_per_asset:
                        overexposed_assets.append({
                            'asset': asset,
                            'current_exposure': current_exposure,
                            'max_allowed': max_exposure_per_asset,
                            'excess_eur': current_exposure - max_exposure_per_asset,
                            'balance': balance
                        })
                        
                except Exception as e:
                    self.logger.debug(f"⚠️ Impossible de vérifier exposition {asset}: {e}")
                    continue
            
            # 3. CORRECTION AUTOMATIQUE des surexpositions
            if overexposed_assets:
                self.logger.warning(f"🚨 SUREXPOSITION DÉTECTÉE sur {len(overexposed_assets)} asset(s)!")
                
                for asset_info in overexposed_assets:
                    asset = asset_info['asset']
                    excess_eur = asset_info['excess_eur']
                    current_exposure = asset_info['current_exposure']
                    max_allowed = asset_info['max_allowed']
                    
                    self.logger.warning(f"   🔥 {asset}: {current_exposure:.2f} EUR > {max_allowed:.2f} EUR (excès: {excess_eur:.2f} EUR)")
                    
                    # Calculer quelle quantité vendre pour revenir dans la limite
                    try:
                        symbol = asset + 'EUR'
                        ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        
                        # Quantité à vendre = excès en EUR / prix actuel
                        quantity_to_sell = excess_eur / current_price
                        balance = asset_info['balance']
                        
                        # Ne pas vendre plus que ce qu'on a
                        if quantity_to_sell > balance:
                            quantity_to_sell = balance * 0.95  # Marge de sécurité
                        
                        # Arrondir selon les règles de la paire
                        quantity_to_sell = self.round_quantity(symbol, quantity_to_sell)
                        
                        if quantity_to_sell > 0:
                            self.logger.warning(f"   🔧 VENTE FORCÉE {asset}: {quantity_to_sell:.8f} ({quantity_to_sell * current_price:.2f} EUR)")
                            
                            # Exécuter la vente d'urgence
                            try:
                                order = self.binance_client.order_market_sell(
                                    symbol=symbol,
                                    quantity=quantity_to_sell
                                )
                                
                                self.logger.info(f"✅ SUREXPOSITION CORRIGÉE: Vendu {quantity_to_sell:.8f} {asset} pour {quantity_to_sell * current_price:.2f} EUR")
                                
                                # Notification Telegram d'urgence
                                message = f"🚨 CORRECTION SUREXPOSITION\n"
                                message += f"Asset: {asset}\n"
                                message += f"Vendu: {quantity_to_sell:.8f} ({quantity_to_sell * current_price:.2f} EUR)\n"
                                message += f"Exposition avant: {current_exposure:.2f} EUR\n"
                                message += f"Limite: {max_allowed:.2f} EUR"
                                
                                await self.telegram_notifier.send_message(message)
                                
                            except Exception as e:
                                self.logger.error(f"❌ ÉCHEC vente forcée {asset}: {e}")
                                
                    except Exception as e:
                        self.logger.error(f"❌ Erreur calcul vente forcée {asset}: {e}")
            
            # 4. Détection de soldes non tracés (positions fantômes inverses)
            for asset, balance in balances.items():
                if asset == 'EUR' or balance <= 0.001:
                    continue
                    
                # Vérifier si on a un solde significatif sans position tracée
                has_tracked_position = any(trade.pair.replace('EUR', '') == asset for trade in self.open_positions.values())
                
                if not has_tracked_position and balance > 0.001:
                    try:
                        symbol = asset + 'EUR'
                        ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        value_eur = balance * current_price
                        
                        if value_eur > 100:  # Seuil significatif
                            self.logger.warning(f"⚠️ Incohérence détectée: {asset} balance={balance:.6f} mais 0 positions en mémoire")
                            
                    except Exception:
                        pass
                        
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification cohérence positions: {e}")

    def calculate_volatility_1h(self, symbol: str) -> float:
        """
        Calcule la volatilité sur les 12 dernières heures pour une paire.
        Méthode : variation max-min sur prix moyen (en %).
        """
        try:
            # Récupérer les données horaires (sur 12 heures pour une meilleure moyenne)
            klines = self.binance_client.get_historical_klines(
                symbol, "1h", "12 hours ago UTC"
            )

            if len(klines) < 2:
                return 0.0

            # Extraire les prix de clôture
            prices = [float(kline[4]) for kline in klines]

            if len(prices) >= 2:
                max_price = max(prices)
                min_price = min(prices)
                avg_price = sum(prices) / len(prices)

                if avg_price > 0:
                    volatility = ((max_price - min_price) / avg_price) * 100
                    self.logger.debug(f"📊 Volatilité 12h {symbol}: {volatility:.2f}%")
                    return volatility
                else:
                    return 0.0

            return 0.0

        except Exception as e:
            self.logger.error(f"❌ Erreur calcul volatilité 12h {symbol}: {e}")
            return 0.0

    def count_trades_per_pair(self, symbol: str) -> int:
        """Compte le nombre de trades ouverts pour une paire - VÉRIFICATION RENFORCÉE"""
        # Comptage en mémoire par symbole
        memory_count = len([trade for trade_id, trade in self.open_positions.items() 
                           if trade.pair == symbol])
        
        # Vérification supplémentaire via solde Binance
        try:
            base_asset = symbol.replace('EUR', '')
            binance_balance = self.get_asset_balance(base_asset)
            
            # Si on a un solde significatif mais pas de position en mémoire = incohérence
            if binance_balance > 0.001 and memory_count == 0:
                self.logger.warning(f"⚠️ Incohérence détectée: {base_asset} balance={binance_balance:.6f} mais 0 positions en mémoire")
                # Considérer qu'on a déjà une position pour éviter la surexposition
                return 1
            
            return memory_count
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification solde {symbol}: {e}")
            # En cas d'erreur, on est conservateur et on suppose qu'on a déjà des positions
            return max(memory_count, 1)  # Au minimum 1 pour éviter le sur-trading

    def can_open_position_enhanced(self, symbol: str, volatility: float) -> tuple[bool, str]:
        """Vérifie si on peut ouvrir une position selon les nouvelles règles"""
        # 1. Vérifier limite trades par paire - STRICT
        current_trades = self.count_trades_per_pair(symbol)
        if current_trades >= self.config.MAX_TRADES_PER_PAIR:
            return False, f"Limite trades par paire atteinte ({current_trades}/{self.config.MAX_TRADES_PER_PAIR})"
        
        # 2. Vérifier volatilité minimum
        if volatility < self.config.MIN_VOLATILITY_1H_PERCENT:
            return False, f"Volatilité insuffisante ({volatility:.2f}% < {self.config.MIN_VOLATILITY_1H_PERCENT}%)"
        
        # 3. Vérifier nombre total de positions
        total_open_positions = len(self.open_positions)
        if total_open_positions >= self.config.MAX_OPEN_POSITIONS:
            return False, f"Limite positions totales atteinte ({total_open_positions}/{self.config.MAX_OPEN_POSITIONS})"
        
        # 4. VÉRIFICATION EXPOSITION : Contrôler AVANT + APRÈS la nouvelle position
        base_asset = symbol.replace('EUR', '')
        current_exposure = self.get_asset_exposure(base_asset)
        total_capital = self.get_total_capital()
        max_exposure_per_asset = total_capital * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
        
        # Calcul de la nouvelle exposition après ajout de la position
        new_position_size = self.calculate_position_size(symbol, volatility)
        future_exposure = current_exposure + new_position_size
        
        if current_exposure > max_exposure_per_asset:
            return False, f"Exposition {base_asset} déjà trop élevée ({current_exposure:.2f} EUR > {max_exposure_per_asset:.2f} EUR = {self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)"
        
        if future_exposure > max_exposure_per_asset:
            return False, f"Nouvelle position créerait surexposition {base_asset} ({current_exposure:.2f} + {new_position_size:.2f} = {future_exposure:.2f} EUR > {max_exposure_per_asset:.2f} EUR = {self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)"
        
        # 5. VÉRIFICATION CAPITAL : Capital EUR minimum disponible avec marge
        eur_balance = self.get_asset_balance('EUR')
        if eur_balance < new_position_size * 1.1:  # Marge de sécurité 10%
            return False, f"Capital EUR insuffisant ({eur_balance:.2f} < {new_position_size * 1.1:.2f} EUR requis)"
        
        return True, "OK"

    def should_timeout_position(self, trade: Trade, current_price: float, volatility: float) -> tuple[bool, str]:
        """Détermine si une position doit être fermée par timeout selon les nouveaux critères"""
        # Calcul durée et P&L
        duration_minutes = (datetime.now() - trade.timestamp).total_seconds() / 60
        pnl_percent = (current_price - trade.entry_price) / trade.entry_price * 100
        
        # Déterminer timeout selon volatilité
        timeout_threshold = self.config.TRADE_TIMEOUT_LOW_VOLATILITY if volatility < 2.0 else self.config.TRADE_TIMEOUT_HIGH_VOLATILITY
        
        # Vérifier conditions de timeout
        if duration_minutes > timeout_threshold:
            # P&L dans la zone de timeout
            min_range, max_range = self.config.MIN_TIMEOUT_PROFIT_RANGE
            if min_range <= pnl_percent <= max_range:
                # TODO: Vérifier indicateurs techniques (MACD, RSI neutres)
                return True, f"TIMEOUT_ADAPTATIF ({duration_minutes:.0f}min, P&L:{pnl_percent:+.2f}%)"
        
        return False, ""

    async def check_momentum_exit(self, trade: Trade, current_price: float, pnl_percent: float) -> tuple[bool, str]:
        """Vérifie si on doit sortir pour faiblesse du momentum"""
        try:
            # Vérifier si P&L dans la zone de momentum faible
            min_range, max_range = self.config.MOMENTUM_PNL_RANGE
            if not (min_range <= pnl_percent <= max_range):
                return False, ""  # P&L en dehors de la zone de momentum faible
            
            # Récupération des données techniques
            klines = self.binance_client.get_klines(
                symbol=trade.pair,
                interval=getattr(Client, f'KLINE_INTERVAL_{self.config.TIMEFRAME}'),
                limit=50
            )
            
            if len(klines) < 30:
                return False, ""
            
            # Préparation des données
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades_count', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Calcul RSI
            rsi = talib.RSI(df['close'], timeperiod=self.config.RSI_PERIOD) # type: ignore
            if np.isnan(rsi.iloc[-1]):
                return False, ""
            
            # Calcul MACD
            macd, macdsignal, macdhist = talib.MACD(df['close']) # type: ignore
            if np.isnan(macdhist.iloc[-1]):
                return False, ""
            
            # Conditions de sortie momentum faible
            rsi_condition = rsi.iloc[-1] < self.config.MOMENTUM_RSI_THRESHOLD
            macd_condition = macdhist.iloc[-1] < 0 if self.config.MOMENTUM_MACD_NEGATIVE else True
            
            if rsi_condition and macd_condition:
                reason = f"Momentum faible détecté (RSI:{rsi.iloc[-1]:.1f}, MACD_hist:{macdhist.iloc[-1]:.6f}, P&L:{pnl_percent:+.2f}%)"
                return True, reason
            
            return False, ""
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification momentum {trade.pair}: {e}")
            return False, ""

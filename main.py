"""
Bot de Trading Scalping Automatisé - CAPITAL DYNAMIQUE USDC
Stratégie multi-paires USDC avec gestion avancée des risques et liquidité maximale
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
from config import API_CONFIG, BLACKLISTED_PAIRS, TradingConfig
from trading_hours import (get_current_trading_session, get_hours_status_message,
                           get_trading_intensity, is_trading_hours_active)
from utils.database import TradingDatabase
from utils.enhanced_sheets_logger import EnhancedSheetsLogger
from utils.firebase_logger import firebase_logger  # type: ignore
from utils.logger import setup_logger
from utils.risk_manager import RiskManager
from utils.technical_indicators import TechnicalAnalyzer
from utils.telegram_notifier import TelegramNotifier
from utils.trading_hours_notifier import TradingHoursNotifier  # type: ignore


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
    capital_before: Optional[float] = None  # AJOUTÉ: Capital avant le trade
    capital_after: Optional[float] = None   # AJOUTÉ: Capital après le trade
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
        
        # Initialize trading hours notifier
        self.hours_notifier = TradingHoursNotifier(
            self.telegram_notifier,
            self.config
        )
        
        # Initialize Google Sheets optionally
        if API_CONFIG.ENABLE_GOOGLE_SHEETS:
            try:
                self.sheets_logger = EnhancedSheetsLogger(
                    API_CONFIG.GOOGLE_SHEETS_CREDENTIALS, 
                    API_CONFIG.GOOGLE_SHEETS_SPREADSHEET_ID
                )
                logging.info(f"📊 Enhanced Google Sheets activé - ID: {API_CONFIG.GOOGLE_SHEETS_SPREADSHEET_ID}")
            except Exception as e:
                logging.error(f"❌ Erreur Enhanced Google Sheets: {e}")
                self.sheets_logger = None
        else:
            self.sheets_logger = None
            logging.info("📊 Google Sheets désactivé")
        
        # Firebase Logger
        self.firebase_logger = firebase_logger
        if firebase_logger.firebase_initialized:
            logging.info("🔥 Firebase Logger activé pour analytics temps réel")
        else:
            logging.info("🔥 Firebase Logger désactivé")
        
        # Bot state
        self.is_running = False
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.open_positions: Dict[str, Trade] = {}  # Une position par ID unique
        self.start_capital = 0.0
        self.current_capital = 0.0
        
        # Anti-fragmentation tracking
        self.last_trade_time: Dict[str, datetime] = {}  # Derniers trades par paire
        self.daily_target_reached = False
        self.daily_stop_loss_hit = False
        
        # OPTIMISÉ: Suivi des nouvelles protections
        self.trades_per_hour: List[datetime] = []  # Historique des trades par heure
        self.consecutive_losses = 0  # Compteur pertes consécutives
        self.last_trade_results: List[bool] = []  # Historique résultats (True=profit, False=perte)
        self.consecutive_loss_pause_until: Optional[datetime] = None  # Pause jusqu'à cette datetime
        
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
        
        # 🔥 Chargement des positions sauvegardées depuis Firebase
        await self.load_open_positions_from_db()
        
        # Nettoyage des positions fantômes
        await self.cleanup_phantom_positions()
        
        # Initialisation du capital
        await self.initialize_capital()
        
        # Notification de démarrage
        await self.telegram_notifier.send_start_notification(self.start_capital)
        
        # 🔥 LOG FIREBASE: Démarrage du bot
        self.firebase_logger.log_message(
            level="INFO",
            message=f"Bot démarré avec capital: {self.start_capital:.2f} USDC",
            module="main",
            capital=self.start_capital,
            additional_data={
                'session_start': True,
                'config_version': 'v3.0_enhanced',
                'max_positions': self.config.MAX_OPEN_POSITIONS,
                'base_position_size': self.config.BASE_POSITION_SIZE_PERCENT
            }
        )
        
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
                base_asset = symbol.replace('USDC', '')
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

    async def save_open_positions_to_db(self):
        """Sauvegarde les positions ouvertes en Firebase pour persistance"""
        try:
            if not self.open_positions:
                return
            
            if not self.firebase_logger or not self.firebase_logger.firebase_initialized or not self.firebase_logger.firestore_db:
                self.logger.warning("🔥 Firebase Firestore non disponible pour sauvegarde positions")
                return
            
            for trade_id, trade in self.open_positions.items():
                try:
                    position_data = {
                        'trade_id': trade_id,
                        'pair': trade.pair,
                        'entry_price': trade.entry_price,
                        'stop_loss': trade.stop_loss,
                        'take_profit': trade.take_profit,
                        'size': trade.size,
                        'timestamp': trade.timestamp.isoformat(),
                        'trailing_stop': getattr(trade, 'trailing_stop', 0),
                        'direction': trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction),
                        'saved_at': datetime.now().isoformat(),
                        'session_id': self.firebase_logger.session_id
                    }
                    
                    # Sauvegarde en Firebase Firestore
                    self.firebase_logger.firestore_db.collection('position_states').document(trade_id).set(position_data)
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur sauvegarde position Firebase {trade_id}: {e}")
                    
            self.logger.debug(f"� {len(self.open_positions)} positions sauvegardées en Firebase")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde positions Firebase: {e}")

    async def load_open_positions_from_db(self):
        """Charge les positions ouvertes depuis Firebase au démarrage"""
        try:
            if not self.firebase_logger or not self.firebase_logger.firebase_initialized or not self.firebase_logger.firestore_db:
                self.logger.warning("🔥 Firebase Firestore non disponible pour chargement positions")
                return
            
            # Récupération des positions depuis Firestore
            positions_ref = self.firebase_logger.firestore_db.collection('position_states')
            saved_positions_docs = positions_ref.get()
            
            if not saved_positions_docs:
                self.logger.info("📂 Aucune position sauvegardée trouvée en Firebase")
                return
            
            saved_positions = []
            for doc in saved_positions_docs:
                saved_positions.append(doc.to_dict())
            
            if not saved_positions:
                self.logger.info("📂 Aucune position sauvegardée trouvée en Firebase")
                return
            
            positions_restored = 0
            
            for position_data in saved_positions:
                try:
                    trade_id = position_data['trade_id']
                    pair = position_data['pair']
                    
                    # Vérifier que le solde existe toujours sur Binance
                    base_asset = pair.replace('USDC', '')
                    available_balance = self.get_asset_balance(base_asset)
                    
                    # Seulement restaurer si on a encore le solde
                    if available_balance >= float(position_data['size']) * 0.95:  # Tolérance 5%
                        
                        # Recréer l'objet Trade (classes déjà définies dans ce fichier)
                        trade = Trade(
                            id=position_data['trade_id'],
                            pair=pair,
                            direction=TradeDirection(position_data['direction']),
                            size=float(position_data['size']),
                            entry_price=float(position_data['entry_price']),
                            stop_loss=float(position_data['stop_loss']),
                            take_profit=float(position_data['take_profit']),
                            trailing_stop=float(position_data.get('trailing_stop', 0)),
                            timestamp=datetime.fromisoformat(position_data['timestamp'])
                        )
                        
                        # S'assurer que le statut est OPEN
                        trade.status = TradeStatus.OPEN
                        
                        # Restaurer dans open_positions
                        self.open_positions[trade_id] = trade
                        positions_restored += 1
                        
                        self.logger.info(f"📂 Position restaurée depuis Firebase: {pair}")
                        self.logger.info(f"   💰 Prix entrée: {trade.entry_price:.4f}")
                        self.logger.info(f"   🛑 Stop Loss: {trade.stop_loss:.4f}")
                        self.logger.info(f"   🎯 Take Profit: {trade.take_profit:.4f}")
                        
                    else:
                        self.logger.warning(f"⚠️ Position {pair} ignorée - solde insuffisant")
                        # Nettoyer cette position obsolète de Firebase
                        if self.firebase_logger.firestore_db:
                            self.firebase_logger.firestore_db.collection('position_states').document(trade_id).delete()
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur restauration position Firebase {position_data.get('trade_id', 'unknown')}: {e}")
            
            if positions_restored > 0:
                self.logger.info(f"✅ {positions_restored} position(s) restaurée(s) avec SL/TP depuis Firebase")
                
                # Firebase logging pour restauration
                if self.firebase_logger:
                    self.firebase_logger.log_message(
                        level="INFO",
                        message=f"POSITIONS RESTAURÉES FIREBASE: {positions_restored} positions avec SL/TP intacts",
                        module="firebase_persistence",
                        additional_data={
                            'positions_restored': positions_restored,
                            'total_saved': len(saved_positions)
                        }
                    )
            else:
                self.logger.info("📂 Aucune position à restaurer depuis Firebase")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement positions Firebase: {e}")

    async def initialize_capital(self):
        """Initialise le capital à partir de l'API Binance (USDC + valeur crypto)"""
        try:
            account_info = self.binance_client.get_account()
            usdc_balance = 0.0
            crypto_value = 0.0
            significant_balances = []
            self.logger.info("💰 Soldes disponibles:")
            for balance in account_info['balances']:
                free_balance = float(balance['free'])
                asset = balance['asset']
                if free_balance > 0:
                    if asset == 'USDC':
                        usdc_balance = free_balance
                        self.logger.info(f"   💶 {asset}: {free_balance:.2f}")
                    elif free_balance > 0.001:
                        # Conversion en USDC pour le capital initial
                        try:
                            symbol = asset + 'USDC'
                            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                            price_usdc = float(ticker['price'])
                            value_usdc = free_balance * price_usdc
                            crypto_value += value_usdc
                            significant_balances.append(f"{asset}: {free_balance:.8f} ({value_usdc:.2f} USDC)")
                        except Exception:
                            significant_balances.append(f"{asset}: {free_balance:.8f}")
            if significant_balances:
                self.logger.info(f"   🪙 Autres: {', '.join(significant_balances[:5])}")
            if usdc_balance == 0.0 and crypto_value == 0.0:
                raise ValueError("Aucun solde USDC ou crypto trouvé dans le compte")
            total_capital = usdc_balance + crypto_value
            self.start_capital = total_capital
            self.current_capital = total_capital
            self.logger.info(f"💰 Capital initial total: {self.start_capital:.2f} USDC (USDC: {usdc_balance:.2f}, Crypto: {crypto_value:.2f})")
            self.logger.info(f"📊 Taille de position configurée: {self.config.BASE_POSITION_SIZE_PERCENT}% = {self.calculate_position_size():.2f} USDC")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation capital: {e}")
            raise

    async def main_loop(self):
        """Boucle principale du bot"""
        while self.is_running:
            try:
                # Vérification et notification des changements d'horaires
                await self.hours_notifier.check_and_notify_schedule_changes()
                
                # Vérification des horaires de trading
                if not is_trading_hours_active(self.config):
                    hours_status = get_hours_status_message(self.config)
                    self.logger.info(f"⏰ {hours_status}")
                    
                    # 🔥 LOG FIREBASE: Statut hors horaires
                    if self.firebase_logger:
                        self.firebase_logger.log_message(
                            level="INFO",
                            message=hours_status,
                            module="trading_hours",
                            capital=self.get_total_capital(),
                            additional_data={'trading_active': False, 'positions_open': len(self.open_positions)}
                        )
                    
                    await asyncio.sleep(300)  # Attendre 5 minutes si hors horaires
                    continue
                
                # Vérification des conditions d'arrêt quotidien
                if self.should_stop_daily_trading():
                    await self.handle_daily_stop()
                    break
                
                # OPTIMISÉ: Vérification pause après pertes consécutives
                if self.consecutive_loss_pause_until:
                    now = datetime.now()
                    if now < self.consecutive_loss_pause_until:
                        remaining_minutes = (self.consecutive_loss_pause_until - now).total_seconds() / 60
                        self.logger.info(f"⏸️ En pause de sécurité - Reprise dans {remaining_minutes:.0f} minutes")
                        await asyncio.sleep(60)  # Vérifier toutes les minutes
                        continue
                    else:
                        # Fin de pause - RÉINITIALISER COMPLÈTEMENT
                        self.logger.info(f"✅ FIN DE PAUSE: Reprise du trading normal")
                        self.consecutive_loss_pause_until = None
                        
                        # 🔥 RÉINITIALISATION COMPLÈTE DU COMPTEUR
                        old_consecutive_losses = self.consecutive_losses
                        self.consecutive_losses = 0
                        self.last_trade_results = []  # Reset de l'historique des résultats
                        
                        self.logger.info(f"🔄 COMPTEURS RÉINITIALISÉS:")
                        self.logger.info(f"   Pertes consécutives: {old_consecutive_losses} → {self.consecutive_losses}")
                        self.logger.info(f"   Historique résultats: Reset complet")
                        
                        # Notification Telegram de reprise avec détails
                        message = f"✅ REPRISE DU TRADING\n"
                        message += f"Fin de la pause de sécurité\n"
                        message += f"Compteurs réinitialisés: {old_consecutive_losses} → 0 pertes\n"
                        message += f"Le bot reprend ses activités normalement"
                        await self.telegram_notifier.send_message(message)
                        
                        # Firebase logging pour reprise
                        if self.firebase_logger:
                            self.firebase_logger.log_message(
                                level="INFO",
                                message=f"✅ REPRISE TRADING: Compteurs réinitialisés ({old_consecutive_losses} → 0)",
                                module="risk_management",
                                additional_data={
                                    'old_consecutive_losses': old_consecutive_losses,
                                    'new_consecutive_losses': 0,
                                    'pause_completed': True,
                                    'counters_reset': True
                                }
                            )
                
                # Affichage status horaires
                hours_status = get_hours_status_message(self.config)
                self.logger.info(f"⏰ {hours_status}")
                
                # Scan des paires USDC
                top_pairs = await self.scan_usdc_pairs()
                
                # Recherche de signaux
                for pair_info in top_pairs:
                    if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS:
                        break
                    
                    signal = await self.analyze_pair(pair_info.pair)
                    if signal:
                        await self.execute_trade(pair_info.pair, signal)
                
                # Gestion des positions ouvertes avec surveillance fréquente
                if len(self.open_positions) > 0:
                    # Surveillance rapide toutes les 5 secondes si positions ouvertes
                    await self.manage_open_positions()
                    
                    # Surveillance intensive pour positions à risque
                    await self.intensive_position_monitoring()
                else:
                    # Surveillance normale si pas de positions
                    await self.manage_open_positions()
                
                # Enregistrement périodique des métriques (toutes les 10 itérations)
                self.metrics_counter += 1
                if self.metrics_counter % 10 == 0:
                    await self.save_realtime_metrics()
                    
                    # Log Firebase pour métriques temps réel
                    if self.firebase_logger:
                        try:
                            total_capital = self.get_total_capital()
                            
                            # Log métriques importantes avec log_metric
                            self.firebase_logger.log_metric("total_capital", total_capital)
                            self.firebase_logger.log_metric("daily_pnl", self.daily_pnl)
                            self.firebase_logger.log_metric("open_positions", len(self.open_positions))
                            self.firebase_logger.log_metric("daily_trades", self.daily_trades)
                            
                        except Exception as e:
                            self.logger.error(f"❌ Erreur Firebase metrics: {e}")
                
                # Vérification de cohérence des positions (toutes les 50 itérations)
                if self.metrics_counter % 50 == 0:
                    await self.check_positions_consistency()
                
                # 🧹 Nettoyage automatique des miettes (toutes les 100 itérations)
                if self.metrics_counter % 100 == 0:
                    await self.convert_dust_to_bnb_if_needed()
                
                # Vérification de la volatilité du marché (toutes les 30 itérations)
                if self.metrics_counter % 30 == 0:
                    await self.check_market_volatility(top_pairs)
                
                # Pause avant le prochain scan
                if len(self.open_positions) > 0:
                    # Scan plus fréquent avec positions ouvertes (5s au lieu de 60s)
                    await asyncio.sleep(5)
                else:
                    # Scan normal sans positions
                    await asyncio.sleep(self.config.SCAN_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans la boucle principale: {e}")
                
                # Log Firebase pour erreurs critiques
                if self.firebase_logger:
                    try:
                        self.firebase_logger.log_message(
                            level="ERROR",
                            message=f"Erreur boucle principale: {str(e)}",
                            module="main_loop",
                            additional_data={'error_type': type(e).__name__}
                        )
                    except Exception:
                        pass  # Éviter les boucles d'erreur
                
                await asyncio.sleep(5)

    async def scan_usdc_pairs(self) -> List[PairScore]:
        """Scanne et classe les paires USDC par score avec logging détaillé des décisions pour Firebase"""
        try:
            self.logger.info("🔎 Scan des paires USDC en cours...")
            
            # Récupération des tickers avec gestion d'erreur améliorée
            try:
                # Essayer d'abord get_ticker() standard
                tickers = self.binance_client.get_ticker()
                if not tickers:
                    # Fallback sur 24hr ticker statistics
                    tickers = self.binance_client.get_24hr_ticker()
                
                usdc_pairs = [t for t in tickers if t['symbol'].endswith('USDC')]
                
                if not usdc_pairs:
                    self.logger.warning("⚠️ Aucune paire USDC trouvée")
                    return []
                    
                self.logger.info(f"📊 {len(usdc_pairs)} paires USDC trouvées")
                
            except Exception as e:
                self.logger.error(f"❌ Erreur récupération tickers: {e}")
                return []
            
            pair_scores = []
            exclusion_stats = {
                'blacklisted': 0,
                'low_volume': 0,
                'high_spread': 0,
                'low_volatility': 0,
                'total_analyzed': len(usdc_pairs)
            }
            excluded_pairs = {
                'blacklisted': [],
                'low_volume': [],
                'high_spread': [],
                'low_volatility': []
            }
            
            # 📊 Liste pour stocker toutes les décisions détaillées
            detailed_decisions = []
            
            for ticker in usdc_pairs:
                try:
                    symbol = ticker['symbol']
                    
                    # Gestion robuste des différentes clés de prix possibles
                    current_price = None
                    if 'lastPrice' in ticker:
                        current_price = float(ticker['lastPrice'])
                    elif 'price' in ticker:
                        current_price = float(ticker['price'])
                    elif 'close' in ticker:
                        current_price = float(ticker['close'])
                    else:
                        self.logger.warning(f"⚠️ Prix non trouvé pour {symbol}, structure: {list(ticker.keys())}")
                        continue
                    
                    # Gestion robuste des autres champs
                    volume_usdc = float(ticker.get('quoteVolume', ticker.get('volume', 0)))
                    bid = float(ticker.get('bidPrice', ticker.get('bid', current_price * 0.999)))
                    ask = float(ticker.get('askPrice', ticker.get('ask', current_price * 1.001)))
                    spread = (ask - bid) / bid * 100 if bid > 0 else 0
                    price_change = abs(float(ticker.get('priceChangePercent', ticker.get('priceChange', 0))))
                    volatility_1h = self.calculate_volatility_1h(symbol)
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur parsing ticker {ticker.get('symbol', 'UNKNOWN')}: {e}")
                    continue
                
                # 📊 Structure détaillée de la décision
                decision = {
                    "timestamp": datetime.now().isoformat(),
                    "pair": symbol,
                    "price": current_price,
                    "volume_24h": volume_usdc,
                    "spread_pct": spread,
                    "volatility_1h_pct": volatility_1h,
                    "volatility_24h_pct": price_change,
                    "signal_score": 0,  # Sera calculé plus tard si validé
                    "conditions": {
                        "blacklisted": symbol in BLACKLISTED_PAIRS,
                        "volume_ok": volume_usdc >= self.config.MIN_VOLUME_USDC,
                        "spread_ok": spread <= self.config.MAX_SPREAD_PERCENT,
                        "volatility_ok": volatility_1h >= self.config.MIN_VOLATILITY_1H_PERCENT,
                        "signal_score_ok": False,  # Sera vérifié plus tard
                        "breaking_high": False  # Sera vérifié plus tard
                    },
                    "final_decision": "PENDING",
                    "reason": ""
                }

                # Exclusion des paires blacklistées
                if symbol in BLACKLISTED_PAIRS:
                    exclusion_stats['blacklisted'] += 1
                    excluded_pairs['blacklisted'].append(symbol)
                    decision["final_decision"] = "REJECTED"
                    decision["reason"] = "Blacklisted pair"
                    detailed_decisions.append(decision)
                    continue
                
                # Vérification volume minimum
                if volume_usdc < self.config.MIN_VOLUME_USDC:
                    exclusion_stats['low_volume'] += 1
                    excluded_pairs['low_volume'].append(f"{symbol}({volume_usdc/1000000:.1f}M)")
                    decision["final_decision"] = "REJECTED"
                    decision["reason"] = f"Volume < {self.config.MIN_VOLUME_USDC/1000000:.0f}M ({volume_usdc/1000000:.1f}M)"
                    detailed_decisions.append(decision)
                    continue
                
                # Vérification spread
                if spread > self.config.MAX_SPREAD_PERCENT:
                    exclusion_stats['high_spread'] += 1
                    excluded_pairs['high_spread'].append(f"{symbol}({spread:.2f}%)")
                    decision["final_decision"] = "REJECTED"
                    decision["reason"] = f"Spread > {self.config.MAX_SPREAD_PERCENT}% ({spread:.2f}%)"
                    detailed_decisions.append(decision)
                    continue
                
                # Vérification volatilité horaire
                if volatility_1h < self.config.MIN_VOLATILITY_1H_PERCENT:
                    exclusion_stats['low_volatility'] += 1
                    excluded_pairs['low_volatility'].append(f"{symbol}({volatility_1h:.1f}%)")
                    decision["final_decision"] = "REJECTED"
                    decision["reason"] = f"Volatility 1h < {self.config.MIN_VOLATILITY_1H_PERCENT}% ({volatility_1h:.1f}%)"
                    detailed_decisions.append(decision)
                    continue
                
                # ✅ Paire validée pour les critères de base - analyser les signaux
                try:
                    # Analyse technique pour calculer le score
                    klines = self.binance_client.get_klines(
                        symbol=symbol,
                        interval=getattr(Client, f'KLINE_INTERVAL_{self.config.TIMEFRAME}'),
                        limit=100
                    )
                    
                    if len(klines) >= 50:
                        df = pd.DataFrame(klines, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_volume', 'trades_count', 'taker_buy_base', 'taker_buy_quote', 'ignore'
                        ])
                        
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = df[col].astype(float)
                        
                        analysis = self.technical_analyzer.analyze_pair(df, symbol)
                        decision["signal_score"] = analysis.total_score
                        decision["conditions"]["signal_score_ok"] = len(analysis.signals) >= self.config.MIN_SIGNAL_CONDITIONS
                        
                        # Vérification cassure si activée
                        if self.config.ENABLE_BREAKOUT_CONFIRMATION:
                            breaking_high = self.check_breakout_confirmation(symbol, current_price)
                            decision["conditions"]["breaking_high"] = breaking_high
                        else:
                            decision["conditions"]["breaking_high"] = True
                        
                        # Décision finale
                        if decision["conditions"]["signal_score_ok"] and decision["conditions"]["breaking_high"]:
                            decision["final_decision"] = "VALIDATED"
                            decision["reason"] = f"All filters passed ✅ (Score: {analysis.total_score:.1f}, Signals: {len(analysis.signals)})"
                            
                            # Ajouter à la liste des paires validées
                            atr = await self.calculate_atr(symbol)
                            score = (0.6 * price_change + 0.4 * (volume_usdc / 1000000))
                            
                            pair_scores.append(PairScore(
                                pair=symbol,
                                volatility=price_change,
                                volume=volume_usdc,
                                score=score,
                                spread=spread,
                                atr=atr
                            ))
                        else:
                            decision["final_decision"] = "REJECTED"
                            reasons = []
                            if not decision["conditions"]["signal_score_ok"]:
                                reasons.append(f"Signal score < {self.config.MIN_SIGNAL_CONDITIONS} ({len(analysis.signals)})")
                            if not decision["conditions"]["breaking_high"]:
                                reasons.append("Not breaking high")
                            decision["reason"] = " & ".join(reasons)
                    else:
                        decision["final_decision"] = "REJECTED"
                        decision["reason"] = "Insufficient klines data"
                        
                except Exception as e:
                    decision["final_decision"] = "REJECTED"
                    decision["reason"] = f"Analysis error: {str(e)}"
                
                detailed_decisions.append(decision)
            
            # � LOGGING FIREBASE: Sauvegarder toutes les décisions détaillées
            if self.firebase_logger and detailed_decisions:
                try:
                    # Logger chaque décision individuelle dans la collection result_pair_scan
                    for decision in detailed_decisions:
                        # Ajouter les seuils de configuration à chaque décision
                        decision["config_min_volume"] = self.config.MIN_VOLUME_USDC
                        decision["config_max_spread"] = self.config.MAX_SPREAD_PERCENT
                        decision["config_min_volatility_1h"] = self.config.MIN_VOLATILITY_1H_PERCENT
                        decision["config_min_signal_conditions"] = self.config.MIN_SIGNAL_CONDITIONS
                        
                        self.firebase_logger.log_pair_scan_result(decision)
                    
                    # Statistiques globales du scan
                    validated_count = sum(1 for d in detailed_decisions if d['final_decision'] == 'VALIDATED')
                    rejected_count = sum(1 for d in detailed_decisions if d['final_decision'] == 'REJECTED')
                    
                    # Logger le résumé du scan
                    summary_data = {
                        'total_pairs': len(detailed_decisions),
                        'validated_pairs': validated_count,
                        'rejected_pairs': rejected_count,
                        'exclusion_stats': exclusion_stats,
                        'config_thresholds': {
                            'min_volume': self.config.MIN_VOLUME_USDC,
                            'max_spread': self.config.MAX_SPREAD_PERCENT,
                            'min_volatility_1h': self.config.MIN_VOLATILITY_1H_PERCENT,
                            'min_signal_conditions': self.config.MIN_SIGNAL_CONDITIONS
                        },
                        'scan_duration_ms': 0  # Peut être ajouté plus tard si besoin
                    }
                    
                    self.firebase_logger.log_scan_summary(summary_data)
                    
                    self.logger.info(f"🔥 {len(detailed_decisions)} décisions et résumé sauvegardés dans result_pair_scan")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur logging Firebase décisions: {e}")
            
            # �📊 LOGGING DÉTAILLÉ DES EXCLUSIONS (conservé pour logs console)
            self.logger.info(f"📊 Scan terminé - {exclusion_stats['total_analyzed']} paires analysées:")
            self.logger.info(f"   ⚫ Blacklistées: {exclusion_stats['blacklisted']} paires")
            if excluded_pairs['blacklisted']:
                self.logger.info(f"      {', '.join(excluded_pairs['blacklisted'][:5])}")
            
            self.logger.info(f"   📉 Volume < {self.config.MIN_VOLUME_USDC/1000000:.0f}M: {exclusion_stats['low_volume']} paires")
            if excluded_pairs['low_volume'][:3]:
                self.logger.info(f"      {', '.join(excluded_pairs['low_volume'][:3])}")
            
            self.logger.info(f"   📈 Spread > {self.config.MAX_SPREAD_PERCENT}%: {exclusion_stats['high_spread']} paires")
            if excluded_pairs['high_spread'][:3]:
                self.logger.info(f"      {', '.join(excluded_pairs['high_spread'][:3])}")
            
            self.logger.info(f"   ⏱️ Volatilité 1h < {self.config.MIN_VOLATILITY_1H_PERCENT}%: {exclusion_stats['low_volatility']} paires")
            if excluded_pairs['low_volatility'][:3]:
                self.logger.info(f"      {', '.join(excluded_pairs['low_volatility'][:3])}")
            
            validated_pairs = sum(1 for d in detailed_decisions if d['final_decision'] == 'VALIDATED')
            rejected_by_signals = sum(1 for d in detailed_decisions if d['final_decision'] == 'REJECTED' and 'Signal score' in d['reason'])
            self.logger.info(f"   🎯 Signaux insuffisants: {rejected_by_signals} paires")
            
            # 🔄 LOGIQUE ADAPTATIVE si pas assez de paires validées (conservée)
            if len(pair_scores) < 3 and hasattr(self.config, 'ADAPTIVE_FILTERING') and self.config.ADAPTIVE_FILTERING:
                self.logger.warning(f"⚠️ Seulement {len(pair_scores)} paires validées - Activation mode adaptatif")
                
                # Relancer avec critères assouplis
                pair_scores_fallback = []
                min_vol_fallback = getattr(self.config, 'MIN_VOLUME_USDC_FALLBACK', 30000000)
                min_volatility_fallback = getattr(self.config, 'MIN_VOLATILITY_1H_FALLBACK', 0.5)
                
                self.logger.info(f"🔄 Nouveaux critères: Volume >{min_vol_fallback/1000000:.0f}M, Volatilité >{min_volatility_fallback}%")
                
                for ticker in usdc_pairs:
                    symbol = ticker['symbol']
                    
                    if symbol in BLACKLISTED_PAIRS:
                        continue
                    
                    volume_usdc = float(ticker['quoteVolume'])
                    if volume_usdc < min_vol_fallback:
                        continue
                    
                    bid = float(ticker['bidPrice'])
                    ask = float(ticker['askPrice'])
                    spread = (ask - bid) / bid * 100
                    if spread > self.config.MAX_SPREAD_PERCENT:
                        continue
                    
                    price_change = abs(float(ticker['priceChangePercent']))
                    volatility_1h = self.calculate_volatility_1h(symbol)
                    if volatility_1h < min_volatility_fallback:
                        continue
                    
                    atr = await self.calculate_atr(symbol)
                    score = (0.6 * price_change + 0.4 * (volume_usdc / 1000000))
                    
                    pair_scores_fallback.append(PairScore(
                        pair=symbol,
                        volatility=price_change,
                        volume=volume_usdc,
                        score=score,
                        spread=spread,
                        atr=atr
                    ))
                
                if len(pair_scores_fallback) > len(pair_scores):
                    pair_scores = pair_scores_fallback
                    self.logger.info(f"✅ Mode adaptatif: {len(pair_scores)} paires trouvées avec critères assouplis")
            
            # Tri par score décroissant
            pair_scores.sort(key=lambda x: x.score, reverse=True)
            top_pairs = pair_scores[:self.config.MAX_PAIRS_TO_ANALYZE]
            
            self.logger.info(f"✅ {len(pair_scores)} paires validées, Top {len(top_pairs)} sélectionnées:")
            for i, pair in enumerate(top_pairs):
                self.logger.info(f"  {i+1}. {pair.pair} - Score: {pair.score:.2f} - Vol: {pair.volatility:.2f}% - Volume: {pair.volume/1000000:.1f}M USDC")
            
            # 🔥 LOG FIREBASE: Résultat du scan avec exclusions détaillées
            if self.firebase_logger and pair_scores:
                top_3_pairs = [f"{p.pair}({p.score:.1f})" for p in top_pairs[:3]]
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"📊 Scan terminé: {len(pair_scores)} paires validées, Top 3: {', '.join(top_3_pairs)}",
                    module="pair_scanner",
                    additional_data={
                        'total_pairs_analyzed': exclusion_stats['total_analyzed'],
                        'pairs_validated': len(pair_scores),
                        'top_pairs_selected': len(top_pairs),
                        'exclusions': exclusion_stats,
                        'excluded_samples': {
                            'low_volume': excluded_pairs['low_volume'][:3],
                            'high_spread': excluded_pairs['high_spread'][:3],
                            'low_volatility': excluded_pairs['low_volatility'][:3]
                        },
                        'best_pair': top_pairs[0].pair if top_pairs else None,
                        'best_score': top_pairs[0].score if top_pairs else 0
                    }
                )
            
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
            
            # 🚀 ANALYSE TECHNIQUE AVANCÉE avec TechnicalAnalyzer
            analysis = self.technical_analyzer.analyze_pair(df, symbol)
            
            # Vérification avec la configuration MIN_SIGNAL_CONDITIONS
            if self.technical_analyzer.is_valid_signal(analysis, self.config.MIN_SIGNAL_CONDITIONS):
                self.logger.info(f"✅ Signal détecté : {symbol}")
                self.logger.info(f"   📊 Score total: {analysis.total_score:.1f}")
                self.logger.info(f"   🎯 Recommandation: {analysis.recommendation}")
                self.logger.info(f"   📈 Tendance: {analysis.trend}")
                self.logger.info(f"   ⚡ Momentum: {analysis.momentum}")
                self.logger.info(f"   📊 Conditions validées: {len(analysis.signals)}/{self.config.MIN_SIGNAL_CONDITIONS}")
                
                # Firebase logging pour signal valide
                if self.firebase_logger:
                    signals_list = []
                    for signal in analysis.signals:
                        signals_list.append({
                            'indicator': signal.indicator,
                            'description': signal.description,
                            'strength': signal.strength.name
                        })
                    
                    self.firebase_logger.log_message(
                        level="INFO",
                        message=f"✅ SIGNAL VALIDE DÉTECTÉ: {symbol} (Score: {analysis.total_score:.1f})",
                        module="signal_detection",
                        pair=symbol,
                        additional_data={
                            'symbol': symbol,
                            'total_score': analysis.total_score,
                            'recommendation': analysis.recommendation,
                            'trend': analysis.trend,
                            'momentum': analysis.momentum,
                            'conditions_count': len(analysis.signals),
                            'min_conditions': self.config.MIN_SIGNAL_CONDITIONS,
                            'signals': signals_list
                        }
                    )
                
                # Log des signaux détectés
                for signal in analysis.signals:
                    strength_emoji = {"WEAK": "🟡", "MODERATE": "🟠", "STRONG": "🔴", "VERY_STRONG": "🟣"}
                    emoji = strength_emoji.get(signal.strength.name, "⚪")
                    self.logger.info(f"   {emoji} {signal.indicator}: {signal.description}")
                
                return TradeDirection.LONG
            
            # Log si signal insuffisant
            if len(analysis.signals) > 0:
                self.logger.info(f"⚠️ Signal {symbol} insuffisant: {len(analysis.signals)}/{self.config.MIN_SIGNAL_CONDITIONS} conditions (score: {analysis.total_score:.1f})")
                self.logger.info(f"   🎯 Recommandation: {analysis.recommendation}")
                for signal in analysis.signals[:3]:  # Max 3 signaux pour éviter spam
                    strength_emoji = {"WEAK": "🟡", "MODERATE": "🟠", "STRONG": "🔴", "VERY_STRONG": "🟣"}
                    emoji = strength_emoji.get(signal.strength.name, "⚪")
                    self.logger.info(f"   {emoji} {signal.indicator}: {signal.description}")
                    
                # Firebase logging pour signal insuffisant
                if self.firebase_logger:
                    signals_list = []
                    for signal in analysis.signals[:3]:
                        signals_list.append({
                            'indicator': signal.indicator,
                            'description': signal.description,
                            'strength': signal.strength.name
                        })
                    
                    self.firebase_logger.log_message(
                        level="WARNING",
                        message=f"⚠️ SIGNAL INSUFFISANT: {symbol} ({len(analysis.signals)}/{self.config.MIN_SIGNAL_CONDITIONS})",
                        module="signal_detection",
                        pair=symbol,
                        additional_data={
                            'symbol': symbol,
                            'total_score': analysis.total_score,
                            'recommendation': analysis.recommendation,
                            'conditions_count': len(analysis.signals),
                            'min_conditions': self.config.MIN_SIGNAL_CONDITIONS,
                            'signals': signals_list
                        }
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse {symbol}: {e}")
            
            # Firebase logging pour erreur d'analyse
            if self.firebase_logger:
                self.firebase_logger.log_message(
                    level="ERROR",
                    message=f"❌ ERREUR ANALYSE: {symbol} - {str(e)}",
                    module="signal_detection",
                    pair=symbol,
                    additional_data={'error': str(e)}
                )
            
            return None

    async def execute_trade(self, symbol: str, direction: TradeDirection):
        """Exécute un trade avec contrôle anti-fragmentation et logging détaillé des données techniques"""
        try:
            # 🚨 CONTRÔLE ANTI-FRAGMENTATION
            now = datetime.now()
            if symbol in self.last_trade_time:
                time_since_last = (now - self.last_trade_time[symbol]).total_seconds()
                if time_since_last < self.config.MIN_TRADE_INTERVAL_SECONDS:
                    self.logger.info(f"🚫 Trade {symbol} bloqué - Trop récent ({time_since_last:.0f}s < {self.config.MIN_TRADE_INTERVAL_SECONDS}s)")
                    
                    # Firebase logging pour trade bloqué
                    if self.firebase_logger:
                        self.firebase_logger.log_message(
                            level="WARNING",
                            message=f"🚫 TRADE BLOQUÉ: {symbol} - Trop récent",
                            module="trade_execution",
                            pair=symbol,
                            additional_data={
                                'time_since_last': time_since_last,
                                'min_interval': self.config.MIN_TRADE_INTERVAL_SECONDS,
                                'reason': 'anti_fragmentation'
                            }
                        )
                    
                    return
            
            # 📊 COLLECTE DES DONNÉES TECHNIQUES COMPLÈTES pour logging détaillé
            try:
                ticker_24h = self.binance_client.get_ticker(symbol=symbol)
                volume_usdc = float(ticker_24h.get('quoteVolume', ticker_24h.get('volume', 0)))
                bid = float(ticker_24h.get('bidPrice', ticker_24h.get('bid', 0)))
                ask = float(ticker_24h.get('askPrice', ticker_24h.get('ask', 0)))
                spread = (ask - bid) / bid * 100 if bid > 0 else 0
                price_change_24h = float(ticker_24h.get('priceChangePercent', ticker_24h.get('priceChange', 0)))
            except Exception as e:
                self.logger.error(f"❌ Erreur récupération ticker {symbol}: {e}")
                # Valeurs par défaut en cas d'erreur
                volume_usdc = 0
                spread = 0
                price_change_24h = 0
            
            # Calcul volatilité 1h
            volatility_1h = self.calculate_volatility_1h(symbol)
            
            # Récupération des données pour analyse technique détaillée
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=getattr(Client, f'KLINE_INTERVAL_{self.config.TIMEFRAME}'),
                limit=100
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades_count', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Analyse technique détaillée
            analysis = self.technical_analyzer.analyze_pair(df, symbol)
            
            # Calcul RSI, MACD, EMA actuels
            closes = df['close'].values
            rsi_current = talib.RSI(closes, timeperiod=self.config.RSI_PERIOD)[-1] # type: ignore
            macd, macd_signal, macd_hist = talib.MACD(closes, # type: ignore
                                                      fastperiod=self.config.MACD_FAST_PERIOD,
                                                      slowperiod=self.config.MACD_SLOW_PERIOD, 
                                                      signalperiod=self.config.MACD_SIGNAL_PERIOD)
            ema_fast = talib.EMA(closes, timeperiod=self.config.EMA_FAST_PERIOD)[-1] # type: ignore
            ema_slow = talib.EMA(closes, timeperiod=self.config.EMA_SLOW_PERIOD)[-1] # type: ignore
            
            # Calculer la volatilité pour cette paire
            volatility = self.calculate_volatility_1h(symbol)
            
            # Vérifications avant entrée avec nouveaux critères
            can_open, reason = self.can_open_position_enhanced(symbol, volatility)
            if not can_open:
                self.logger.info(f"❌ Trade {symbol} refusé: {reason}")
                
                # Firebase logging pour trade refusé
                if self.firebase_logger:
                    self.firebase_logger.log_message(
                        level="WARNING",
                        message=f"❌ TRADE REFUSÉ: {symbol} - {reason}",
                        module="trade_execution",
                        pair=symbol,
                        additional_data={
                            'volatility': volatility,
                            'reason': reason
                        }
                    )
                
                return
            
            # 🚀 PROTECTION VOLATILITÉ EXTRÊME
            if volatility > 30.0:  # Protection contre volatilité > 30%
                self.logger.warning(f"⚠️ VOLATILITÉ EXTRÊME {symbol}: {volatility:.2f}% > 30% - Trade refusé pour éviter gaps")
                
                # Firebase logging pour volatilité extrême
                if self.firebase_logger:
                    self.firebase_logger.log_message(
                        level="WARNING",
                        message=f"⚠️ VOLATILITÉ EXTRÊME: {symbol} - {volatility:.2f}%",
                        module="risk_management",
                        pair=symbol,
                        additional_data={
                            'volatility': volatility,
                            'max_allowed': 30.0,
                            'reason': 'extreme_volatility_gap_protection'
                        }
                    )
                return
            
            # 🚀 OPTIMISÉ: Vérification cassure AVANT calculs coûteux
            current_price = float(self.binance_client.get_symbol_ticker(symbol=symbol)['price'])
            if not self.check_breakout_confirmation(symbol, current_price):
                self.logger.info(f"❌ Trade {symbol} refusé: Cassure non confirmée (prix: {current_price:.4f})")
                
                # Firebase logging pour cassure non confirmée
                if self.firebase_logger:
                    self.firebase_logger.log_message(
                        level="WARNING",
                        message=f"❌ CASSURE NON CONFIRMÉE: {symbol}",
                        module="trade_execution",
                        pair=symbol,
                        additional_data={
                            'current_price': current_price,
                            'reason': 'breakout_not_confirmed'
                        }
                    )
                return
            
            # Informations d'allocation avant trade
            total_capital = self.get_total_capital()
            usdc_balance = self.get_asset_balance('USDC')
            base_asset = symbol.replace('USDC', '')
            current_exposure = self.get_asset_exposure(base_asset)
            
            # Calcul de la taille de position avec sizing adaptatif ANTI-FRAGMENTATION
            position_size = self.calculate_position_size(symbol, volatility)
            
            self.logger.info(f"💰 Allocation avant trade {symbol}:")
            self.logger.info(f"   📊 Capital total: {total_capital:.2f} USDC")
            self.logger.info(f"   � USDC disponible: {usdc_balance:.2f} USDC")
            self.logger.info(f"   🎯 Taille position: {position_size:.2f} USDC (volatilité: {volatility:.2f}%)")
            self.logger.info(f"   📈 Exposition {base_asset} actuelle: {current_exposure:.2f} USDC")
            self.logger.info(f"   🏦 Positions ouvertes: {len(self.open_positions)}")
            
            # Firebase logging pour allocation avant trade
            if self.firebase_logger:
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"💰 ALLOCATION AVANT TRADE: {symbol}",
                    module="trade_execution",
                    pair=symbol,
                    capital=total_capital,
                    additional_data={
                        'total_capital': total_capital,
                        'usdc_balance': usdc_balance,
                        'position_size': position_size,
                        'volatility': volatility,
                        'current_exposure': current_exposure,
                        'open_positions': len(self.open_positions),
                        'base_asset': base_asset
                    }
                )
            
            # Calcul SL et TP (current_price déjà récupéré lors de la vérification cassure)
            stop_loss = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
            take_profit = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
            trailing_stop = current_price * (1 + self.config.TRAILING_ACTIVATION_PERCENT / 100)
            
            # Log des niveaux de sortie incluant trailing stop
            self.logger.info(f"🎯 Niveaux de sortie pour {symbol}:")
            self.logger.info(f"   🛑 Stop Loss: {stop_loss:.4f} USDC (-{self.config.STOP_LOSS_PERCENT}%)")
            self.logger.info(f"   🎯 Take Profit: {take_profit:.4f} USDC (+{self.config.TAKE_PROFIT_PERCENT}%)")
            self.logger.info(f"   📈 Trailing activation: {trailing_stop:.4f} USDC (+{self.config.TRAILING_ACTIVATION_PERCENT}%)")
            self.logger.info(f"   🔄 Trailing step: {self.config.TRAILING_STEP_PERCENT}%")
            
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
                    self.logger.info(f"🔧 Quantité ajustée: {quantity:.8f} (capital: {position_size:.2f} USDC)")
                else:
                    self.logger.error(f"❌ Impossible de trader {symbol}: quantité minimale non respectée")
                    return
            
            # Arrondi final selon les règles de la paire
            quantity = self.round_quantity(symbol, quantity)
            
            # Vérification finale ANTI-FRAGMENTATION
            final_notional = quantity * current_price
            min_trade_size = getattr(self.config, 'MIN_POSITION_SIZE_USDC', 500.0)
            
            if final_notional < min_trade_size:
                self.logger.warning(f"🚫 Trade {symbol} bloqué - Taille insuffisante: {final_notional:.2f}€ < {min_trade_size}€ (ANTI-FRAGMENTATION)")
                return
                                  
            self.logger.info(f"✅ Trade {symbol} validé - Taille: {final_notional:.2f}€ (>{min_trade_size}€)")
            
            # Firebase logging pour trade validé
            if self.firebase_logger:
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"✅ TRADE VALIDÉ: {symbol} - Taille: {final_notional:.2f}€",
                    module="trade_execution",
                    pair=symbol,
                    additional_data={
                        'final_notional': final_notional,
                        'min_trade_size': min_trade_size,
                        'quantity': quantity,
                        'current_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'trailing_stop': trailing_stop
                    }
                )
            
            # Capital avant trade (AVANT l'achat)
            capital_before_trade = self.get_total_capital()
            
            # Passage de l'ordre
            order = self.binance_client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            # Création du trade avec capital_before
            trade = Trade(
                id=order['orderId'],
                pair=symbol,
                direction=direction,
                size=quantity,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                trailing_stop=trailing_stop,
                timestamp=datetime.now(),
                capital_before=capital_before_trade  # AJOUTÉ: Stocker le capital avant trade
            )
            
            # Ajout aux positions ouvertes avec ID unique
            trade_id = f"{symbol}_{trade.id}_{int(datetime.now().timestamp())}"
            self.open_positions[trade_id] = trade

            # � CRÉATION D'ORDRES STOP LOSS AUTOMATIQUES BINANCE
            try:
                stop_loss_order_id = await self.create_automatic_stop_loss(trade, symbol, quantity)
                if stop_loss_order_id:
                    trade.stop_loss_order_id = stop_loss_order_id
                    self.logger.info(f"🛑 Stop Loss automatique créé: {stop_loss_order_id}")
                else:
                    self.logger.warning(f"⚠️ Impossible de créer stop loss automatique pour {symbol}")
            except Exception as e:
                self.logger.error(f"❌ Erreur création stop loss automatique: {e}")

            # �🔥 Sauvegarde immédiate en Firebase
            try:
                if self.firebase_logger and self.firebase_logger.firebase_initialized and self.firebase_logger.firestore_db:
                    position_data = {
                        'trade_id': trade_id,
                        'pair': symbol,
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'size': quantity,
                        'timestamp': datetime.now().isoformat(),
                        'trailing_stop': trailing_stop,
                        'direction': direction.value if hasattr(direction, 'value') else str(direction),
                        'saved_at': datetime.now().isoformat(),
                        'session_id': self.firebase_logger.session_id
                    }
                    self.firebase_logger.firestore_db.collection('position_states').document(trade_id).set(position_data)
                    self.logger.debug(f"🔥 Position {trade_id} sauvegardée en Firebase")
            except Exception as e:
                self.logger.error(f"❌ Erreur sauvegarde position Firebase {trade_id}: {e}")

            # Enregistrement du timestamp pour éviter la fragmentation
            self.last_trade_time[symbol] = datetime.now()
            
            # OPTIMISÉ: Mise à jour des compteurs de suivi
            self.trades_per_hour.append(datetime.now())  # Enregistrer le trade pour limite horaire
            
            # Mise à jour du capital
            self.current_capital -= position_size
            
            # Logging
            self.logger.info(f"📈 Trade ouvert : {symbol}")
            self.logger.info(f"   💰 Prix d'entrée: {current_price:.4f} USDC")
            self.logger.info(f"   📊 Quantité: {quantity:.6f}")
            self.logger.info(f"   🛑 Stop Loss: {stop_loss:.4f} USDC (-{self.config.STOP_LOSS_PERCENT}%)")
            self.logger.info(f"   🎯 Take Profit: {take_profit:.4f} USDC (+{self.config.TAKE_PROFIT_PERCENT}%)")
            self.logger.info(f"   💵 Capital engagé: {position_size:.2f} USDC")
            
            # 📊 LOGGING DÉTAILLÉ DES DONNÉES TECHNIQUES
            self.logger.info(f"📊 Données techniques lors de l'entrée:")
            self.logger.info(f"   📈 RSI: {rsi_current:.1f} | MACD: {macd[-1]:.6f} | Signal: {macd_signal[-1]:.6f}")
            self.logger.info(f"   ⚡ EMA Fast: {ema_fast:.4f} | EMA Slow: {ema_slow:.4f}")
            self.logger.info(f"   📊 Score analyse: {analysis.total_score:.1f} | Tendance: {analysis.trend}")
            self.logger.info(f"   💹 Volume 24h: {volume_usdc/1000000:.1f}M USDC | Spread: {spread:.2f}%")
            self.logger.info(f"   🌡️ Volatilité 1h: {volatility_1h:.2f}% | 24h: {abs(price_change_24h):.2f}%")
            self.logger.info(f"   ✅ Signaux détectés: {len(analysis.signals)}/{self.config.MIN_SIGNAL_CONDITIONS}")
            
            # Affichage des signaux principaux
            for i, signal in enumerate(analysis.signals[:3]):  # Max 3 signaux pour éviter spam
                strength_emoji = {"WEAK": "🟡", "MODERATE": "🟠", "STRONG": "🔴", "VERY_STRONG": "🟣"}
                emoji = strength_emoji.get(signal.strength.name, "⚪")
                self.logger.info(f"   {emoji} Signal {i+1}: {signal.indicator} - {signal.description}")
            
            # Firebase logging pour trade ouvert avec données techniques complètes
            if self.firebase_logger:
                # Préparer les signaux détectés
                signals_data = []
                for signal in analysis.signals:
                    signals_data.append({
                        'indicator': signal.indicator,
                        'description': signal.description,
                        'strength': signal.strength.name
                    })
                
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"📈 TRADE OUVERT: {symbol} - Prix: {current_price:.4f} (Trailing: {trailing_stop:.4f})",
                    module="trade_execution",
                    trade_id=trade_id,
                    pair=symbol,
                    capital=capital_before_trade,
                    additional_data={
                        'order_id': order['orderId'],
                        'entry_price': current_price,
                        'quantity': quantity,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'trailing_stop': trailing_stop,
                        'trailing_activation_percent': self.config.TRAILING_ACTIVATION_PERCENT,
                        'trailing_step_percent': self.config.TRAILING_STEP_PERCENT,
                        'position_size': position_size,
                        'volatility_1h': volatility_1h,
                        'volatility_24h': abs(price_change_24h),
                        'technical_data': {
                            'rsi': float(rsi_current) if not np.isnan(rsi_current) else 0,
                            'macd': float(macd[-1]) if len(macd) > 0 and not np.isnan(macd[-1]) else 0,
                            'macd_signal': float(macd_signal[-1]) if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else 0,
                            'macd_hist': float(macd_hist[-1]) if len(macd_hist) > 0 and not np.isnan(macd_hist[-1]) else 0,
                            'ema_fast': float(ema_fast) if not np.isnan(ema_fast) else 0,
                            'ema_slow': float(ema_slow) if not np.isnan(ema_slow) else 0,
                            'analysis_score': analysis.total_score,
                            'trend': analysis.trend,
                            'momentum': analysis.momentum
                        },
                        'market_data': {
                            'volume_24h_usdc': volume_usdc,
                            'spread_percent': spread,
                            'price_change_24h': price_change_24h,
                            'bid_price': bid,
                            'ask_price': ask
                        },
                        'signals_detected': signals_data,
                        'conditions_met': len(analysis.signals),
                        'min_conditions_required': self.config.MIN_SIGNAL_CONDITIONS
                    }
                )
            
            # Notification Telegram
            await self.telegram_notifier.send_trade_open_notification(trade, position_size)
            
            # Log dans Google Sheets (si activé)
            if self.sheets_logger:
                # Capital après = USDC total + crypto existant APRÈS l'achat
                capital_after_trade = self.get_total_capital()
                
                self.logger.info(f"📊 Google Sheets - Capital avant: {capital_before_trade:.2f} USDC, après: {capital_after_trade:.2f} USDC (différence: {capital_after_trade - capital_before_trade:+.2f} USDC)")
                await self.sheets_logger.log_trade(trade, "OPEN", capital_before_trade, capital_after_trade)
            else:
                capital_after_trade = self.get_total_capital()
            
            # 🔥 LOG FIREBASE: Trade ouvert avec données techniques complètes
            self.firebase_logger.log_trade({
                'trade_id': trade_id,
                'timestamp': trade.timestamp.isoformat(),
                'pair': symbol,
                'direction': direction.value,
                'action': 'OPEN',
                'entry_price': current_price,
                'size': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'capital_before': capital_before_trade,
                'capital_after': capital_after_trade,
                'session_trading': get_current_trading_session(),
                'volatility_1h': volatility_1h,
                'volatility_24h': abs(price_change_24h),
                'volume_24h_usdc': volume_usdc,
                'spread_percent': spread,
                'technical_indicators': {
                    'rsi': float(rsi_current) if not np.isnan(rsi_current) else 0,
                    'macd': float(macd[-1]) if len(macd) > 0 and not np.isnan(macd[-1]) else 0,
                    'macd_signal': float(macd_signal[-1]) if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else 0,
                    'macd_hist': float(macd_hist[-1]) if len(macd_hist) > 0 and not np.isnan(macd_hist[-1]) else 0,
                    'ema_fast': float(ema_fast) if not np.isnan(ema_fast) else 0,
                    'ema_slow': float(ema_slow) if not np.isnan(ema_slow) else 0,
                    'analysis_score': analysis.total_score,
                    'trend': analysis.trend,
                    'momentum': analysis.momentum
                },
                'signals': {
                    'direction': direction.value,
                    'position_size': position_size,
                    'anti_fragmentation': True,
                    'conditions_met': len(analysis.signals),
                    'signals_count': len(analysis.signals)
                }
            })
            
            # 🔥 LOG FIREBASE: Métrique capital
            self.firebase_logger.log_metric(
                metric_type="capital_change",
                value=capital_after_trade - capital_before_trade,
                pair=symbol,
                additional_info={
                    'action': 'trade_open',
                    'capital_total': capital_after_trade,
                    'position_size': position_size
                }
            )
            
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

    async def create_automatic_stop_loss(self, trade, symbol: str, quantity: float) -> Optional[str]:
        """Crée un ordre stop loss automatique sur Binance"""
        try:
            # Calcul des prix pour l'ordre stop loss
            stop_price = trade.stop_loss  # Prix de déclenchement
            limit_price = stop_price * 0.995  # Prix limite légèrement en dessous (-0.5%)
            
            # Arrondir selon les règles de la paire
            limit_price = self.round_price(symbol, limit_price)
            stop_price = self.round_price(symbol, stop_price)
            
            # Vérification que la quantité est valide
            quantity = self.round_quantity(symbol, quantity)
            
            self.logger.info(f"🛑 Création stop loss automatique {symbol}:")
            self.logger.info(f"   📊 Quantité: {quantity:.8f}")
            self.logger.info(f"   🎯 Prix stop: {stop_price:.4f} USDC")
            self.logger.info(f"   💰 Prix limite: {limit_price:.4f} USDC")
            
            # Tentative avec ordre STOP_LOSS_LIMIT
            try:
                stop_order = self.binance_client.create_order(
                    symbol=symbol,
                    side='SELL',
                    type='STOP_LOSS_LIMIT',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=limit_price,
                    stopPrice=stop_price
                )
                
                self.logger.info(f"✅ Stop Loss automatique créé: ID {stop_order['orderId']}")
                return str(stop_order['orderId'])
                
            except Exception as e:
                # Fallback: Tentative avec ordre OCO si STOP_LOSS_LIMIT échoue
                if "not supported" in str(e).lower() or "invalid" in str(e).lower():
                    self.logger.warning(f"⚠️ STOP_LOSS_LIMIT non supporté pour {symbol}, tentative OCO...")
                    return await self.create_oco_order(trade, symbol, quantity)
                else:
                    raise e
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur création stop loss automatique pour {symbol}: {e}")
            return None

    async def create_oco_order(self, trade, symbol: str, quantity: float) -> Optional[str]:
        """Crée un ordre OCO (One-Cancels-Other) comme alternative"""
        try:
            # Prix pour l'ordre OCO
            stop_price = trade.stop_loss
            stop_limit_price = stop_price * 0.995
            take_profit_price = trade.take_profit
            
            # Arrondir les prix
            stop_price = self.round_price(symbol, stop_price)
            stop_limit_price = self.round_price(symbol, stop_limit_price)
            take_profit_price = self.round_price(symbol, take_profit_price)
            quantity = self.round_quantity(symbol, quantity)
            
            self.logger.info(f"🔄 Tentative OCO pour {symbol}")
            
            oco_order = self.binance_client.create_oco_order(
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                price=take_profit_price,  # Take profit
                stopPrice=stop_price,     # Stop loss trigger
                stopLimitPrice=stop_limit_price,  # Stop limit
                stopLimitTimeInForce='GTC'
            )
            
            # Récupérer l'ID de l'ordre stop loss de l'OCO
            for order in oco_order.get('orders', []):
                if order.get('type') == 'STOP_LOSS_LIMIT':
                    stop_loss_id = str(order['orderId'])
                    self.logger.info(f"✅ OCO créé avec stop loss: ID {stop_loss_id}")
                    return stop_loss_id
            
            return str(oco_order.get('orderListId', ''))
            
        except Exception as e:
            self.logger.error(f"❌ OCO non supporté pour {symbol}: {e}")
            return None

    def round_price(self, symbol: str, price: float) -> float:
        """Arrondit un prix selon les règles de la paire"""
        try:
            info = self.binance_client.get_symbol_info(symbol)
            for filter_item in info['filters']: # type: ignore
                if filter_item['filterType'] == 'PRICE_FILTER':
                    tick_size = float(filter_item['tickSize'])
                    precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                    return round(price, precision)
            return round(price, 4)
        except:
            return round(price, 4)

    async def cancel_automatic_stop_loss(self, trade, symbol: str):
        """Annule un ordre stop loss automatique"""
        try:
            if hasattr(trade, 'stop_loss_order_id') and trade.stop_loss_order_id:
                self.binance_client.cancel_order(
                    symbol=symbol,
                    orderId=int(trade.stop_loss_order_id)
                )
                self.logger.info(f"🗑️ Stop loss automatique annulé: {trade.stop_loss_order_id}")
                trade.stop_loss_order_id = None
                
        except Exception as e:
            # L'ordre peut déjà être exécuté ou annulé
            self.logger.debug(f"⚠️ Impossible d'annuler stop loss {trade.stop_loss_order_id}: {e}")

    async def check_automatic_order_execution(self, trade_id: str, trade) -> bool:
        """Vérifie si un ordre automatique (SL/TP) a été exécuté par Binance et enregistre le trade"""
        try:
            if not hasattr(trade, 'stop_loss_order_id') or not trade.stop_loss_order_id:
                return False
            
            # Vérifier le statut de l'ordre automatique
            try:
                order_status = self.binance_client.get_order(
                    symbol=trade.pair,
                    orderId=int(trade.stop_loss_order_id)
                )
                
                # Si l'ordre est rempli (FILLED), la position a été fermée automatiquement
                if order_status['status'] == 'FILLED':
                    executed_price = float(order_status['price']) if order_status.get('price') else float(order_status.get('avgPrice', 0))
                    executed_qty = float(order_status['executedQty'])
                    executed_time = order_status.get('updateTime', int(datetime.now().timestamp() * 1000))
                    
                    # Déterminer la raison de fermeture
                    if executed_price <= trade.stop_loss * 1.01:  # Tolérance 1%
                        reason = "STOP_LOSS_BINANCE_AUTO"
                    else:
                        reason = "TAKE_PROFIT_BINANCE_AUTO"
                    
                    self.logger.info(f"🤖 Ordre automatique Binance exécuté:")
                    self.logger.info(f"   📊 {trade.pair}: {executed_qty:.8f} à {executed_price:.4f} USDC")
                    self.logger.info(f"   🎯 Raison: {reason}")
                    self.logger.info(f"   🕐 Heure: {datetime.fromtimestamp(executed_time/1000)}")
                    
                    # Enregistrer la fermeture de trade avec les données Binance
                    await self.record_automatic_trade_closure(trade_id, trade, executed_price, reason, executed_time)
                    
                    return True
                    
            except Exception as e:
                # Si l'ordre n'existe plus, il a peut-être été exécuté
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    self.logger.warning(f"⚠️ Ordre {trade.stop_loss_order_id} introuvable - possiblement exécuté")
                    # Essayer de détecter via l'historique des trades récents
                    await self.detect_missing_execution(trade_id, trade)
                    return True
                else:
                    self.logger.debug(f"❌ Erreur vérification ordre {trade.stop_loss_order_id}: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification ordre automatique {trade_id}: {e}")
            return False

    async def record_automatic_trade_closure(self, trade_id: str, trade, exit_price: float, reason: str, executed_time: int):
        """Enregistre la fermeture automatique d'un trade par Binance"""
        try:
            # Mise à jour du trade
            trade.status = TradeStatus.CLOSED
            trade.exit_price = exit_price
            trade.exit_timestamp = datetime.fromtimestamp(executed_time / 1000)
            trade.duration = trade.exit_timestamp - trade.timestamp
            trade.exit_reason = reason
            
            # Calcul P&L
            capital_after_trade = self.get_total_capital()
            theoretical_pnl = (exit_price - trade.entry_price) * trade.size
            theoretical_pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
            
            # Utilisation du P&L réel si capital_before disponible
            if trade.capital_before is not None:
                real_pnl = capital_after_trade - trade.capital_before
                trade.capital_after = capital_after_trade
                trade.pnl = real_pnl
                pnl_amount = real_pnl
                pnl_percent = theoretical_pnl_percent
                
                self.logger.info(f"💰 P&L Réel (auto): {real_pnl:+.4f} USDC ({theoretical_pnl_percent:+.3f}%)")
            else:
                trade.pnl = theoretical_pnl
                pnl_amount = theoretical_pnl
                pnl_percent = theoretical_pnl_percent
                self.logger.info(f"💰 P&L théorique (auto): {theoretical_pnl:+.4f} USDC ({theoretical_pnl_percent:+.2f}%)")
            
            # Mise à jour des compteurs
            is_profit = pnl_amount > 0
            self.update_trade_result(is_profit)
            self.current_capital += (trade.entry_price * trade.size) + pnl_amount
            self.daily_pnl += pnl_amount
            self.daily_trades += 1
            
            # Suppression de la position ouverte
            if trade_id in self.open_positions:
                del self.open_positions[trade_id]
            
            # 🔥 FIREBASE LOGGING POUR FERMETURE AUTOMATIQUE
            if self.firebase_logger:
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"🤖 TRADE FERMÉ AUTOMATIQUEMENT: {trade.pair} - P&L: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)",
                    module="binance_auto_execution",
                    trade_id=trade_id,
                    pair=trade.pair,
                    capital=capital_after_trade,
                    additional_data={
                        'exit_price': exit_price,
                        'exit_reason': reason,
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent,
                        'duration_seconds': trade.duration.total_seconds() if trade.duration else 0,
                        'daily_pnl': self.daily_pnl,
                        'daily_trades': self.daily_trades,
                        'execution_source': 'binance_automatic',
                        'order_id': trade.stop_loss_order_id
                    }
                )
                
                # Log Firebase pour trade fermé automatiquement
                trade_data = {
                    'trade_id': trade_id,
                    'pair': trade.pair,
                    'direction': trade.direction.value,
                    'size': trade.size,
                    'entry_price': trade.entry_price,
                    'exit_price': exit_price,
                    'pnl_amount': pnl_amount,
                    'pnl_percent': pnl_percent,
                    'duration_seconds': trade.duration.total_seconds() if trade.duration else 0,
                    'exit_reason': reason,
                    'daily_pnl': self.daily_pnl,
                    'total_capital': capital_after_trade,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'capital_before': trade.capital_before,
                    'capital_after': capital_after_trade,
                    'execution_source': 'binance_automatic',
                    'automatic_order_id': trade.stop_loss_order_id
                }
                self.firebase_logger.log_trade(trade_data)
            
            # 🔥 Suppression de la position sauvegardée en Firebase
            try:
                if self.firebase_logger and self.firebase_logger.firebase_initialized and self.firebase_logger.firestore_db:
                    self.firebase_logger.firestore_db.collection('position_states').document(trade_id).delete()
                    self.logger.debug(f"🔥 Position {trade_id} supprimée de Firebase")
            except Exception as e:
                self.logger.error(f"❌ Erreur suppression position Firebase {trade_id}: {e}")
            
            # Logging détaillé
            pnl_symbol = "🚀" if pnl_amount > 0 else "📉"
            self.logger.info(f"{pnl_symbol} Trade fermé automatiquement : {trade.pair} ({reason})")
            self.logger.info(f"   💰 Prix de sortie: {exit_price:.4f} USDC")
            self.logger.info(f"   📊 P&L: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)")
            self.logger.info(f"   ⏱️ Durée: {trade.duration}")
            self.logger.info(f"   🤖 Exécution: Binance automatique")
            total_capital = self.get_total_capital()
            daily_pnl_percent = self.daily_pnl / total_capital * 100
            self.logger.info(f"   🔄 Total journalier: {self.daily_pnl:+.2f} USDC ({daily_pnl_percent:+.2f}%)")
            
            # Notification Telegram
            await self.telegram_notifier.send_trade_close_notification(trade, pnl_amount, pnl_percent, self.daily_pnl, total_capital)
            
            # Log dans Google Sheets (si activé)
            if self.sheets_logger:
                capital_before_close = total_capital - pnl_amount
                await self.sheets_logger.log_trade(trade, "CLOSE_AUTO", capital_before_close, total_capital)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur enregistrement fermeture automatique {trade_id}: {e}")

    async def detect_missing_execution(self, trade_id: str, trade):
        """Détecte une exécution manquée via l'historique des trades"""
        try:
            # Récupérer l'historique récent des trades
            recent_trades = self.binance_client.get_my_trades(symbol=trade.pair, limit=50)
            
            # Chercher un trade de vente correspondant à notre position
            for binance_trade in recent_trades:
                trade_time = datetime.fromtimestamp(binance_trade['time'] / 1000)
                
                # Si le trade est récent (dernières 10 minutes) et c'est une vente
                if (datetime.now() - trade_time).total_seconds() < 600 and binance_trade['isBuyer'] == False:
                    executed_price = float(binance_trade['price'])
                    executed_qty = float(binance_trade['qty'])
                    
                    # Si la quantité correspond approximativement
                    if abs(executed_qty - trade.size) / trade.size < 0.05:  # 5% de tolérance
                        reason = "STOP_LOSS_BINANCE_AUTO" if executed_price <= trade.stop_loss * 1.01 else "TAKE_PROFIT_BINANCE_AUTO"
                        
                        self.logger.info(f"🔍 Exécution automatique détectée via historique:")
                        self.logger.info(f"   📊 {trade.pair}: {executed_qty:.8f} à {executed_price:.4f} USDC")
                        self.logger.info(f"   🕐 Heure: {trade_time}")
                        
                        await self.record_automatic_trade_closure(trade_id, trade, executed_price, reason, binance_trade['time'])
                        return True
            
            # Si aucune exécution trouvée, fermeture virtuelle par sécurité
            self.logger.warning(f"⚠️ Aucune exécution automatique trouvée pour {trade.pair}, fermeture virtuelle")
            current_price = float(self.binance_client.get_symbol_ticker(symbol=trade.pair)['price'])
            await self.record_automatic_trade_closure(trade_id, trade, current_price, "BINANCE_AUTO_UNKNOWN", int(datetime.now().timestamp() * 1000))
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection exécution manquée {trade_id}: {e}")
            return False

    def get_non_dust_trades_on_pair(self, symbol: str) -> int:
        """Compte le nombre de trades non-miettes sur une paire"""
        base_asset = symbol.replace('USDC', '')
        non_dust_trades = 0
        
        for trade_id, trade in self.open_positions.items():
            if trade.pair == symbol:
                try:
                    # Récupération du prix actuel pour calculer la valeur
                    ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    position_value = trade.size * current_price
                    
                    # Ne compter que si la valeur dépasse le seuil des miettes
                    if position_value >= self.config.DUST_BALANCE_THRESHOLD_USDC:
                        non_dust_trades += 1
                        self.logger.debug(f"💎 Trade non-miette détecté {symbol}: {position_value:.2f}$ USDC")
                    else:
                        self.logger.debug(f"🧹 Trade miette ignoré {symbol}: {position_value:.2f}$ USDC < {self.config.DUST_BALANCE_THRESHOLD_USDC}$")
                        
                except Exception as e:
                    # Fallback sur le prix d'entrée en cas d'erreur
                    position_value = trade.size * trade.entry_price
                    if position_value >= self.config.DUST_BALANCE_THRESHOLD_USDC:
                        non_dust_trades += 1
                    self.logger.debug(f"⚠️ Erreur calcul valeur trade {symbol}, fallback: {position_value:.2f}$ USDC")
        
        return non_dust_trades

    def can_open_position(self, symbol: str) -> bool:
        """Vérifie si on peut ouvrir une position"""
        # Vérification nombre de positions
        if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS:
            self.logger.debug(f"❌ Limite max positions atteinte: {len(self.open_positions)}")
            return False
        
        # Vérification position déjà ouverte sur la paire (ignorant les miettes)
        non_dust_trades_on_pair = self.get_non_dust_trades_on_pair(symbol)
        if non_dust_trades_on_pair >= self.config.MAX_TRADES_PER_PAIR:
            self.logger.debug(f"❌ Limite trades non-miettes par paire atteinte: {non_dust_trades_on_pair}/{self.config.MAX_TRADES_PER_PAIR}")
            return False
        
        # Vérification capital USDC disponible (pas le total avec crypto!)
        position_size = self.calculate_position_size()
        usdc_balance = self.get_asset_balance('USDC')
        if usdc_balance < position_size:
            self.logger.debug(f"❌ Capital USDC insuffisant: {usdc_balance:.2f} < {position_size:.2f}")
            return False
        
        # Vérification exposition maximale par asset de base
        base_asset = symbol.replace('USDC', '')
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
        """Calcule l'exposition actuelle sur un asset de base (positions ouvertes + soldes existants NON TRACÉS)"""
        total_exposure = 0.0
        tracked_assets = 0
        
        # 1. Exposition des positions ouvertes tracées par le bot
        for trade_id, trade in self.open_positions.items():
            if trade.pair.replace('USDC', '') == base_asset:
                try:
                    ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                    current_price = float(ticker['price'])
                    position_value = trade.size * current_price
                    total_exposure += position_value
                    tracked_assets += trade.size
                    self.logger.debug(f"🎯 Position tracée {base_asset}: {trade.size:.8f} = {position_value:.2f} USDC")
                except Exception as e:
                    self.logger.error(f"❌ Erreur calcul exposition position {trade.pair}: {e}")
                    # Fallback sur le prix d'entrée
                    position_value = trade.size * trade.entry_price
                    total_exposure += position_value
                    tracked_assets += trade.size
        
        # 2. Exposition des soldes crypto existants NON TRACÉS (pour éviter double comptage)
        try:
            existing_balance = self.get_asset_balance(base_asset)
            if existing_balance > 0.00001:  # Seuil technique pour éviter erreurs
                # Calculer le solde NON TRACÉ (solde total - soldes des positions ouvertes)
                untracked_balance = existing_balance - tracked_assets
                
                if untracked_balance > 0.00001:  # Il y a un solde non tracé significatif
                    symbol = base_asset + 'USDC'
                    ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    untracked_value = untracked_balance * current_price
                    
                    # 🧹 GESTION INTELLIGENTE DES MIETTES pour le solde NON TRACÉ
                    if untracked_value < self.config.DUST_BALANCE_THRESHOLD_USDC:
                        self.logger.info(f"🧹 Miettes non-tracées détectées {base_asset}: {untracked_balance:.8f} ({untracked_value:.2f}$ < {self.config.DUST_BALANCE_THRESHOLD_USDC}$) - Ignorées pour exposition")
                    else:
                        total_exposure += untracked_value
                        self.logger.debug(f"💎 Exposition {base_asset}: Positions tracées: {total_exposure - untracked_value:.2f} USDC + Solde non-tracé: {untracked_value:.2f} USDC = Total: {total_exposure:.2f} USDC")
                else:
                    self.logger.debug(f"✅ Exposition {base_asset}: Tout le solde ({existing_balance:.8f}) est tracé par les positions ouvertes ({tracked_assets:.8f})")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul exposition solde existant {base_asset}: {e}")
        
        return total_exposure

    def calculate_position_size(self, pair: Optional[str] = None, volatility: Optional[float] = None) -> float:
        """Calcule la taille de position avec sizing adaptatif basé sur la volatilité et horaires"""
        total_capital = self.get_total_capital()
        base_size = total_capital * self.config.BASE_POSITION_SIZE_PERCENT / 100
        
        # Ajustement selon l'intensité horaire
        trading_intensity = get_trading_intensity(self.config)
        base_size *= trading_intensity
        
        # Si pas de volatilité fournie, utiliser la taille de base ajustée
        if volatility is None:
            return base_size
        
        # Position sizing adaptatif selon la volatilité
        if volatility > self.config.HIGH_VOLATILITY_THRESHOLD:
            # Réduire la taille pour paires très volatiles
            reduction_factor = min(0.5, self.config.VOLATILITY_REDUCTION_FACTOR * (volatility / self.config.HIGH_VOLATILITY_THRESHOLD))
            adjusted_size = base_size * (1 - reduction_factor)
            self.logger.info(f"📊 Position réduite pour {pair} (volatilité {volatility:.2f}%, intensité {trading_intensity*100:.0f}%): {adjusted_size:.2f} USDC")
            return adjusted_size
        elif volatility < self.config.LOW_VOLATILITY_THRESHOLD:
            # Augmenter légèrement pour paires peu volatiles (plus sûres)
            adjusted_size = base_size * 1.1
            self.logger.info(f"📊 Position augmentée pour {pair} (faible volatilité {volatility:.2f}%, intensité {trading_intensity*100:.0f}%): {adjusted_size:.2f} USDC")
            return adjusted_size
        else:
            # Volatilité normale, taille de base ajustée par horaire
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
        """Calcule le capital total dynamique (USDC + valeur de TOUTES les cryptos du compte)"""
        try:
            account_info = self.binance_client.get_account()
            total_capital = 0.0
            
            # Solde USDC
            usdc_balance = 0.0
            crypto_value = 0.0
            
            for balance in account_info['balances']:
                free_balance = float(balance['free'])
                asset = balance['asset']
                
                if free_balance > 0:
                    if asset == 'USDC':
                        usdc_balance = free_balance
                        total_capital += usdc_balance
                    elif free_balance > 0.00001:  # Seuil pour éviter les poussières
                        # Conversion en USDC pour tous les autres assets
                        try:
                            symbol = asset + 'USDC'
                            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                            price_usdc = float(ticker['price'])
                            value_usdc = free_balance * price_usdc
                            crypto_value += value_usdc
                            total_capital += value_usdc
                            self.logger.debug(f"💎 {asset}: {free_balance:.8f} x {price_usdc:.4f} = {value_usdc:.2f} USDC")
                        except Exception:
                            # Si pas de paire USDC pour cet asset, on ignore
                            self.logger.debug(f"⚠️ Pas de conversion USDC pour {asset}")
                            continue
            
            self.logger.debug(f"💰 Capital total: {total_capital:.2f} USDC (USDC libre: {usdc_balance:.2f}, Toutes cryptos: {crypto_value:.2f})")
            return total_capital
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul capital total: {e}")
            # Fallback sur le capital courant
            return self.current_capital

    async def manage_open_positions(self):
        """Gère les positions ouvertes et la surexposition"""
        for trade_id, trade in list(self.open_positions.items()):
            try:
                # 🚨 NOUVEAU: Vérification si un ordre automatique a été exécuté par Binance
                if hasattr(trade, 'stop_loss_order_id') and trade.stop_loss_order_id:
                    executed = await self.check_automatic_order_execution(trade_id, trade)
                    # Si le trade a été fermé automatiquement, passer au suivant
                    if executed or trade_id not in self.open_positions:
                        continue
                
                # Récupération du prix actuel
                ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                current_price = float(ticker['price'])

                # Calcul du P&L
                pnl_percent = (current_price - trade.entry_price) / trade.entry_price * 100

                # Vérification surexposition dynamique
                base_asset = trade.pair.replace('USDC', '')
                current_exposure = self.get_asset_exposure(base_asset)
                max_exposure_per_asset = self.get_total_capital() * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
                if current_exposure > max_exposure_per_asset * 1.01:  # tolérance 1%
                    self.logger.warning(f"⚠️ Surexposition détectée sur {base_asset}: {current_exposure:.2f} USDC > {max_exposure_per_asset:.2f} USDC ({self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)")
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

                # Vérification Stop Loss avec protection gap
                if current_price <= trade.stop_loss:
                    # Analyse du gap de marché
                    expected_loss = abs((trade.stop_loss - trade.entry_price) / trade.entry_price * 100)
                    actual_loss = abs((current_price - trade.entry_price) / trade.entry_price * 100)
                    gap_excess = actual_loss - expected_loss
                    
                    if gap_excess > 0.5:  # Gap significatif détecté
                        self.logger.error(f"🚨 GAP STOP LOSS {trade.pair}: Perte {actual_loss:.2f}% vs {expected_loss:.2f}% attendu (gap: {gap_excess:.2f}%)")
                        
                        # Firebase logging pour analyse des gaps
                        if self.firebase_logger:
                            self.firebase_logger.log_message(
                                level="ERROR",
                                message=f"🚨 GAP STOP LOSS: {trade.pair} - Gap: {gap_excess:.2f}%",
                                module="risk_management",
                                pair=trade.pair,
                                additional_data={
                                    'entry_price': trade.entry_price,
                                    'configured_stop_loss': trade.stop_loss,
                                    'actual_exit_price': current_price,
                                    'expected_loss_percent': expected_loss,
                                    'actual_loss_percent': actual_loss,
                                    'gap_excess_percent': gap_excess,
                                    'trade_duration': str(datetime.now() - trade.timestamp)
                                }
                            )
                    
                    await self.close_position(trade_id, current_price, "STOP_LOSS")
                    continue

                # Trailing Stop (priorité sur Take Profit pour laisser monter)
                trailing_activated = False
                if current_price >= trade.trailing_stop:
                    # Mise à jour du trailing stop
                    new_stop = current_price * (1 - self.config.TRAILING_STEP_PERCENT / 100)
                    if new_stop > trade.stop_loss:
                        trailing_activated = True
                        old_stop = trade.stop_loss
                        old_tp = trade.take_profit
                        
                        # Annuler l'ancien stop loss automatique
                        await self.cancel_automatic_stop_loss(trade, trade.pair)
                        
                        # Mise à jour du Stop Loss
                        trade.stop_loss = new_stop
                        
                        # Mise à jour du Take Profit pour qu'il suive la progression
                        # Nouveau TP = prix actuel + même écart relatif que le TP initial
                        new_take_profit = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
                        trade.take_profit = new_take_profit
                        
                        # Créer nouveau stop loss automatique avec nouveau niveau
                        try:
                            new_stop_order_id = await self.create_automatic_stop_loss(trade, trade.pair, trade.size)
                            if new_stop_order_id:
                                trade.stop_loss_order_id = new_stop_order_id
                        except Exception as e:
                            self.logger.error(f"❌ Erreur création nouveau stop loss automatique: {e}")
                        
                        self.logger.info(f"📈 Trailing Stop mis à jour pour {trade.pair}:")
                        self.logger.info(f"   🛑 Nouveau SL: {new_stop:.4f} USDC (ancien: {old_stop:.4f})")
                        self.logger.info(f"   🎯 Nouveau TP: {new_take_profit:.4f} USDC (ancien: {old_tp:.4f})")
                        
                        # Firebase logging pour trailing stop
                        if self.firebase_logger:
                            profit_percent = (current_price - trade.entry_price) / trade.entry_price * 100
                            self.firebase_logger.log_message(
                                level="INFO",
                                message=f"📈 TRAILING STOP: {trade.pair} - SL: {new_stop:.4f} (+{profit_percent:.2f}%)",
                                module="position_management",
                                trade_id=trade_id,
                                pair=trade.pair,
                                additional_data={
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': new_stop,
                                    'old_take_profit': old_tp,
                                    'new_take_profit': new_take_profit,
                                    'trigger_price': current_price,
                                    'profit_percent': profit_percent,
                                    'entry_price': trade.entry_price,
                                    'new_stop_order_id': trade.stop_loss_order_id
                                }
                            )

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

                # Vérification Take Profit (seulement si trailing stop pas activé)
                if not trailing_activated and current_price >= trade.take_profit:
                    await self.close_position(trade_id, current_price, "TAKE_PROFIT")
                    continue

            except Exception as e:
                self.logger.error(f"❌ Erreur gestion position {trade_id}: {e}")

    async def intensive_position_monitoring(self):
        """Surveillance intensive des positions à risque avec détection de gaps rapide"""
        try:
            for trade_id, trade in list(self.open_positions.items()):
                try:
                    # Récupération prix en temps réel
                    ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                    current_price = float(ticker['price'])
                    
                    # Calcul distance au stop loss
                    distance_to_stop = (current_price - trade.stop_loss) / trade.stop_loss * 100
                    
                    # Surveillance intensive si proche du stop loss
                    if distance_to_stop < 1.0:  # Moins de 1% du stop loss
                        self.logger.warning(f"⚠️ SURVEILLANCE INTENSIVE {trade.pair}: Prix {current_price:.4f} très proche du SL {trade.stop_loss:.4f} ({distance_to_stop:.2f}%)")
                        
                        # Vérification gap imminent
                        if current_price <= trade.stop_loss:
                            # Exécution immédiate pour éviter gap plus important
                            await self.close_position(trade_id, current_price, "STOP_LOSS_IMMEDIATE")
                            continue
                    
                    # Surveillance des mouvements rapides (volatilité excessive)
                    volatility = self.calculate_volatility_1h(trade.pair)
                    if volatility > 50.0:  # Volatilité extrême
                        pnl_percent = (current_price - trade.entry_price) / trade.entry_price * 100
                        
                        # Sortie préventive si volatilité dangereuse et perte modérée
                        if pnl_percent < -0.2 and volatility > 100.0:  # Perte > 0.2% et volatilité > 100%
                            self.logger.warning(f"🚨 SORTIE PRÉVENTIVE {trade.pair}: Volatilité extrême {volatility:.1f}% + perte {pnl_percent:.2f}%")
                            await self.close_position(trade_id, current_price, "VOLATILITY_PROTECTION")
                            continue
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur surveillance intensive {trade_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur surveillance intensive générale: {e}")

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
                base_asset = trade.pair.replace('USDC', '')
                current_exposure = self.get_asset_exposure(base_asset)
                max_exposure_per_asset = self.get_total_capital() * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
                if current_exposure > max_exposure_per_asset * 1.01:  # tolérance 1%
                    self.logger.warning(f"⚠️ Surexposition détectée sur {base_asset}: {current_exposure:.2f} USDC > {max_exposure_per_asset:.2f} USDC ({self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)")
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

                # Vérification Stop Loss avec protection gap
                if current_price <= trade.stop_loss:
                    # Analyse du gap de marché
                    expected_loss = abs((trade.stop_loss - trade.entry_price) / trade.entry_price * 100)
                    actual_loss = abs((current_price - trade.entry_price) / trade.entry_price * 100)
                    gap_excess = actual_loss - expected_loss
                    
                    if gap_excess > 0.5:  # Gap significatif détecté
                        self.logger.error(f"🚨 GAP STOP LOSS {trade.pair}: Perte {actual_loss:.2f}% vs {expected_loss:.2f}% attendu (gap: {gap_excess:.2f}%)")
                        
                        # Firebase logging pour analyse des gaps
                        if self.firebase_logger:
                            self.firebase_logger.log_message(
                                level="ERROR",
                                message=f"🚨 GAP STOP LOSS: {trade.pair} - Gap: {gap_excess:.2f}%",
                                module="risk_management",
                                pair=trade.pair,
                                additional_data={
                                    'entry_price': trade.entry_price,
                                    'configured_stop_loss': trade.stop_loss,
                                    'actual_exit_price': current_price,
                                    'expected_loss_percent': expected_loss,
                                    'actual_loss_percent': actual_loss,
                                    'gap_excess_percent': gap_excess,
                                    'trade_duration': str(datetime.now() - trade.timestamp)
                                }
                            )
                    
                    await self.close_position(trade_id, current_price, "STOP_LOSS")
                    continue

                # Trailing Stop (priorité sur Take Profit pour laisser monter)
                trailing_activated = False
                if current_price >= trade.trailing_stop:
                    # Mise à jour du trailing stop
                    new_stop = current_price * (1 - self.config.TRAILING_STEP_PERCENT / 100)
                    if new_stop > trade.stop_loss:
                        trailing_activated = True
                        old_stop = trade.stop_loss
                        old_tp = trade.take_profit
                        
                        # Annuler l'ancien stop loss automatique
                        await self.cancel_automatic_stop_loss(trade, trade.pair)
                        
                        # Mise à jour du Stop Loss
                        trade.stop_loss = new_stop
                        
                        # Mise à jour du Take Profit pour qu'il suive la progression
                        # Nouveau TP = prix actuel + même écart relatif que le TP initial
                        new_take_profit = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
                        trade.take_profit = new_take_profit
                        
                        # Créer nouveau stop loss automatique avec nouveau niveau
                        try:
                            new_stop_order_id = await self.create_automatic_stop_loss(trade, trade.pair, trade.size)
                            if new_stop_order_id:
                                trade.stop_loss_order_id = new_stop_order_id
                        except Exception as e:
                            self.logger.error(f"❌ Erreur création nouveau stop loss automatique: {e}")
                        
                        self.logger.info(f"📈 Trailing Stop mis à jour pour {trade.pair}:")
                        self.logger.info(f"   🛑 Nouveau SL: {new_stop:.4f} USDC (ancien: {old_stop:.4f})")
                        self.logger.info(f"   🎯 Nouveau TP: {new_take_profit:.4f} USDC (ancien: {old_tp:.4f})")
                        
                        # Firebase logging pour trailing stop
                        if self.firebase_logger:
                            profit_percent = (current_price - trade.entry_price) / trade.entry_price * 100
                            self.firebase_logger.log_message(
                                level="INFO",
                                message=f"📈 TRAILING STOP: {trade.pair} - SL: {new_stop:.4f} (+{profit_percent:.2f}%)",
                                module="position_management",
                                trade_id=trade_id,
                                pair=trade.pair,
                                additional_data={
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': new_stop,
                                    'old_take_profit': old_tp,
                                    'new_take_profit': new_take_profit,
                                    'trigger_price': current_price,
                                    'profit_percent': profit_percent,
                                    'entry_price': trade.entry_price,
                                    'new_stop_order_id': trade.stop_loss_order_id
                                }
                            )

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

                # Vérification Take Profit (seulement si trailing stop pas activé)
                if not trailing_activated and current_price >= trade.take_profit:
                    await self.close_position(trade_id, current_price, "TAKE_PROFIT")
                    continue

            except Exception as e:
                self.logger.error(f"❌ Erreur gestion position {trade_id}: {e}")

    async def close_position(self, trade_id: str, exit_price: float, reason: str):
        """Ferme une position"""
        try:
            trade = self.open_positions[trade_id]
            symbol = trade.pair
            
            # Annuler l'ordre stop loss automatique s'il existe
            await self.cancel_automatic_stop_loss(trade, symbol)
            
            # Récupération de l'asset de base (ex: ETH pour ETHUSDC)
            base_asset = symbol.replace('USDC', '')
            
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
                    self.logger.error(f"   Valeur: {quantity_to_sell * exit_price:.2f} USDC")
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
            
            # CORRIGÉ: Calcul P&L réel basé sur la différence de capital
            capital_after_trade = self.get_total_capital()
            
            # Calcul théorique pour comparaison
            theoretical_pnl = (exit_price - trade.entry_price) * trade.size
            theoretical_pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
            
            # Utilisation du P&L réel si capital_before disponible
            if trade.capital_before is not None:
                real_pnl = capital_after_trade - trade.capital_before
                # CORRECTION: Utiliser le pourcentage théorique (basé sur le prix) au lieu du capital
                # real_pnl_percent = (real_pnl / trade.capital_before) * 100  # BUG: mauvais calcul
                
                # Mise à jour du trade avec le capital après et P&L réel
                trade.capital_after = capital_after_trade
                trade.pnl = real_pnl
                pnl_amount = real_pnl
                pnl_percent = theoretical_pnl_percent  # CORRECTION: utiliser le % théorique correct
                
                self.logger.info(f"💰 P&L Réel: {real_pnl:+.4f} USDC ({theoretical_pnl_percent:+.3f}%)")
                self.logger.debug(f"🧮 P&L Théorique: {theoretical_pnl:+.4f} USDC ({theoretical_pnl_percent:+.3f}%)")
                self.logger.debug(f"📊 Capital-based %: {real_pnl / trade.capital_before * 100:+.3f}% (debug only)")
            else:
                # Fallback sur calcul théorique si capital_before manquant
                self.logger.warning(f"⚠️ Capital avant trade non disponible, utilisation du calcul théorique")
                trade.pnl = theoretical_pnl
                pnl_amount = theoretical_pnl
                pnl_percent = theoretical_pnl_percent
                self.logger.debug(f"🧮 P&L théorique: {theoretical_pnl:+.4f} USDC ({theoretical_pnl_percent:+.2f}%)")
            
            # OPTIMISÉ: Mise à jour du suivi des résultats
            is_profit = pnl_amount > 0
            self.update_trade_result(is_profit)
            
            # OPTIMISÉ: Vérification arrêt après pertes consécutives
            if self.consecutive_losses >= self.config.MAX_CONSECUTIVE_LOSSES and self.config.ENABLE_CONSECUTIVE_LOSS_PROTECTION:
                if self.config.AUTO_RESUME_AFTER_PAUSE:
                    # Mode pause temporaire
                    self.consecutive_loss_pause_until = datetime.now() + timedelta(minutes=self.config.CONSECUTIVE_LOSS_PAUSE_MINUTES)
                    
                    self.logger.warning(f"⏸️ PAUSE TEMPORAIRE: {self.consecutive_losses} pertes consécutives")
                    self.logger.warning(f"   Reprise prévue: {self.consecutive_loss_pause_until.strftime('%H:%M:%S')}")
                    self.logger.warning(f"   Durée: {self.config.CONSECUTIVE_LOSS_PAUSE_MINUTES} minutes")
                    
                    # Firebase logging pour pause temporaire
                    if self.firebase_logger:
                        self.firebase_logger.log_message(
                            level="WARNING", 
                            message=f"⏸️ PAUSE TEMPORAIRE: {self.consecutive_losses} pertes consécutives",
                            module="risk_management",
                            additional_data={
                                'consecutive_losses': self.consecutive_losses,
                                'pause_duration_minutes': self.config.CONSECUTIVE_LOSS_PAUSE_MINUTES,
                                'resume_at': self.consecutive_loss_pause_until.isoformat(),
                                'last_trade_results': self.last_trade_results
                            }
                        )
                    
                    # Notification Telegram de pause
                    message = f"⏸️ PAUSE TEMPORAIRE ACTIVÉE\n"
                    message += f"Raison: {self.consecutive_losses} pertes consécutives\n"
                    message += f"Dernière perte: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)\n"
                    message += f"Reprise prévue: {self.consecutive_loss_pause_until.strftime('%H:%M:%S')}\n"
                    message += f"Durée: {self.config.CONSECUTIVE_LOSS_PAUSE_MINUTES} minutes"
                    
                    await self.telegram_notifier.send_message(message)
                    
                else:
                    # Mode arrêt définitif (ancien comportement)
                    self.logger.error(f"🚨 ARRÊT AUTOMATIQUE: {self.consecutive_losses} pertes consécutives atteintes!")
                    
                    # Firebase logging pour arrêt automatique
                    if self.firebase_logger:
                        self.firebase_logger.log_message(
                            level="CRITICAL",
                            message=f"🚨 BOT ARRÊTÉ: {self.consecutive_losses} pertes consécutives",
                            module="risk_management",
                            additional_data={
                                'consecutive_losses': self.consecutive_losses,
                                'max_allowed': self.config.MAX_CONSECUTIVE_LOSSES,
                                'last_trade_results': self.last_trade_results
                            }
                        )
                    
                    # Notification Telegram d'urgence
                    message = f"🚨 BOT ARRÊTÉ AUTOMATIQUEMENT\n"
                    message += f"Raison: {self.consecutive_losses} pertes consécutives\n"
                    message += f"Dernière perte: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)\n"
                    message += f"Protection activée pour préserver le capital"
                    
                    await self.telegram_notifier.send_message(message)
                    
                    # Arrêt du bot
                    self.is_running = False
                    return
            
            # Mise à jour des totaux
            self.current_capital += (trade.entry_price * trade.size) + pnl_amount
            self.daily_pnl += pnl_amount
            self.daily_trades += 1
            
            # Suppression de la position ouverte
            del self.open_positions[trade_id]
            
            # 🔥 Suppression de la position sauvegardée en Firebase
            try:
                if self.firebase_logger and self.firebase_logger.firebase_initialized and self.firebase_logger.firestore_db:
                    self.firebase_logger.firestore_db.collection('position_states').document(trade_id).delete()
                    self.logger.debug(f"🔥 Position {trade_id} supprimée de Firebase")
            except Exception as e:
                self.logger.error(f"❌ Erreur suppression position Firebase {trade_id}: {e}")
            
            # Logging
            pnl_symbol = "🚀" if pnl_amount > 0 else "📉"
            self.logger.info(f"{pnl_symbol} Trade fermé : {symbol} ({reason})")
            self.logger.info(f"   💰 Prix de sortie: {exit_price:.4f} USDC")
            self.logger.info(f"   📊 P&L: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)")
            self.logger.info(f"   ⏱️ Durée: {trade.duration}")
            total_capital = self.get_total_capital()
            daily_pnl_percent = self.daily_pnl / total_capital * 100
            self.logger.info(f"   🔄 Total journalier: {self.daily_pnl:+.2f} USDC ({daily_pnl_percent:+.2f}%)")
            
            # Firebase logging pour trade fermé
            if self.firebase_logger:
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"{pnl_symbol} TRADE FERMÉ: {symbol} - P&L: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)",
                    module="trade_execution",
                    trade_id=trade_id,
                    pair=symbol,
                    capital=total_capital,
                    additional_data={
                        'exit_price': exit_price,
                        'exit_reason': reason,
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent,
                        'duration_seconds': trade.duration.total_seconds() if trade.duration else 0,
                        'daily_pnl': self.daily_pnl,
                        'daily_trades': self.daily_trades
                    }
                )
            
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
            
            # Log Firebase pour fermeture de trade
            if self.firebase_logger:
                try:
                    trade_data = {
                        'trade_id': trade_id,
                        'pair': trade.pair,
                        'direction': trade.direction.value,
                        'size': trade.size,
                        'entry_price': trade.entry_price,
                        'exit_price': exit_price,
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent,
                        'duration_seconds': trade.duration.total_seconds() if trade.duration else 0,
                        'exit_reason': reason,
                        'daily_pnl': self.daily_pnl,
                        'total_capital': total_capital,
                        'stop_loss': trade.stop_loss,
                        'take_profit': trade.take_profit,
                        'capital_before': total_capital - pnl_amount,
                        'capital_after': total_capital,
                        'pnl_gross': pnl_amount,
                        'pnl_net': pnl_amount  # À ajuster si vous avez des frais à déduire
                    }
                    self.firebase_logger.log_trade(trade_data)
                except Exception as e:
                    self.logger.error(f"❌ Erreur log Firebase fermeture: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture position {trade_id}: {e}")
    
    async def close_position_virtually(self, trade_id: str, exit_price: float, reason: str):
        """Ferme une position virtuellement (sans ordre réel) en cas de problème"""
        try:
            trade = self.open_positions[trade_id]
            symbol = trade.pair
            
            self.logger.warning(f"🔄 Fermeture virtuelle de {symbol} à {exit_price:.4f} USDC")
            
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
            
            # 🔥 Suppression de la position sauvegardée en Firebase
            try:
                if self.firebase_logger and self.firebase_logger.firebase_initialized and self.firebase_logger.firestore_db:
                    self.firebase_logger.firestore_db.collection('position_states').document(trade_id).delete()
                    self.logger.debug(f"🔥 Position virtuelle {trade_id} supprimée de Firebase")
            except Exception as e:
                self.logger.error(f"❌ Erreur suppression position virtuelle Firebase {trade_id}: {e}")
            
            # Logging spécial pour fermeture virtuelle
            pnl_symbol = "⚠️" 
            self.logger.warning(f"{pnl_symbol} Trade fermé virtuellement : {symbol} ({reason})")
            self.logger.warning(f"   💰 Prix de sortie: {exit_price:.4f} USDC")
            self.logger.warning(f"   📊 P&L théorique: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%)")
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
            
            # Log Firebase pour fermeture virtuelle de trade
            if self.firebase_logger:
                try:
                    trade_data = {
                        'trade_id': trade_id,
                        'pair': trade.pair,
                        'direction': trade.direction.value,
                        'size': trade.size,
                        'entry_price': trade.entry_price,
                        'exit_price': exit_price,
                        'pnl_amount': pnl_amount,
                        'pnl_percent': pnl_percent,
                        'duration_seconds': trade.duration.total_seconds() if trade.duration else 0,
                        'exit_reason': f"{reason}_VIRTUAL",
                        'daily_pnl': self.daily_pnl,
                        'total_capital': total_capital,
                        'stop_loss': trade.stop_loss,
                        'take_profit': trade.take_profit,
                        'capital_before': total_capital - pnl_amount,
                        'capital_after': total_capital,
                        'pnl_gross': pnl_amount,
                        'pnl_net': pnl_amount  # Pas de frais en fermeture virtuelle
                    }
                    self.firebase_logger.log_trade(trade_data)
                except Exception as e:
                    self.logger.error(f"❌ Erreur log Firebase fermeture virtuelle: {e}")
            
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
        
        # Firebase logging pour arrêt quotidien
        if self.firebase_logger:
            reason = "DAILY_TARGET" if self.daily_target_reached else "DAILY_STOP_LOSS"
            total_capital = self.get_total_capital()
            daily_pnl_percent = self.daily_pnl / total_capital * 100
            
            self.firebase_logger.log_message(
                level="WARNING",
                message=f"🛑 ARRÊT QUOTIDIEN: {reason} - P&L: {self.daily_pnl:+.2f} USDC ({daily_pnl_percent:+.2f}%)",
                module="daily_management",
                capital=total_capital,
                additional_data={
                    'reason': reason,
                    'daily_pnl': self.daily_pnl,
                    'daily_pnl_percent': daily_pnl_percent,
                    'daily_trades': self.daily_trades,
                    'open_positions_count': len(self.open_positions),
                    'target_reached': self.daily_target_reached,
                    'stop_loss_hit': self.daily_stop_loss_hit
                }
            )
        
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
            
            # Log Firebase pour les performances quotidiennes
            if self.firebase_logger:
                try:
                    firebase_perf_data = {
                        'date': today,
                        'total_capital': total_capital,
                        'daily_pnl': self.daily_pnl,
                        'daily_pnl_percent': daily_pnl_percent,
                        'total_trades': total_trades,
                        'winning_trades': winning_trades,
                        'losing_trades': losing_trades,
                        'win_rate': win_rate,
                        'max_drawdown': min(0, daily_pnl_percent),
                        'status': 'COMPLETED'
                    }
                    self.firebase_logger.log_performance(firebase_perf_data)
                    self.logger.info(f"🔥 Performances journalières enregistrées dans Firebase")
                except Exception as e:
                    self.logger.error(f"❌ Erreur log Firebase performances: {e}")
            
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
                'total_pnl': self.get_total_capital() - self.start_capital,  # P&L total par rapport au capital initial USDC
                'win_rate': win_rate,
                'pairs_analyzed': [trade.pair for trade in self.open_positions.values()],
                'top_pair': list(self.open_positions.values())[0].pair if self.open_positions else None
            }
            
            await self.database.insert_realtime_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur enregistrement métriques temps réel: {e}")
    
    async def convert_dust_to_bnb_if_needed(self):
        """Convertit automatiquement les miettes de crypto en BNB si nécessaire"""
        try:
            account_info = self.binance_client.get_account()
            dust_assets = []
            
            for balance in account_info['balances']:
                asset = balance['asset']
                free_balance = float(balance['free'])
                
                # Skip USDC, BNB et les soldes nuls
                if asset in ['USDC', 'BNB'] or free_balance <= 0.00001:
                    continue
                
                try:
                    # Calcul de la valeur en USDC
                    symbol = asset + 'USDC'
                    ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                    price_usdc = float(ticker['price'])
                    value_usdc = free_balance * price_usdc
                    
                    # Si c'est une miette
                    if value_usdc < self.config.DUST_BALANCE_THRESHOLD_USDC:
                        dust_assets.append({
                            'asset': asset,
                            'balance': free_balance,
                            'value_usdc': value_usdc
                        })
                        
                except Exception:
                    # Pas de paire USDC pour cet asset, on ignore
                    continue
            
            if dust_assets:
                total_dust_value = sum(d['value_usdc'] for d in dust_assets)
                self.logger.info(f"🧹 {len(dust_assets)} miettes détectées (total: {total_dust_value:.2f}$ USDC)")
                
                # Conversion via l'API Binance Dust Transfer
                try:
                    assets_to_convert = [d['asset'] for d in dust_assets]
                    result = self.binance_client.transfer_dust(**{'asset': assets_to_convert})
                    
                    if result.get('transferResult'):
                        total_bnb = sum(float(r.get('transferedAmount', 0)) for r in result['transferResult'])
                        self.logger.info(f"✅ Miettes converties en {total_bnb:.8f} BNB")
                        
                        # Notification Telegram
                        await self.telegram_notifier.send_message(
                            f"🧹 **Nettoyage automatique des miettes**\\n\\n"
                            f"💰 {len(dust_assets)} assets convertis\\n"
                            f"📊 Valeur totale: {total_dust_value:.2f}$ USDC\\n"
                            f"🪙 BNB reçu: {total_bnb:.8f} BNB\\n\\n"
                            f"Assets convertis: {', '.join(assets_to_convert)}"
                        )
                        
                    else:
                        self.logger.warning(f"⚠️ Échec conversion miettes: {result}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Erreur conversion miettes: {e}")
                    # Alternative: Log pour conversion manuelle
                    dust_list = ', '.join([f"{d['asset']} ({d['value_usdc']:.2f}$)" for d in dust_assets])
                    self.logger.info(f"💡 Miettes à convertir manuellement: {dust_list}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur check miettes: {e}")

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
                    base_asset = trade.pair.replace('USDC', '')
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
                if asset == 'USDC' or balance <= 0.00001:
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
                    
                    self.logger.warning(f"   🔥 {asset}: {current_exposure:.2f} USDC > {max_allowed:.2f} USDC (excès: {excess_eur:.2f} USDC)")
                    
                    # Calculer quelle quantité vendre pour revenir dans la limite
                    try:
                        symbol = asset + 'USDC'
                        ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        
                        # Quantité à vendre = excès en USDC / prix actuel
                        quantity_to_sell = excess_eur / current_price
                        balance = asset_info['balance']
                        
                        # Ne pas vendre plus que ce qu'on a
                        if quantity_to_sell > balance:
                            quantity_to_sell = balance * 0.95  # Marge de sécurité
                        
                        # Arrondir selon les règles de la paire
                        quantity_to_sell = self.round_quantity(symbol, quantity_to_sell)
                        
                        if quantity_to_sell > 0:
                            self.logger.warning(f"   🔧 VENTE FORCÉE {asset}: {quantity_to_sell:.8f} ({quantity_to_sell * current_price:.2f} USDC)")
                            
                            # Exécuter la vente d'urgence
                            try:
                                order = self.binance_client.order_market_sell(
                                    symbol=symbol,
                                    quantity=quantity_to_sell
                                )
                                
                                self.logger.info(f"✅ SUREXPOSITION CORRIGÉE: Vendu {quantity_to_sell:.8f} {asset} pour {quantity_to_sell * current_price:.2f} USDC")
                                
                                # Notification Telegram d'urgence
                                message = f"🚨 CORRECTION SUREXPOSITION\n"
                                message += f"Asset: {asset}\n"
                                message += f"Vendu: {quantity_to_sell:.8f} ({quantity_to_sell * current_price:.2f} USDC)\n"
                                message += f"Exposition avant: {current_exposure:.2f} USDC\n"
                                message += f"Limite: {max_allowed:.2f} USDC"
                                
                                await self.telegram_notifier.send_message(message)
                                
                            except Exception as e:
                                self.logger.error(f"❌ ÉCHEC vente forcée {asset}: {e}")
                                
                    except Exception as e:
                        self.logger.error(f"❌ Erreur calcul vente forcée {asset}: {e}")
            
            # 4. Détection de soldes non tracés (positions fantômes inverses)
            for asset, balance in balances.items():
                if asset == 'USDC' or balance <= 0.001:
                    continue
                    
                # Vérifier si on a un solde significatif sans position tracée
                has_tracked_position = any(trade.pair.replace('USDC', '') == asset for trade in self.open_positions.values())
                
                if not has_tracked_position and balance > 0.001:
                    try:
                        symbol = asset + 'USDC'
                        ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        value_usdc = balance * current_price
                        
                        if value_usdc > 100:  # Seuil significatif
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
        """Compte le nombre de trades ouverts NON-MIETTES pour une paire - VÉRIFICATION RENFORCÉE"""
        # Comptage en mémoire par symbole MAIS en ignorant les miettes
        non_dust_trades = self.get_non_dust_trades_on_pair(symbol)
        
        # Vérification supplémentaire via solde Binance
        try:
            base_asset = symbol.replace('USDC', '')
            binance_balance = self.get_asset_balance(base_asset)
            
            # Calculer la valeur du solde en USDC
            ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            balance_value_usdc = binance_balance * current_price
            
            # Si on a un solde significatif (non-miette) mais pas de position non-miette en mémoire = incohérence
            if balance_value_usdc >= self.config.DUST_BALANCE_THRESHOLD_USDC and non_dust_trades == 0:
                self.logger.warning(f"⚠️ Incohérence détectée: {base_asset} balance={binance_balance:.6f} ({balance_value_usdc:.2f}$ USDC) mais 0 positions non-miettes en mémoire")
                # Considérer qu'on a déjà une position pour éviter la surexposition
                return 1
            elif balance_value_usdc < self.config.DUST_BALANCE_THRESHOLD_USDC:
                self.logger.debug(f"🧹 Solde miette détecté {base_asset}: {balance_value_usdc:.2f}$ < {self.config.DUST_BALANCE_THRESHOLD_USDC}$ - Non compté dans limite")
            
            return non_dust_trades
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification solde {symbol}: {e}")
            # En cas d'erreur, utiliser le comptage des trades non-miettes en mémoire
            return non_dust_trades

    def can_open_position_enhanced(self, symbol: str, volatility: float) -> tuple[bool, str]:
        """Vérifie si on peut ouvrir une position selon les nouvelles règles"""
        # 1. Vérifier limite trades par paire - STRICT
        current_trades = self.count_trades_per_pair(symbol)
        if current_trades >= self.config.MAX_TRADES_PER_PAIR:
            return False, f"Limite trades par paire atteinte ({current_trades}/{self.config.MAX_TRADES_PER_PAIR})"

        # 2. OPTIMISÉ: Vérifier limite trades par heure
        if not self.can_trade_within_hourly_limit():
            return False, f"Limite trades par heure atteinte ({len(self.trades_per_hour)}/{self.config.MAX_TRADES_PER_HOUR})"

        # 3. OPTIMISÉ: Vérifier protection contre pertes consécutives
        if not self.can_trade_after_consecutive_losses():
            return False, f"Bot arrêté après {self.consecutive_losses} pertes consécutives"

        # 4. Vérifier volatilité minimum
        if volatility < self.config.MIN_VOLATILITY_1H_PERCENT:
            return False, f"Volatilité insuffisante ({volatility:.2f}% < {self.config.MIN_VOLATILITY_1H_PERCENT}%)"
        
        # 5. Vérifier nombre total de positions
        total_open_positions = len(self.open_positions)
        if total_open_positions >= self.config.MAX_OPEN_POSITIONS:
            return False, f"Limite positions totales atteinte ({total_open_positions}/{self.config.MAX_OPEN_POSITIONS})"
        
        # 4. VÉRIFICATION EXPOSITION : Contrôler AVANT + APRÈS la nouvelle position
        base_asset = symbol.replace('USDC', '')
        current_exposure = self.get_asset_exposure(base_asset)
        total_capital = self.get_total_capital()
        max_exposure_per_asset = total_capital * self.config.MAX_EXPOSURE_PER_ASSET_PERCENT / 100
        
        # Calcul de la nouvelle exposition après ajout de la position
        new_position_size = self.calculate_position_size(symbol, volatility)
        future_exposure = current_exposure + new_position_size
        
        if current_exposure > max_exposure_per_asset:
            return False, f"Exposition {base_asset} déjà trop élevée ({current_exposure:.2f} USDC > {max_exposure_per_asset:.2f} USDC = {self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)"
        
        if future_exposure > max_exposure_per_asset:
            return False, f"Nouvelle position créerait surexposition {base_asset} ({current_exposure:.2f} + {new_position_size:.2f} = {future_exposure:.2f} USDC > {max_exposure_per_asset:.2f} USDC = {self.config.MAX_EXPOSURE_PER_ASSET_PERCENT}% du capital)"
        
        # 5. VÉRIFICATION CAPITAL : Capital USDC minimum disponible avec marge
        usdc_balance = self.get_asset_balance('USDC')
        if usdc_balance < new_position_size * 1.1:  # Marge de sécurité 10%
            return False, f"Capital USDC insuffisant ({usdc_balance:.2f} < {new_position_size * 1.1:.2f} USDC requis)"
        
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
            # Vérifier durée minimale avant sortie momentum
            duration_minutes = (datetime.now() - trade.timestamp).total_seconds() / 60
            if duration_minutes < self.config.MOMENTUM_MIN_DURATION_MINUTES:
                return False, ""  # Trop tôt pour sortie momentum
            
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

    # OPTIMISÉ: Nouvelles fonctions de protection
    def clean_old_trades_from_hour(self):
        """Nettoie les trades de plus d'une heure"""
        now = datetime.now()
        self.trades_per_hour = [
            trade_time for trade_time in self.trades_per_hour 
            if (now - trade_time).total_seconds() < 3600  # 1 heure = 3600 secondes
        ]

    def can_trade_within_hourly_limit(self) -> bool:
        """Vérifie si on peut trader selon la limite horaire"""
        self.clean_old_trades_from_hour()
        return len(self.trades_per_hour) < self.config.MAX_TRADES_PER_HOUR

    def can_trade_after_consecutive_losses(self) -> bool:
        """Vérifie si on peut trader après vérification des pertes consécutives"""
        if not self.config.ENABLE_CONSECUTIVE_LOSS_PROTECTION:
            return True
        
        # Vérifier si on est en pause
        if self.consecutive_loss_pause_until:
            now = datetime.now()
            if now < self.consecutive_loss_pause_until:
                return False  # Encore en pause
            else:
                # Fin de pause - RÉINITIALISATION COMPLÈTE
                old_consecutive_losses = self.consecutive_losses
                self.logger.info(f"✅ FIN DE PAUSE: Reprise du trading après pause de sécurité")
                self.consecutive_loss_pause_until = None
                
                # 🔥 RÉINITIALISATION COMPLÈTE DU COMPTEUR
                self.consecutive_losses = 0
                self.last_trade_results = []  # Reset de l'historique des résultats
                
                self.logger.info(f"🔄 COMPTEURS RÉINITIALISÉS dans can_trade_after_consecutive_losses:")
                self.logger.info(f"   Pertes consécutives: {old_consecutive_losses} → {self.consecutive_losses}")
                
                return True
        
        return self.consecutive_losses < self.config.MAX_CONSECUTIVE_LOSSES

    def update_trade_result(self, is_profit: bool):
        """Met à jour le suivi des résultats de trades"""
        self.last_trade_results.append(is_profit)
        
        # Garder seulement les 10 derniers trades
        if len(self.last_trade_results) > 10:
            self.last_trade_results.pop(0)
        
        # Si c'est un profit, reset le compteur de pertes consécutives et la pause
        if is_profit:
            if self.consecutive_losses > 0:
                self.logger.info(f"✅ PROFIT: Reset du compteur de pertes consécutives ({self.consecutive_losses} → 0)")
            self.consecutive_losses = 0
            self.consecutive_loss_pause_until = None  # Annuler toute pause en cours
        else:
            # Compter les pertes consécutives depuis la fin
            self.consecutive_losses = 0
            for result in reversed(self.last_trade_results):
                if not result:  # Si c'est une perte
                    self.consecutive_losses += 1
                else:  # Si c'est un profit, arrêter le comptage
                    break
        
        # Log important si on approche de la limite
        if self.consecutive_losses >= self.config.MAX_CONSECUTIVE_LOSSES - 1:
            self.logger.warning(f"⚠️ ATTENTION: {self.consecutive_losses} pertes consécutives (limite: {self.config.MAX_CONSECUTIVE_LOSSES})")

    def check_breakout_confirmation(self, symbol: str, current_price: float) -> bool:
        """Vérifie la confirmation de cassure"""
        if not self.config.ENABLE_BREAKOUT_CONFIRMATION:
            return True
        
        try:
            # Récupérer les dernières bougies pour trouver le dernier sommet
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=20
            )
            
            if len(klines) < 10:
                return True  # Pas assez de données, on laisse passer
            
            # Trouver le plus haut des 20 dernières minutes
            highs = [float(k[2]) for k in klines[:-1]]  # Exclure la bougie courante
            last_high = max(highs)
            
            # Vérifier si le prix actuel dépasse le dernier sommet + seuil
            confirmation_threshold = last_high * (1 + self.config.BREAKOUT_CONFIRMATION_PERCENT / 100)
            
            if current_price > confirmation_threshold:
                self.logger.info(f"✅ Cassure confirmée {symbol}: {current_price:.4f} > {confirmation_threshold:.4f}")
                return True
            else:
                self.logger.debug(f"❌ Cassure non confirmée {symbol}: {current_price:.4f} ≤ {confirmation_threshold:.4f}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification cassure {symbol}: {e}")
            return True  # En cas d'erreur, on laisse passer

    async def check_market_volatility(self, top_pairs: List):
        """Vérifie la volatilité moyenne du marché et envoie des notifications"""
        try:
            if not top_pairs:
                return
            
            # Calcul de la volatilité moyenne des top paires
            volatilities = [pair.volatility for pair in top_pairs if hasattr(pair, 'volatility')]
            
            if not volatilities:
                return
            
            avg_volatility = sum(volatilities) / len(volatilities)
            
            # Notification de volatilité via le notificateur d'horaires
            await self.hours_notifier.check_volatility_and_notify(avg_volatility)
            
            # Log pour suivi
            self.logger.debug(f"📊 Volatilité moyenne marché: {avg_volatility:.2f}% (sur {len(volatilities)} paires)")
            
            # Firebase logging pour volatilité marché
            if self.firebase_logger and avg_volatility > 5.0:  # Logger seulement si volatilité significative
                self.firebase_logger.log_message(
                    level="INFO",
                    message=f"📊 VOLATILITÉ MARCHÉ: {avg_volatility:.2f}% (sur {len(volatilities)} paires)",
                    module="market_analysis",
                    additional_data={
                        'avg_volatility': avg_volatility,
                        'pairs_count': len(volatilities),
                        'volatilities': volatilities[:10]  # Top 10 pour éviter surcharge
                    }
                )
                
                # Log métrique volatilité
                self.firebase_logger.log_metric("market_volatility", avg_volatility)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification volatilité marché: {e}")

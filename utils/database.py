"""
Module de gestion de base de données SQLite pour le bot de trading
"""

import asyncio
import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class TradingDatabase:
    """Gestionnaire de base de données SQLite pour le trading"""
    
    def __init__(self, db_path: str = "data/trading_bot.db"):
        self.db_path = db_path
        self.ensure_directory()
        
    def ensure_directory(self):
        """Crée le répertoire data s'il n'existe pas"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager pour les connexions DB"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Pour des résultats en dict
            yield conn
        finally:
            if conn:
                conn.close()
    
    async def initialize_database(self):
        """Initialise la base de données avec toutes les tables"""
        async with self.get_connection() as conn:
            # Table des trades
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    trailing_stop REAL NOT NULL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    exit_reason TEXT,
                    pnl_amount REAL DEFAULT 0,
                    pnl_percent REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    capital_engaged REAL NOT NULL,
                    signals_detected TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des trailing stops
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trailing_stops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    old_stop_loss REAL NOT NULL,
                    new_stop_loss REAL NOT NULL,
                    trigger_price REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    profit_percent REAL NOT NULL,
                    FOREIGN KEY (trade_id) REFERENCES trades (id)
                )
            """)
            
            # Table des performances quotidiennes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    start_capital REAL NOT NULL,
                    end_capital REAL NOT NULL,
                    daily_pnl REAL NOT NULL,
                    daily_pnl_percent REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    losing_trades INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    profit_factor REAL,
                    sharpe_ratio REAL,
                    best_trade REAL,
                    worst_trade REAL,
                    avg_trade_duration REAL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des métriques en temps réel
            conn.execute("""
                CREATE TABLE IF NOT EXISTS realtime_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    current_capital REAL NOT NULL,
                    open_positions INTEGER NOT NULL,
                    daily_pnl REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    pairs_analyzed TEXT,
                    top_pair TEXT,
                    api_calls_count INTEGER DEFAULT 0,
                    uptime_seconds INTEGER DEFAULT 0
                )
            """)
            
            # Table des signaux détectés
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_strength INTEGER NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    technical_indicators TEXT,
                    action_taken TEXT,
                    reason TEXT
                )
            """)
            
            # Index pour optimiser les requêtes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(entry_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_performance_date ON daily_performance(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trailing_stops_trade_id ON trailing_stops(trade_id)")
            
            conn.commit()
            logging.info("✅ Base de données initialisée")
    
    async def insert_trade(self, trade_data: Dict) -> int:
        """Insert un nouveau trade"""
        async with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO trades (
                    symbol, side, entry_price, quantity, stop_loss, take_profit,
                    trailing_stop, entry_time, capital_engaged, signals_detected, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['symbol'],
                trade_data['side'],
                trade_data['entry_price'],
                trade_data['quantity'],
                trade_data['stop_loss'],
                trade_data['take_profit'],
                trade_data['trailing_stop'],
                trade_data['entry_time'],
                trade_data['capital_engaged'],
                json.dumps(trade_data.get('signals_detected', [])),
                'OPEN'
            ))
            conn.commit()
            return cursor.lastrowid # type: ignore
    
    async def update_trade_exit(self, trade_id: int, exit_data: Dict):
        """Met à jour un trade à la fermeture"""
        async with self.get_connection() as conn:
            conn.execute("""
                UPDATE trades SET
                    exit_price = ?, exit_time = ?, status = ?, exit_reason = ?,
                    pnl_amount = ?, pnl_percent = ?, commission = ?
                WHERE id = ?
            """, (
                exit_data['exit_price'],
                exit_data['exit_time'],
                'CLOSED',
                exit_data['exit_reason'],
                exit_data['pnl_amount'],
                exit_data['pnl_percent'],
                exit_data.get('commission', 0),
                trade_id
            ))
            conn.commit()
    
    async def insert_trailing_stop(self, trailing_data: Dict):
        """Insert un événement de trailing stop"""
        async with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO trailing_stops (
                    trade_id, symbol, old_stop_loss, new_stop_loss,
                    trigger_price, timestamp, profit_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trailing_data['trade_id'],
                trailing_data['symbol'],
                trailing_data['old_stop_loss'],
                trailing_data['new_stop_loss'],
                trailing_data['trigger_price'],
                trailing_data['timestamp'],
                trailing_data['profit_percent']
            ))
            conn.commit()
    
    async def insert_daily_performance(self, perf_data: Dict):
        """Insert les performances quotidiennes"""
        async with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO daily_performance (
                    date, start_capital, end_capital, daily_pnl, daily_pnl_percent,
                    total_trades, winning_trades, losing_trades, win_rate,
                    max_drawdown, profit_factor, sharpe_ratio, best_trade,
                    worst_trade, avg_trade_duration, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                perf_data['date'],
                perf_data['start_capital'],
                perf_data['end_capital'],
                perf_data['daily_pnl'],
                perf_data['daily_pnl_percent'],
                perf_data['total_trades'],
                perf_data['winning_trades'],
                perf_data['losing_trades'],
                perf_data['win_rate'],
                perf_data['max_drawdown'],
                perf_data.get('profit_factor'),
                perf_data.get('sharpe_ratio'),
                perf_data.get('best_trade'),
                perf_data.get('worst_trade'),
                perf_data.get('avg_trade_duration'),
                perf_data['status']
            ))
            conn.commit()
    
    async def insert_realtime_metrics(self, metrics: Dict):
        """Insert les métriques en temps réel"""
        async with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO realtime_metrics (
                    timestamp, current_capital, open_positions, daily_pnl,
                    total_pnl, win_rate, pairs_analyzed, top_pair,
                    api_calls_count, uptime_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics['timestamp'],
                metrics['current_capital'],
                metrics['open_positions'],
                metrics['daily_pnl'],
                metrics['total_pnl'],
                metrics['win_rate'],
                json.dumps(metrics.get('pairs_analyzed', [])),
                metrics.get('top_pair'),
                metrics.get('api_calls_count', 0),
                metrics.get('uptime_seconds', 0)
            ))
            conn.commit()
    
    async def insert_signal(self, signal_data: Dict):
        """Insert un signal détecté"""
        async with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO signals (
                    symbol, timestamp, signal_type, signal_strength,
                    price, volume, technical_indicators, action_taken, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['symbol'],
                signal_data['timestamp'],
                signal_data['signal_type'],
                signal_data['signal_strength'],
                signal_data['price'],
                signal_data['volume'],
                json.dumps(signal_data.get('technical_indicators', {})),
                signal_data.get('action_taken'),
                signal_data.get('reason')
            ))
            conn.commit()
    
    # Méthodes de requête pour les investisseurs
    async def get_performance_summary(self, days: int = 30) -> Dict:
        """Récupère un résumé des performances"""
        async with self.get_connection() as conn:
            # Performance globale
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl_amount > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl_amount < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl_amount) as total_pnl,
                    AVG(pnl_percent) as avg_return,
                    MAX(pnl_percent) as best_trade,
                    MIN(pnl_percent) as worst_trade,
                    AVG((julianday(exit_time) - julianday(entry_time)) * 24 * 60) as avg_duration_minutes
                FROM trades 
                WHERE status = 'CLOSED' 
                AND entry_time >= datetime('now', '-{} days')
            """.format(days))
            
            performance = dict(cursor.fetchone())
            
            # Performance quotidienne récente
            cursor = conn.execute("""
                SELECT date, daily_pnl_percent, total_trades, win_rate
                FROM daily_performance 
                WHERE date >= date('now', '-{} days')
                ORDER BY date DESC
            """.format(days))
            
            daily_performance = [dict(row) for row in cursor.fetchall()]
            
            return {
                'summary': performance,
                'daily_performance': daily_performance,
                'generated_at': datetime.now().isoformat()
            }
    
    async def get_trades_history(self, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des trades"""
        async with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM trades 
                ORDER BY entry_time DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_trailing_stops_history(self, symbol: str = None) -> List[Dict]: # type: ignore
        """Récupère l'historique des trailing stops"""
        async with self.get_connection() as conn:
            if symbol:
                cursor = conn.execute("""
                    SELECT * FROM trailing_stops 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                """, (symbol,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM trailing_stops 
                    ORDER BY timestamp DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    async def export_data_for_investors(self, output_file: str = "investor_report.json"):
        """Exporte toutes les données pour les investisseurs"""
        try:
            # Récupération de toutes les données
            performance_summary = await self.get_performance_summary(365)  # 1 an
            trades_history = await self.get_trades_history(1000)  # 1000 derniers trades
            trailing_stops = await self.get_trailing_stops_history()
            
            # Calculs supplémentaires pour les investisseurs
            async with self.get_connection() as conn:
                # Évolution du capital
                cursor = conn.execute("""
                    SELECT date, end_capital 
                    FROM daily_performance 
                    ORDER BY date
                """)
                capital_evolution = [dict(row) for row in cursor.fetchall()]
                
                # Distribution des retours
                cursor = conn.execute("""
                    SELECT 
                        pnl_percent,
                        COUNT(*) as frequency
                    FROM trades 
                    WHERE status = 'CLOSED'
                    GROUP BY ROUND(pnl_percent, 1)
                    ORDER BY pnl_percent
                """)
                returns_distribution = [dict(row) for row in cursor.fetchall()]
            
            # Compilation du rapport
            investor_report = {
                'report_date': datetime.now().isoformat(),
                'performance_summary': performance_summary,
                'capital_evolution': capital_evolution,
                'trades_history': trades_history,
                'trailing_stops_history': trailing_stops,
                'returns_distribution': returns_distribution,
                'metadata': {
                    'total_records': len(trades_history),
                    'period_covered': '365 days',
                    'bot_version': '2.0.0',
                    'strategy': 'EUR Scalping with Trailing Stops'
                }
            }
            
            # Sauvegarde
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(investor_report, f, indent=2, default=str, ensure_ascii=False)
            
            logging.info(f"✅ Rapport investisseurs exporté: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Erreur export investisseurs: {e}")
            raise

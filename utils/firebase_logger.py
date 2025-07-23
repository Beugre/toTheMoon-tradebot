"""
Firebase Logger complet pour Trading Bot
Enregistrement temps réel des logs, trades, performances et métriques
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from queue import Queue
from typing import Any, Dict, List, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, db, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("⚠️ Firebase non installé. Installez avec: pip install firebase-admin")
    FIREBASE_AVAILABLE = False

from .firebase_config import FIREBASE_CONFIG


def get_paris_time() -> datetime:
    """Obtient l'heure actuelle en fuseau horaire Paris (UTC+2)"""
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))

def get_paris_time_iso() -> str:
    """Obtient l'heure actuelle en fuseau horaire Paris au format ISO"""
    return get_paris_time().isoformat()

@dataclass
class LogEntry:
    """Structure d'un log entry"""
    timestamp: str
    level: str
    message: str
    bot_module: str
    session_id: str
    trade_id: Optional[str] = None
    pair: Optional[str] = None
    capital: Optional[float] = None
    additional_data: Optional[Dict] = None

@dataclass
class TradeEntry:
    """Structure d'un trade entry"""
    trade_id: str
    timestamp: str
    pair: str
    direction: str
    action: str  # OPEN, CLOSE, UPDATE
    entry_price: float
    exit_price: Optional[float]
    size: float
    stop_loss: float
    take_profit: float
    pnl_gross: Optional[float]
    pnl_net: Optional[float]
    fees: Optional[float]
    duration_seconds: Optional[int]
    exit_reason: Optional[str]
    capital_before: float
    capital_after: float
    session_trading: str
    volatility: Optional[float]
    volume_24h: Optional[str]
    spread_percent: Optional[float]
    signals: Optional[Dict] = None

@dataclass
class PerformanceEntry:
    """Structure d'une entrée de performance"""
    timestamp: str
    session_id: str
    total_capital: float
    daily_pnl: float
    daily_trades: int
    win_rate: float
    total_fees: float
    open_positions: int
    best_pair: Optional[str]
    worst_pair: Optional[str]
    trading_session: str
    market_volatility: Optional[float]

@dataclass
class MetricEntry:
    """Structure d'une métrique temps réel"""
    timestamp: str
    metric_type: str  # capital, positions, pnl, volatility, etc.
    value: float
    pair: Optional[str] = None
    additional_info: Optional[Dict] = None


class FirebaseLogger:
    """Logger Firebase complet pour analytics temps réel"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_id = f"session_{int(time.time())}"
        
        # Files d'attente pour upload en batch
        self.logs_queue = Queue()
        self.trades_queue = Queue()
        self.performance_queue = Queue()
        self.metrics_queue = Queue()
        
        # État Firebase
        self.firebase_initialized = False
        self.db_ref = None
        self.firestore_db = None
        
        # Thread d'upload en arrière-plan
        self.upload_thread = None
        self.stop_upload = False
        
        if FIREBASE_AVAILABLE and FIREBASE_CONFIG.ENABLE_FIREBASE_LOGGING:
            self.initialize_firebase()
            self.start_upload_thread()
        else:
            self.logger.warning("🔥 Firebase désactivé ou non disponible")

    def initialize_firebase(self):
        """Initialise Firebase Admin SDK"""
        try:
            # Vérification si déjà initialisé
            if firebase_admin._apps:  # type: ignore
                app = firebase_admin.get_app() # type: ignore
            else:
                # Initialisation avec le fichier de credentials
                cred = credentials.Certificate(FIREBASE_CONFIG.CREDENTIALS_PATH) # type: ignore
                app = firebase_admin.initialize_app(cred, { # type: ignore
                    'databaseURL': FIREBASE_CONFIG.DATABASE_URL,
                    'projectId': FIREBASE_CONFIG.PROJECT_ID
                })
            
            # Références aux bases de données
            self.db_ref = db.reference() # type: ignore
            self.firestore_db = firestore.client() # type: ignore
            
            self.firebase_initialized = True
            self.logger.info("🔥 Firebase initialisé avec succès")
            
            # Test de connexion
            self.test_firebase_connection()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Firebase: {e}")
            self.firebase_initialized = False

    def test_firebase_connection(self):
        """Test la connexion Firebase"""
        try:
            # Test Realtime Database
            test_ref = self.db_ref.child('_connection_test') # type: ignore
            test_ref.set({
                'timestamp': get_paris_time_iso(),
                'session_id': self.session_id,
                'status': 'connected'
            })
            
            # Test Firestore
            doc_ref = self.firestore_db.collection('_connection_test').document('test') # type: ignore
            doc_ref.set({
                'timestamp': get_paris_time_iso(),
                'session_id': self.session_id,
                'status': 'connected'
            })
            
            self.logger.info("🔥 Test connexion Firebase réussi")
            
        except Exception as e:
            self.logger.error(f"❌ Test connexion Firebase échoué: {e}")

    def start_upload_thread(self):
        """Démarre le thread d'upload en arrière-plan"""
        self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self.upload_thread.start()
        self.logger.info("🔥 Thread upload Firebase démarré")

    def _upload_worker(self):
        """Worker thread pour upload en batch"""
        while not self.stop_upload:
            try:
                self._process_upload_queues()
                time.sleep(FIREBASE_CONFIG.BATCH_INTERVAL_SECONDS)
            except Exception as e:
                self.logger.error(f"❌ Erreur upload worker: {e}")

    def _process_upload_queues(self):
        """Traite toutes les files d'upload"""
        if not self.firebase_initialized:
            return

        # Upload logs
        self._upload_batch_from_queue(
            self.logs_queue, 
            FIREBASE_CONFIG.LOGS_COLLECTION,
            "logs"
        )
        
        # Upload trades
        self._upload_batch_from_queue(
            self.trades_queue,
            FIREBASE_CONFIG.TRADES_COLLECTION, 
            "trades"
        )
        
        # Upload performance
        self._upload_batch_from_queue(
            self.performance_queue,
            FIREBASE_CONFIG.PERFORMANCE_COLLECTION,
            "performance"
        )
        
        # Upload métriques
        self._upload_batch_from_queue(
            self.metrics_queue,
            FIREBASE_CONFIG.METRICS_COLLECTION,
            "metrics"
        )

    def _upload_batch_from_queue(self, queue: Queue, collection: str, data_type: str):
        """Upload un batch depuis une file"""
        batch_data = []
        batch_count = 0
        
        # Collecte des données
        while not queue.empty() and batch_count < FIREBASE_CONFIG.BATCH_SIZE:
            try:
                data = queue.get_nowait()
                batch_data.append(data)
                batch_count += 1
            except:
                break
        
        if not batch_data:
            return
        
        try:
            # Upload vers Firestore (pour requêtes complexes)
            collection_ref = self.firestore_db.collection(collection) # type: ignore
            
            batch = self.firestore_db.batch() # type: ignore
            for data in batch_data: 
                doc_ref = collection_ref.document()
                batch.set(doc_ref, data)
            
            batch.commit()
            
            # Upload vers Realtime Database (pour temps réel)
            if data_type == "metrics":
                # Métriques temps réel dans Realtime DB
                metrics_ref = self.db_ref.child(f'realtime_metrics/{self.session_id}') # type: ignore
                for data in batch_data:
                    metrics_ref.child(str(int(time.time()))).set(data)
            
            self.logger.debug(f"🔥 Batch {data_type} uploadé: {len(batch_data)} entrées")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur upload batch {data_type}: {e}")
            # Remettre les données en queue en cas d'erreur
            for data in batch_data:
                queue.put(data)

    # =================== MÉTHODES DE LOGGING ===================

    def should_log_to_firebase(self, level: str, message: str, module: str) -> bool:
        """Détermine si un log doit aller vers Firebase (filtrage intelligent)"""
        
        # Toujours logger les événements critiques
        critical_keywords = [
            "Trade", "Position", "Signal détecté", "Erreur", "HORS HORAIRES", 
            "démarré", "Capital", "Stop Loss", "Take Profit", "fermé", "ouvert",
            "Scan des paires", "Top", "sélectionnées", "insuffisant", "bloqué",
            "P&L", "Trailing Stop", "Surexposition", "Timeout", "Momentum"
        ]
        
        # Événements importants à logger
        if any(keyword in message for keyword in critical_keywords):
            return True
        
        # Tous les WARNING et ERROR
        if level in ["ERROR", "WARNING"]:
            return True
            
        # Logs de démarrage/arrêt
        if module in ["main", "trading_hours", "firebase_logger"]:
            return True
        
        # Filtrer le spam de debug
        spam_keywords = [
            "Batch uploadé", "debug", "Vérification simple", "Thread upload",
            "Collection nettoyée", "Test connexion"
        ]
        if any(keyword in message for keyword in spam_keywords):
            return False
        
        # Par défaut, logger les INFO importantes
        return level in ["INFO", "WARNING", "ERROR"]

    def log_message(self, level: str, message: str, module: str = "bot", 
                   trade_id: Optional[str] = None, pair: Optional[str] = None, 
                   capital: Optional[float] = None, additional_data: Optional[Dict] = None):
        """Log un message avec contexte et filtrage intelligent"""
        if not FIREBASE_CONFIG.ENABLE_FIREBASE_LOGGING:
            return

        # Filtrage intelligent pour éviter le spam
        if not self.should_log_to_firebase(level, message, module):
            return

        log_entry = LogEntry(
            timestamp=get_paris_time_iso(),
            level=level,
            message=message,
            bot_module=module,
            session_id=self.session_id,
            trade_id=trade_id,
            pair=pair,
            capital=capital,
            additional_data=additional_data
        )
        
        self.logs_queue.put(asdict(log_entry))

    def log_trade(self, trade_data: Dict):
        """Log un trade complet"""
        if not FIREBASE_CONFIG.ENABLE_TRADES_LOGGING:
            return

        # Conversion en TradeEntry
        trade_entry = TradeEntry(
            trade_id=trade_data.get('trade_id', ''),
            timestamp=trade_data.get('timestamp', get_paris_time_iso()),
            pair=trade_data.get('pair', ''),
            direction=trade_data.get('direction', ''),
            action=trade_data.get('action', ''),
            entry_price=trade_data.get('entry_price', 0.0),
            exit_price=trade_data.get('exit_price'),
            size=trade_data.get('size', 0.0),
            stop_loss=trade_data.get('stop_loss', 0.0),
            take_profit=trade_data.get('take_profit', 0.0),
            pnl_gross=trade_data.get('pnl_gross'),
            pnl_net=trade_data.get('pnl_net'),
            fees=trade_data.get('fees'),
            duration_seconds=trade_data.get('duration_seconds'),
            exit_reason=trade_data.get('exit_reason'),
            capital_before=trade_data.get('capital_before', 0.0),
            capital_after=trade_data.get('capital_after', 0.0),
            session_trading=trade_data.get('session_trading', ''),
            volatility=trade_data.get('volatility'),
            volume_24h=trade_data.get('volume_24h'),
            spread_percent=trade_data.get('spread_percent'),
            signals=trade_data.get('signals')
        )
        
        self.trades_queue.put(asdict(trade_entry))

    def log_performance(self, performance_data: Dict):
        """Log les performances"""
        if not FIREBASE_CONFIG.ENABLE_PERFORMANCE_LOGGING:
            return

        perf_entry = PerformanceEntry(
            timestamp=get_paris_time_iso(),
            session_id=self.session_id,
            total_capital=performance_data.get('total_capital', 0.0),
            daily_pnl=performance_data.get('daily_pnl', 0.0),
            daily_trades=performance_data.get('daily_trades', 0),
            win_rate=performance_data.get('win_rate', 0.0),
            total_fees=performance_data.get('total_fees', 0.0),
            open_positions=performance_data.get('open_positions', 0),
            best_pair=performance_data.get('best_pair'),
            worst_pair=performance_data.get('worst_pair'),
            trading_session=performance_data.get('trading_session', ''),
            market_volatility=performance_data.get('market_volatility')
        )
        
        self.performance_queue.put(asdict(perf_entry))

    def log_metric(self, metric_type: str, value: float, pair: Optional[str] = None, 
                  additional_info: Optional[Dict] = None):
        """Log une métrique temps réel"""
        metric_entry = MetricEntry(
            timestamp=get_paris_time_iso(),
            metric_type=metric_type,
            value=value,
            pair=pair,
            additional_info=additional_info
        )
        
        self.metrics_queue.put(asdict(metric_entry))

    def log_pair_scan_result(self, scan_data: Dict):
        """Log les résultats de scan des paires dans une collection dédiée"""
        if not FIREBASE_CONFIG.ENABLE_FIREBASE_LOGGING:
            return

        # Structure spécifique pour les résultats de scan
        scan_result = {
            "timestamp": get_paris_time_iso(),
            "session_id": self.session_id,
            "pair": scan_data.get("pair", ""),
            "decision": scan_data.get("final_decision", "UNKNOWN"),
            "reason": scan_data.get("reason", ""),
            "price": scan_data.get("price", 0),
            "volume_24h": scan_data.get("volume_24h", 0),
            "spread_pct": scan_data.get("spread_pct", 0),
            "volatility_1h_pct": scan_data.get("volatility_1h_pct", 0),
            "volatility_24h_pct": scan_data.get("volatility_24h_pct", 0),
            "signal_score": scan_data.get("signal_score", 0),
            "conditions": scan_data.get("conditions", {}),
            "config_thresholds": {
                "min_volume": scan_data.get("config_min_volume", 0),
                "max_spread": scan_data.get("config_max_spread", 0),
                "min_volatility_1h": scan_data.get("config_min_volatility_1h", 0),
                "min_signal_conditions": scan_data.get("config_min_signal_conditions", 0)
            }
        }
        
        # Upload direct dans la collection dédiée (pas via queue pour la rapidité)
        if self.firebase_initialized and self.firestore_db:
            try:
                self.firestore_db.collection("result_pair_scan").add(scan_result)
            except Exception as e:
                self.logger.error(f"❌ Erreur upload scan result: {e}")

    def log_scan_summary(self, summary_data: Dict):
        """Log le résumé global d'un scan de paires"""
        if not FIREBASE_CONFIG.ENABLE_FIREBASE_LOGGING:
            return

        summary_result = {
            "timestamp": get_paris_time_iso(),
            "session_id": self.session_id,
            "scan_type": "SUMMARY",
            "total_pairs": summary_data.get("total_pairs", 0),
            "validated_pairs": summary_data.get("validated_pairs", 0),
            "rejected_pairs": summary_data.get("rejected_pairs", 0),
            "exclusion_stats": summary_data.get("exclusion_stats", {}),
            "config_thresholds": summary_data.get("config_thresholds", {}),
            "scan_duration_ms": summary_data.get("scan_duration_ms", 0)
        }
        
        # Upload direct dans la collection dédiée
        if self.firebase_initialized and self.firestore_db:
            try:
                self.firestore_db.collection("result_pair_scan").add(summary_result)
            except Exception as e:
                self.logger.error(f"❌ Erreur upload scan summary: {e}")

    # =================== MÉTHODES DE REQUÊTE ===================

    def get_recent_trades(self, limit: int = 50, pair: Optional[str] = None) -> List[Dict]:
        """Récupère les trades récents"""
        if not self.firebase_initialized:
            return []

        try:
            query = self.firestore_db.collection(FIREBASE_CONFIG.TRADES_COLLECTION) \
                .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                .limit(limit)
            
            if pair:
                query = query.where('pair', '==', pair)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération trades: {e}")
            return []

    def get_performance_summary(self, days: int = 7) -> Dict:
        """Récupère un résumé de performance"""
        if not self.firebase_initialized:
            return {}

        try:
            since = datetime.now() - timedelta(days=days)
            
            query = self.firestore_db.collection(FIREBASE_CONFIG.PERFORMANCE_COLLECTION) \
                .where('timestamp', '>=', since.isoformat()) \
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            docs = list(query.stream())
            
            if not docs:
                return {}
            
            # Calcul du résumé
            performances = [doc.to_dict() for doc in docs]
            latest = performances[0]
            
            total_pnl = sum(p.get('daily_pnl', 0) for p in performances) # type: ignore
            total_trades = sum(p.get('daily_trades', 0) for p in performances) # type: ignore
            avg_capital = sum(p.get('total_capital', 0) for p in performances) / len(performances) # type: ignore
            
            return {
                'period_days': days,
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'average_capital': avg_capital,
                'current_capital': latest.get('total_capital', 0), # type: ignore
                'latest_win_rate': latest.get('win_rate', 0), # type: ignore
                'roi_percent': (total_pnl / avg_capital * 100) if avg_capital > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur résumé performance: {e}")
            return {}

    def get_pair_analytics(self, pair: str, days: int = 30) -> Dict:
        """Analytics détaillés pour une paire"""
        if not self.firebase_initialized:
            return {}

        try:
            since = datetime.now() - timedelta(days=days)
            
            # Trades pour cette paire
            query = self.firestore_db.collection(FIREBASE_CONFIG.TRADES_COLLECTION) \
                .where('pair', '==', pair) \
                .where('timestamp', '>=', since.isoformat()) \
                .where('action', '==', 'CLOSE')
            
            trades = [doc.to_dict() for doc in query.stream()]
            
            if not trades:
                return {'pair': pair, 'trades_count': 0}
            
            # Calculs
            total_trades = len(trades)
            pnl_values = [t.get('pnl_net', 0) for t in trades if t.get('pnl_net') is not None]
            
            winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
            total_pnl = sum(pnl_values)
            total_fees = sum(t.get('fees', 0) for t in trades)
            
            durations = [t.get('duration_seconds', 0) for t in trades if t.get('duration_seconds')]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'pair': pair,
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'total_fees': total_fees,
                'pnl_net': total_pnl - total_fees,
                'average_duration_minutes': avg_duration / 60,
                'best_trade': max(pnl_values) if pnl_values else 0,
                'worst_trade': min(pnl_values) if pnl_values else 0,
                'profit_factor': self._calculate_profit_factor(pnl_values)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analytics paire {pair}: {e}")
            return {}

    def _calculate_profit_factor(self, pnl_values: List[float]) -> float:
        """Calcule le profit factor"""
        if not pnl_values:
            return 0
        
        gross_profit = sum(pnl for pnl in pnl_values if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in pnl_values if pnl < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    def cleanup_old_data(self):
        """Nettoie les anciennes données selon la rétention"""
        if not self.firebase_initialized:
            return

        try:
            now = datetime.now()
            
            # Cleanup logs
            logs_cutoff = now - timedelta(days=FIREBASE_CONFIG.LOGS_RETENTION_DAYS)
            self._cleanup_collection(FIREBASE_CONFIG.LOGS_COLLECTION, logs_cutoff)
            
            # Cleanup performance
            perf_cutoff = now - timedelta(days=FIREBASE_CONFIG.PERFORMANCE_RETENTION_DAYS)
            self._cleanup_collection(FIREBASE_CONFIG.PERFORMANCE_COLLECTION, perf_cutoff)
            
            self.logger.info("🔥 Nettoyage Firebase effectué")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage Firebase: {e}")

    def _cleanup_collection(self, collection_name: str, cutoff_date: datetime):
        """Nettoie une collection"""
        try:
            query = self.firestore_db.collection(collection_name) \
                .where('timestamp', '<', cutoff_date.isoformat())
            
            docs = query.stream()
            
            batch = self.firestore_db.batch() # type: ignore
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                if count >= 500:  # Limite de batch Firestore
                    batch.commit()
                    batch = self.firestore_db.batch() # type: ignore
                    count = 0
            
            if count > 0:
                batch.commit()
                
            self.logger.debug(f"🔥 Collection {collection_name} nettoyée")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage collection {collection_name}: {e}")

    def stop(self):
        """Arrête le logger Firebase"""
        self.stop_upload = True
        if self.upload_thread:
            self.upload_thread.join(timeout=5)
        self.logger.info("🔥 Firebase Logger arrêté")

# Instance globale
firebase_logger = FirebaseLogger()
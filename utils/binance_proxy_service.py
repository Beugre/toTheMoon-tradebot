"""
Service Proxy Binance pour VPS - Collecte données et stockage Firebase
Contourne les restrictions IP en exécutant depuis le VPS européen
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import firebase_admin
from binance.client import Client
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


class BinanceProxyService:
    """Service proxy pour collecter données Binance et les stocker dans Firebase"""
    
    def __init__(self):
        self.setup_logging()
        self.setup_binance_client()
        self.setup_firebase()
        self.monitored_pairs = []  # Sera rempli dynamiquement
        self.running = False
        
    def setup_logging(self):
        """Configuration du logging"""
        # Déterminer le répertoire de logs selon l'environnement
        possible_log_dirs = [
            '/opt/toTheMoon_tradebot/logs',  # VPS
            'logs',  # Répertoire local
            '../logs'  # Répertoire parent
        ]
        
        log_dir = None
        for log_path in possible_log_dirs:
            try:
                os.makedirs(log_path, exist_ok=True)
                log_dir = log_path
                break
            except (OSError, PermissionError):
                continue
        
        # Si aucun répertoire de logs n'est accessible, utiliser seulement console
        handlers = [logging.StreamHandler()]
        
        if log_dir:
            log_file = os.path.join(log_dir, 'binance_proxy.log')
            try:
                handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
            except (OSError, PermissionError):
                pass  # Ignorer si impossible d'écrire le fichier
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers,
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        if log_dir:
            self.logger.info(f"[LOG] Logging configure - Repertoire: {log_dir}")
        else:
            self.logger.info("[LOG] Logging configure - Console seulement")
        
    def setup_binance_client(self):
        """Configuration du client Binance depuis VPS"""
        try:
            # Charger .env depuis différents emplacements possibles
            possible_env_paths = [
                '/opt/toTheMoon_tradebot/.env',  # VPS
                '.env',  # Répertoire courant
                '../.env'  # Répertoire parent (si dans utils/)
            ]
            
            env_loaded = False
            for env_path in possible_env_paths:
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    self.logger.info(f"[OK] Fichier .env charge depuis: {env_path}")
                    env_loaded = True
                    break
            
            if not env_loaded:
                self.logger.warning("[WARN] Aucun fichier .env trouve, utilisation variables systeme")
                load_dotenv()  # Fallback sur variables système
            
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_SECRET_KEY')
            
            if not api_key or not api_secret:
                raise ValueError("[ERROR] Cles API Binance manquantes dans .env")
                
            self.binance_client = Client(
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Test de connexion
            account = self.binance_client.get_account()
            self.logger.info(f"[OK] Binance connecte - Type: {account.get('accountType', 'UNKNOWN')}")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur connexion Binance: {e}")
            raise
            
    def setup_firebase(self):
        """Configuration Firebase depuis VPS"""
        try:
            # Essayer de récupérer une app Firebase existante
            try:
                app = firebase_admin.get_app()
                self.firebase_db = firestore.client(app)
                self.logger.info("[FIREBASE] App reutilisee")
            except ValueError:
                # Initialiser nouvelle app Firebase
                cred = credentials.Certificate('/opt/toTheMoon_tradebot/firebase_credentials.json')
                app = firebase_admin.initialize_app(cred)
                self.firebase_db = firestore.client(app)
                self.logger.info("[FIREBASE] Initialise avec succes")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur Firebase: {e}")
            raise

    def discover_usdc_pairs_with_activity(self, hours_back: int = 24) -> List[str]:
        """Découvre toutes les paires USDC avec activité récente"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Récupérer toutes les paires USDC d'abord
            all_usdc_pairs = self.get_all_usdc_pairs_from_exchange()
            usdc_pairs_with_activity = set()
            
            # Vérifier l'activité pour chaque paire USDC (échantillonnage)
            for symbol in all_usdc_pairs[:20]:  # Limiter à 20 paires pour éviter les limites de rate
                try:
                    trades = self.binance_client.get_my_trades(
                        symbol=symbol,
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        limit=10  # Juste vérifier s'il y a de l'activité
                    )
                    
                    if trades:  # Si il y a des trades sur cette paire
                        usdc_pairs_with_activity.add(symbol)
                        
                except Exception as e:
                    # Ignorer les erreurs par paire (paire pas autorisée, etc.)
                    continue
            
            usdc_pairs_list = sorted(list(usdc_pairs_with_activity))
            
            if usdc_pairs_list:
                self.logger.info(f"[DISCOVERY] Decouvert {len(usdc_pairs_list)} paires USDC avec activite: {usdc_pairs_list}")
            else:
                self.logger.warning("[WARN] Aucune paire USDC avec activite detectee - Utilisation des paires par defaut")
                # Fallback sur quelques paires principales
                usdc_pairs_list = ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'SOLUSDC']
            
            return usdc_pairs_list
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur decouverte paires USDC: {e}")
            # Fallback sur les paires principales
            return ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'SOLUSDC']

    def get_all_usdc_pairs_from_exchange(self) -> List[str]:
        """Récupère toutes les paires USDC disponibles sur Binance"""
        try:
            exchange_info = self.binance_client.get_exchange_info()
            usdc_pairs = []
            
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info['symbol']
                if (symbol.endswith('USDC') and 
                    symbol_info['status'] == 'TRADING' and
                    symbol_info['quoteAsset'] == 'USDC'):
                    usdc_pairs.append(symbol)
            
            self.logger.info(f"[EXCHANGE] Trouve {len(usdc_pairs)} paires USDC actives sur Binance")
            return sorted(usdc_pairs)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur recuperation paires exchange: {e}")
            return []

    def update_monitored_pairs(self):
        """Met à jour la liste des paires surveillées"""
        try:
            # Méthode 1: Paires avec activité récente (priorité)
            active_pairs = self.discover_usdc_pairs_with_activity(hours_back=48)
            
            # Méthode 2: Toutes les paires USDC si peu d'activité
            if len(active_pairs) < 10:  # Si moins de 10 paires actives
                all_usdc_pairs = self.get_all_usdc_pairs_from_exchange()
                # Limiter à 50 paires max pour éviter la surcharge
                if len(all_usdc_pairs) > 50:
                    # Prendre les 50 paires avec le plus gros volume (approximation par ordre alphabétique + principales)
                    priority_pairs = [p for p in all_usdc_pairs if any(coin in p for coin in ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE'])]
                    other_pairs = [p for p in all_usdc_pairs if p not in priority_pairs]
                    all_usdc_pairs = priority_pairs + other_pairs[:50-len(priority_pairs)]
                
                # Fusionner avec les paires actives
                active_pairs = sorted(list(set(active_pairs + all_usdc_pairs)))
            
            self.monitored_pairs = active_pairs
            self.logger.info(f"[OK] Surveillance mise a jour: {len(self.monitored_pairs)} paires USDC")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur mise a jour paires surveillees: {e}")
            # Fallback sécurisé
            self.monitored_pairs = ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'SOLUSDC']

    async def collect_account_info(self):
        """Collecte les informations de compte Binance"""
        try:
            account = self.binance_client.get_account()
            
            # Filtrer les balances > 0
            balances = []
            for balance in account['balances']:
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if total_balance > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free_balance,
                        'locked': locked_balance,
                        'total': total_balance
                    })
            
            account_data = {
                'timestamp': datetime.now().isoformat(),
                'balances': balances,
                'canTrade': account.get('canTrade', False),
                'canWithdraw': account.get('canWithdraw', False),
                'accountType': account.get('accountType', 'UNKNOWN'),
                'collected_at': firestore.SERVER_TIMESTAMP
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('account_info').set(account_data)
            self.logger.info(f"[OK] Account info mise a jour - {len(balances)} balances")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte account info: {e}")

    async def collect_recent_trades(self, hours_back: int = 24):
        """Collecte les trades récents pour toutes les paires USDC surveillées"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Si pas de paires définies, les découvrir
            if not self.monitored_pairs:
                self.update_monitored_pairs()
            
            all_trades = []
            
            for symbol in self.monitored_pairs:
                try:
                    trades = self.binance_client.get_my_trades(
                        symbol=symbol,
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000)
                    )
                    
                    for trade in trades:
                        all_trades.append({
                            'symbol': symbol,
                            'time': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                            'side': 'BUY' if trade['isBuyer'] else 'SELL',
                            'price': float(trade['price']),
                            'qty': float(trade['qty']),
                            'quoteQty': float(trade['quoteQty']),
                            'orderId': str(trade['orderId']),
                            'commission': float(trade['commission']),
                            'commissionAsset': trade['commissionAsset']
                        })
                        
                except Exception as e:
                    self.logger.warning(f"[WARN] Erreur recuperation trades {symbol}: {e}")
                    continue
            
            trades_data = {
                'timestamp': datetime.now().isoformat(),
                'trades': all_trades,
                'pairs_detected': self.monitored_pairs,
                'total_trades': len(all_trades),
                'collection_method': 'per_pair_discovery',
                'collected_at': firestore.SERVER_TIMESTAMP
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('recent_trades').set(trades_data)
            self.logger.info(f"[OK] Trades USDC mis a jour - {len(all_trades)} trades sur {len(self.monitored_pairs)} paires")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte trades USDC: {e}")

    async def collect_open_orders(self):
        """Collecte les ordres ouverts pour toutes les paires USDC actives"""
        try:
            # Si pas de paires définies, les découvrir
            if not self.monitored_pairs:
                self.update_monitored_pairs()
            
            all_orders = []
            
            for symbol in self.monitored_pairs:
                try:
                    orders = self.binance_client.get_open_orders(symbol=symbol)
                    
                    for order in orders:
                        all_orders.append({
                            'symbol': order['symbol'],
                            'orderId': str(order['orderId']),
                            'side': order['side'],
                            'type': order['type'],
                            'status': order['status'],
                            'price': float(order['price']) if order['price'] != '0.00000000' else 0,
                            'origQty': float(order['origQty']),
                            'executedQty': float(order['executedQty']),
                            'time': datetime.fromtimestamp(order['time'] / 1000).isoformat(),
                            'updateTime': datetime.fromtimestamp(order['updateTime'] / 1000).isoformat()
                        })
                        
                except Exception as e:
                    self.logger.warning(f"[WARN] Erreur recuperation ordres {symbol}: {e}")
                    continue
            
            orders_data = {
                'timestamp': datetime.now().isoformat(),
                'orders': all_orders,
                'pairs_monitored': self.monitored_pairs,
                'total_orders': len(all_orders),
                'collected_at': firestore.SERVER_TIMESTAMP
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('open_orders').set(orders_data)
            self.logger.info(f"[OK] Ordres ouverts mis a jour - {len(all_orders)} ordres sur {len(self.monitored_pairs)} paires")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte ordres ouverts: {e}")

    async def cleanup_old_data(self):
        """Nettoyage des données Firebase anciennes (> 48h)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=48)
            
            # Note: Pour cette version, on garde seulement les 3 derniers documents
            # Le cleanup automatique se fait par rotation plutôt que par timestamp
            # car nous n'avons qu'un document par type mis à jour en continu
            
            self.logger.info("[CLEANUP] Donnees rotees automatiquement par mise a jour")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur cleanup: {e}")

    async def health_check(self):
        """Vérification de l'état du service"""
        try:
            # Test Binance
            self.binance_client.get_server_time()
            
            # Test Firebase
            self.firebase_db.collection('binance_live').document('health').set({
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'service': 'binance_proxy',
                'last_health_check': firestore.SERVER_TIMESTAMP
            })
            
            self.logger.info("[HEALTH] Health check OK - Service operationnel")
            
        except Exception as e:
            self.logger.error(f"[HEALTH] Health check FAILED: {e}")

    async def run_collection_cycle(self):
        """Cycle complet de collecte de données"""
        try:
            self.logger.info("[CYCLE] Debut cycle de collecte")
            
            # Collecte parallèle des données
            await asyncio.gather(
                self.collect_account_info(),
                self.collect_recent_trades(),
                self.collect_open_orders(),
                return_exceptions=True
            )
            
            self.logger.info("[CYCLE] Cycle de collecte termine")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur cycle de collecte: {e}")

    async def start_service(self):
        """Démarrage du service principal"""
        self.logger.info("[START] Demarrage du service Binance Proxy")
        self.running = True
        
        # Health check initial
        await self.health_check()
        
        # Découverte initiale des paires USDC
        self.update_monitored_pairs()
        
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                self.logger.info(f"[CYCLE] Cycle #{cycle_count}")
                
                # Cycle de collecte principal
                await self.run_collection_cycle()
                
                # Health check périodique (toutes les 10 cycles = 10 minutes)
                if cycle_count % 10 == 0:
                    await self.health_check()
                
                # Cleanup périodique (toutes les 60 cycles = 1 heure)
                if cycle_count % 60 == 0:
                    await self.cleanup_old_data()
                
                # Redécouverte des paires (toutes les 12 cycles = 12 minutes)
                if cycle_count % 12 == 0:
                    self.update_monitored_pairs()
                
                # Attente avant prochain cycle (60 secondes)
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("[STOP] Arret demande par l'utilisateur")
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur critique dans le service: {e}")
        finally:
            self.running = False
            self.logger.info("[STOP] Service Binance Proxy arrete")

    def stop_service(self):
        """Arrêt du service"""
        self.logger.info("[STOP] Demande d'arret du service")
        self.running = False


async def main():
    """Point d'entrée principal"""
    service = BinanceProxyService()
    
    try:
        await service.start_service()
    except Exception as e:
        logging.error(f"[ERROR] Erreur fatale: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

"""
Auditeur de trades sans dépendances Streamlit pour les tests
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
from binance.client import Client


class TradeAuditorSimple:
    """Auditeur simple pour comparer les trades Binance vs Firebase (sans Streamlit)"""
    
    def __init__(self, binance_client: Client, firebase_db):
        self.binance_client = binance_client
        self.firebase_db = firebase_db
        
    def get_binance_trades(self, symbols: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Récupère l'historique des trades depuis Binance"""
        all_trades = []
        
        for symbol in symbols:
            try:
                trades = self.binance_client.get_my_trades(
                    symbol=symbol,
                    startTime=int(start_date.timestamp() * 1000),
                    endTime=int(end_date.timestamp() * 1000)
                )
                
                for trade in trades:
                    trade['symbol'] = symbol
                    all_trades.append(trade)
                    
            except Exception as e:
                print(f"❌ Erreur récupération trades {symbol}: {e}")
                continue
        
        if not all_trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_trades)
        
        # Conversion et nettoyage
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['price'] = pd.to_numeric(df['price'])
        df['qty'] = pd.to_numeric(df['qty'])
        df['commission'] = pd.to_numeric(df['commission'])
        df['quoteQty'] = pd.to_numeric(df['quoteQty'])
        
        # 🎯 AJOUT: Identification du type de trade
        df['trade_type'] = df['isBuyer'].apply(lambda x: 'BUY' if x else 'SELL')
        
        # 🔧 GROUPEMENT des trades fragmentés par orderId
        return self._aggregate_fragmented_trades(df)
    
    def _aggregate_fragmented_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrège les trades fragmentés par orderId en trades unifiés"""
        if df.empty:
            return df
        
        aggregated_trades = []
        
        # Grouper par symbol, orderId et trade_type
        for (symbol, order_id, trade_type), group in df.groupby(['symbol', 'orderId', 'trade_type']):
            if len(group) == 1:
                # Trade non fragmenté - garder tel quel
                trade = group.iloc[0].to_dict()
                # Ajouter les clés de matching
                trade['time_rounded'] = pd.to_datetime(trade['time']).round('1min')
                trade['match_key'] = f"{symbol}_{order_id}_{int(pd.to_datetime(trade['time']).timestamp())}"
                trade['pair_time_key'] = f"{symbol}_{int(trade['time_rounded'].timestamp())}"
                trade['fragment_count'] = 1
                aggregated_trades.append(trade)
            else:
                # Trade fragmenté - agréger
                aggregated_trade = {
                    'symbol': symbol,
                    'orderId': order_id,
                    'trade_type': trade_type,
                    'time': group['time'].min(),  # Premier fragment
                    'price': (group['price'] * group['qty']).sum() / group['qty'].sum(),  # Prix moyen pondéré
                    'qty': group['qty'].sum(),  # Quantité totale
                    'quoteQty': group['quoteQty'].sum(),  # Valeur totale
                    'commission': group['commission'].sum(),  # Commission totale
                    'commissionAsset': group['commissionAsset'].iloc[0],
                    'isBuyer': group['isBuyer'].iloc[0],
                    'fragment_count': len(group)
                }
                
                # Ajouter les clés de matching
                aggregated_trade['time_rounded'] = pd.to_datetime(aggregated_trade['time']).round('1min')
                aggregated_trade['match_key'] = f"{symbol}_{order_id}_{int(pd.to_datetime(aggregated_trade['time']).timestamp())}"
                aggregated_trade['pair_time_key'] = f"{symbol}_{int(aggregated_trade['time_rounded'].timestamp())}"
                
                aggregated_trades.append(aggregated_trade)
        
        if not aggregated_trades:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(aggregated_trades)
        
        # Reconvertir les types
        result_df['time'] = pd.to_datetime(result_df['time'])
        result_df['time_rounded'] = pd.to_datetime(result_df['time_rounded'])
        
        print(f"🔧 Agrégation: {len(df)} fragments → {len(result_df)} trades unifiés")
        
        return result_df
    
    def get_firebase_trades(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Récupère les trades depuis Firebase"""
        try:
            docs = self.firebase_db.collection("trades").where(
                "timestamp", ">=", start_date.isoformat()
            ).where(
                "timestamp", "<=", end_date.isoformat()
            ).stream()
            
            data = []
            for doc in docs:
                trade_data = doc.to_dict()
                trade_data['doc_id'] = doc.id
                data.append(trade_data)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Nettoyage et conversion
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['entry_price'] = pd.to_numeric(df['entry_price'], errors='coerce')
            df['size'] = pd.to_numeric(df['size'], errors='coerce')
            df['pnl_amount'] = pd.to_numeric(df.get('pnl_amount', 0), errors='coerce')
            
            # Clé de matching
            df['match_key'] = df.apply(lambda row: self._create_firebase_match_key(row), axis=1)
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur récupération Firebase: {e}")
            return pd.DataFrame()
    
    def _create_firebase_match_key(self, row) -> str:
        """Crée une clé de matching pour Firebase"""
        # Utilisation de plusieurs stratégies de matching
        binance_id = row.get('binance_order_id', 'UNKNOWN')
        timestamp = int(pd.to_datetime(row['timestamp']).timestamp())
        
        # Clé principale avec ID Binance
        if binance_id and binance_id != 'UNKNOWN':
            return f"{row['pair']}_{binance_id}_{timestamp}"
        
        # Clé alternative par paire et temps (pour les cas sans binance_order_id)
        time_rounded = pd.to_datetime(row['timestamp']).round('1min')
        return f"{row['pair']}_{int(time_rounded.timestamp())}_FIREBASE"
    
    def compare_trades(self, binance_df: pd.DataFrame, firebase_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Compare les trades entre Binance et Firebase avec matching intelligent"""
        # Cas où les deux DataFrames sont vides
        if binance_df.empty and firebase_df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Cas où seul Binance est vide
        if binance_df.empty:
            return pd.DataFrame(), pd.DataFrame(), firebase_df.copy()
        
        # Cas où seul Firebase est vide
        if firebase_df.empty:
            return pd.DataFrame(), binance_df.copy(), pd.DataFrame()
        
        # 🎯 MATCHING INTELLIGENT basé sur prix et timestamps
        matched_pairs = []
        unmatched_binance = binance_df.copy()
        unmatched_firebase = firebase_df.copy()
        
        # Pour chaque trade Firebase, chercher le meilleur match Binance
        for fb_idx, fb_trade in firebase_df.iterrows():
            best_match = self._find_best_binance_match(fb_trade, binance_df)
            
            if best_match is not None:
                # Créer une ligne matchée
                matched_row = {
                    # Données Binance
                    'symbol_binance': best_match['symbol'],
                    'orderId_binance': best_match['orderId'],
                    'time_binance': best_match['time'],
                    'price_binance': best_match['price'],
                    'qty_binance': best_match['qty'],
                    'trade_type_binance': best_match['trade_type'],
                    'fragment_count_binance': best_match.get('fragment_count', 1),
                    
                    # Données Firebase
                    'pair_firebase': fb_trade['pair'],
                    'timestamp_firebase': fb_trade['timestamp'],
                    'entry_price_firebase': fb_trade.get('entry_price'),
                    'exit_price_firebase': fb_trade.get('exit_price'),
                    'action_firebase': fb_trade.get('action'),
                    'trade_id_firebase': fb_trade.get('trade_id'),
                    
                    # Métadonnées de matching
                    'match_confidence': best_match.get('match_confidence', 0),
                    'price_diff_percent': best_match.get('price_diff_percent', 0),
                    'time_diff_minutes': best_match.get('time_diff_minutes', 0)
                }
                
                matched_pairs.append(matched_row)
                
                # Retirer des non-matchés
                unmatched_binance = unmatched_binance[unmatched_binance['orderId'] != best_match['orderId']]
                unmatched_firebase = unmatched_firebase.drop(fb_idx)
        
        # Convertir en DataFrames
        matched_df = pd.DataFrame(matched_pairs) if matched_pairs else pd.DataFrame()
        
        return matched_df, unmatched_binance, unmatched_firebase
    
    def _find_best_binance_match(self, firebase_trade: pd.Series, binance_df: pd.DataFrame) -> Optional[dict]:
        """Trouve le meilleur match Binance pour un trade Firebase"""
        pair = firebase_trade['pair']
        fb_timestamp = pd.to_datetime(firebase_trade['timestamp'])
        fb_action = firebase_trade.get('action', 'UNKNOWN')
        fb_price = firebase_trade.get('exit_price' if fb_action == 'SELL' else 'entry_price')
        
        if fb_price is None:
            return None
        
        # Filtrer les trades Binance par paire et type
        binance_type = 'SELL' if fb_action == 'SELL' else 'BUY'
        candidates = binance_df[
            (binance_df['symbol'] == pair) & 
            (binance_df['trade_type'] == binance_type)
        ].copy()
        
        if candidates.empty:
            return None
        
        best_match = None
        best_score = 0
        
        for _, candidate in candidates.iterrows():
            # Calcul de la différence de prix (%)
            price_diff_percent = abs(candidate['price'] - fb_price) / fb_price * 100
            
            # Calcul de la différence de temps (minutes)
            time_diff_minutes = abs((candidate['time'] - fb_timestamp).total_seconds()) / 60
            
            # Score de matching (plus c'est proche, plus le score est élevé)
            price_score = max(0, 100 - price_diff_percent * 10)  # Pénalité forte sur prix
            time_score = max(0, 100 - time_diff_minutes / 60 * 10)  # Pénalité sur temps
            
            # Score global (pondéré : prix 70%, temps 30%)
            global_score = price_score * 0.7 + time_score * 0.3
            
            # Conditions de matching strictes
            if (price_diff_percent <= 2.0 and  # Prix dans 2%
                time_diff_minutes <= 240 and  # Temps dans 4h
                global_score > best_score):
                
                best_match = candidate.to_dict()
                best_match['match_confidence'] = global_score
                best_match['price_diff_percent'] = price_diff_percent
                best_match['time_diff_minutes'] = time_diff_minutes
                best_score = global_score
        
        return best_match
    
    def analyze_trading_cycles(self, binance_df: pd.DataFrame, firebase_df: pd.DataFrame) -> Dict:
        """Analyse les cycles de trading complets vs incomplets"""
        analysis = {
            'binance_buy_orders': 0,
            'binance_sell_orders': 0,
            'firebase_open_trades': 0,
            'firebase_close_trades': 0,
            'incomplete_cycles': [],
            'orphaned_closes': 0,  # Trades CLOSE sans OPEN correspondant
            'orphaned_opens': 0    # Trades OPEN sans CLOSE correspondant
        }
        
        if not binance_df.empty:
            analysis['binance_buy_orders'] = len(binance_df[binance_df['trade_type'] == 'BUY'])
            analysis['binance_sell_orders'] = len(binance_df[binance_df['trade_type'] == 'SELL'])
        
        if not firebase_df.empty:
            # Compter les actions Firebase (BUY/SELL au lieu d'OPEN/CLOSE)
            open_trades = firebase_df[firebase_df.get('action') == 'BUY']
            close_trades = firebase_df[firebase_df.get('action') == 'SELL']
            
            analysis['firebase_open_trades'] = len(open_trades)
            analysis['firebase_close_trades'] = len(close_trades)
            
            # 🔍 DÉTECTION: Trades SELL orphelins (sans BUY correspondant)
            for idx, sell_trade in close_trades.iterrows():
                pair = sell_trade.get('pair')
                sell_time = pd.to_datetime(sell_trade['timestamp'])
                trade_id_base = sell_trade.get('trade_id', '').split('_')[0] if sell_trade.get('trade_id') else None
                
                # Chercher un BUY correspondant (même trade_id de base ou fenêtre temporelle)
                matching_buys = []
                for _, buy_trade in open_trades.iterrows():
                    buy_trade_id = buy_trade.get('trade_id', '')
                    if (buy_trade.get('pair') == pair and 
                        ((trade_id_base and buy_trade_id.startswith(trade_id_base)) or
                         abs((pd.to_datetime(buy_trade['timestamp']) - sell_time).total_seconds()) < 7200)):
                        matching_buys.append(buy_trade)
                
                if len(matching_buys) == 0:
                    analysis['incomplete_cycles'].append({
                        'type': 'ORPHANED_CLOSE',
                        'pair': pair,
                        'close_time': sell_time,
                        'entry_price': sell_trade.get('entry_price'),
                        'exit_price': sell_trade.get('exit_price'),
                        'trade_id': sell_trade.get('trade_id'),
                        'issue': 'SELL_WITHOUT_BUY_IN_FIREBASE'
                    })
                    analysis['orphaned_closes'] += 1
            
            # 🔍 DÉTECTION: Trades BUY orphelins (sans SELL correspondant)
            for idx, buy_trade in open_trades.iterrows():
                pair = buy_trade.get('pair')
                buy_time = pd.to_datetime(buy_trade['timestamp'])
                trade_id_base = buy_trade.get('trade_id', '').split('_')[0] if buy_trade.get('trade_id') else None
                
                # Chercher un SELL correspondant
                matching_sells = []
                for _, sell_trade in close_trades.iterrows():
                    sell_trade_id = sell_trade.get('trade_id', '')
                    if (sell_trade.get('pair') == pair and 
                        ((trade_id_base and sell_trade_id.startswith(trade_id_base)) or
                         pd.to_datetime(sell_trade['timestamp']) > buy_time)):
                        matching_sells.append(sell_trade)
                
                if len(matching_sells) == 0:
                    analysis['incomplete_cycles'].append({
                        'type': 'ORPHANED_OPEN',
                        'pair': pair,
                        'open_time': buy_time,
                        'entry_price': buy_trade.get('entry_price'),
                        'trade_id': buy_trade.get('trade_id'),
                        'issue': 'BUY_WITHOUT_SELL_IN_FIREBASE'
                    })
                    analysis['orphaned_opens'] += 1
        
        return analysis
    
    def calculate_metrics(self, matched: pd.DataFrame, only_binance: pd.DataFrame, only_firebase: pd.DataFrame) -> Dict:
        """Calcule les métriques de cohérence"""
        total_binance = len(matched) + len(only_binance)
        total_firebase = len(matched) + len(only_firebase)
        
        metrics = {
            'total_binance_trades': total_binance,
            'total_firebase_trades': total_firebase,
            'matched_trades': len(matched),
            'missing_in_firebase': len(only_binance),
            'phantom_in_firebase': len(only_firebase),
            'match_rate': (len(matched) / max(total_binance, 1)) * 100,
            'firebase_coverage': (len(matched) / max(total_binance, 1)) * 100,
            'binance_coverage': (len(matched) / max(total_firebase, 1)) * 100
        }
        
        return metrics
        
        return metrics

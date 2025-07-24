"""
Monitoring en temps réel des trades - Interface Streamlit
Surveillance continue directe Binance + Firebase (comme dashboard.py)
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import Firebase direct
import firebase_admin
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from binance.client import Client
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# Charger les variables d'environnement dès le démarrage
load_dotenv()

# Configuration simplifiée pour les clés API (comme dans config.py)
class APIConfig:
    """Configuration des clés API pour Streamlit"""
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")

# Instance globale de la configuration
API_CONFIG = APIConfig()


class RealTimeTradingMonitor:
    """Monitoring en temps réel - Connexion directe Binance + Firebase"""
    
    def __init__(self):
        self.setup_binance_client()
        self.setup_firebase()
        
    def setup_binance_client(self):
        """Configuration du client Binance"""
        try:
            # Essayer d'abord les secrets Streamlit Cloud
            if hasattr(st, 'secrets') and 'binance' in st.secrets:
                api_key = st.secrets['binance']['api_key']
                api_secret = st.secrets['binance']['api_secret']
                st.success("🔑 Binance configuré avec les secrets Streamlit Cloud")
            else:
                # Utiliser la configuration API (comme dashboard.py)
                api_key = API_CONFIG.BINANCE_API_KEY
                api_secret = API_CONFIG.BINANCE_SECRET_KEY
                st.success("🔑 Binance configuré avec APIConfig")
                
                # Debug pour vérifier la récupération
                if api_key:
                    st.info(f"🔍 API Key trouvée: {api_key[:10]}...")
                else:
                    st.warning("⚠️ BINANCE_API_KEY non trouvée dans APIConfig")
                
                if api_secret:
                    st.info(f"🔍 Secret Key trouvée: {api_secret[:10]}...")
                else:
                    st.warning("⚠️ BINANCE_SECRET_KEY non trouvée dans APIConfig")
            
            if not api_key or not api_secret:
                st.error("� Clés manquantes ! Pour Streamlit Cloud, configure les secrets :")
                st.code("""
[binance]
api_key = "ta_clé_api"
api_secret = "ta_clé_secrète"
                """)
                raise ValueError("Clés API Binance manquantes")
                
            self.binance_client = Client(
                api_key=api_key,
                api_secret=api_secret
            )
            st.success("✅ Client Binance initialisé avec succès")
        except Exception as e:
            st.error(f"❌ Erreur Binance: {e}")
            raise
            
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            # Essayer de récupérer une app Firebase existante
            try:
                app = firebase_admin.get_app()
                self.firebase_db = firestore.client(app)
                st.success("🔥 Firebase réutilisé")
            except ValueError:
                # Aucune app existe, donc on peut l'initialiser
                # Essayer d'abord les secrets Streamlit Cloud
                if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                    firebase_credentials = dict(st.secrets['firebase'])
                    cred = credentials.Certificate(firebase_credentials)
                    app = firebase_admin.initialize_app(cred)
                    self.firebase_db = firestore.client(app)
                    st.success("🔥 Firebase initialisé avec les secrets Streamlit Cloud")
                else:
                    # Fallback sur le fichier local
                    cred = credentials.Certificate('firebase_credentials.json')
                    app = firebase_admin.initialize_app(cred)
                    self.firebase_db = firestore.client(app)
                    st.success("🔥 Firebase initialisé avec le fichier local")
                    
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            raise

    def get_recent_binance_trades(self, symbols: List[str], hours_back: int = 24) -> pd.DataFrame:
        """Récupère les trades Binance récents"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        all_trades = []
        
        for symbol in symbols:
            try:
                trades = self.binance_client.get_my_trades(
                    symbol=symbol,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                for trade in trades:
                    all_trades.append({
                        'symbol': symbol,
                        'time': pd.to_datetime(trade['time'], unit='ms'),
                        'side': 'BUY' if trade['isBuyer'] else 'SELL',
                        'price': float(trade['price']),
                        'qty': float(trade['qty']),
                        'quoteQty': float(trade['quoteQty']),
                        'orderId': trade['orderId'],
                        'commission': float(trade['commission'])
                    })
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur récupération {symbol}: {e}")
                continue
        
        return pd.DataFrame(all_trades) if all_trades else pd.DataFrame()

    def get_recent_firebase_trades(self, hours_back: int = 24) -> pd.DataFrame:
        """Récupère les trades Firebase récents"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            docs = self.firebase_db.collection("trades").where(
                "timestamp", ">=", start_time.isoformat()
            ).where(
                "timestamp", "<=", end_time.isoformat()
            ).order_by("timestamp", direction="DESCENDING").stream()
            
            trades = []
            for doc in docs:
                data = doc.to_dict()
                trades.append({
                    'doc_id': doc.id,
                    'pair': data.get('pair'),
                    'timestamp': pd.to_datetime(data.get('timestamp')),
                    'action': data.get('action'),
                    'entry_price': float(data.get('entry_price', 0)),
                    'exit_price': float(data.get('exit_price', 0)),
                    'size': float(data.get('size', 0)),
                    'pnl_amount': float(data.get('pnl_amount', 0)),
                    'trade_id': data.get('trade_id'),
                    'binance_order_id': data.get('binance_order_id')
                })
            
            return pd.DataFrame(trades) if trades else pd.DataFrame()
            
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            return pd.DataFrame()

    def get_live_account_info(self) -> Dict:
        """Récupère les infos compte Binance en temps réel"""
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
            
            return {
                'balances': balances,
                'canTrade': account.get('canTrade', False),
                'canWithdraw': account.get('canWithdraw', False),
                'accountType': account.get('accountType', 'UNKNOWN')
            }
            
        except Exception as e:
            st.error(f"❌ Erreur récupération compte: {e}")
            return {'balances': [], 'canTrade': False}


def main():
    """Interface principale Streamlit"""
    st.set_page_config(
        page_title="🔍 Trading Monitor - Temps Réel",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Trading Monitor - Temps Réel")
    st.markdown("**Surveillance directe Binance + Firebase en temps réel**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Période de surveillance
        hours_back = st.selectbox(
            "Période d'analyse",
            options=[1, 4, 12, 24, 48],
            index=2,  # 12h par défaut
            format_func=lambda x: f"{x}h"
        )
        
        # Paires à surveiller
        default_pairs = ['BNBUSDC', 'ETHUSDC', 'BTCUSDC', 'SOLUSDC']
        monitored_pairs = st.multiselect(
            "Paires à surveiller",
            options=default_pairs + ['ADAUSDC', 'XRPUSDC', 'DOGEUSDC'],
            default=default_pairs
        )
        
        # Auto-refresh
        refresh_rate = st.slider("Auto-refresh (secondes)", 10, 120, 30)
        auto_refresh = st.checkbox("🔄 Auto-refresh activé", value=False)
        
        # Bouton refresh manuel
        if st.button("🔄 Actualiser maintenant", type="primary"):
            st.cache_data.clear()
    
    # Initialisation du monitor
    if 'monitor' not in st.session_state:
        with st.spinner("🔄 Connexion Binance + Firebase..."):
            try:
                st.session_state.monitor = RealTimeTradingMonitor()
            except Exception as e:
                st.error(f"❌ Erreur d'initialisation: {e}")
                return
    
    monitor = st.session_state.monitor
    
    # Récupération des données en temps réel
    with st.spinner("📊 Récupération des données..."):
        # Données Binance
        binance_df = monitor.get_recent_binance_trades(monitored_pairs, hours_back)
        
        # Données Firebase
        firebase_df = monitor.get_recent_firebase_trades(hours_back)
        
        # Infos compte
        account_info = monitor.get_live_account_info()
    
    # Interface principale
    display_real_time_dashboard(binance_df, firebase_df, account_info, hours_back)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()


def display_real_time_dashboard(binance_df: pd.DataFrame, firebase_df: pd.DataFrame, 
                               account_info: Dict, hours_back: int):
    """Affichage du dashboard temps réel"""
    
    # Métriques principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🎯 Trades Binance", len(binance_df))
        
    with col2:
        st.metric("🔥 Trades Firebase", len(firebase_df))
        
    with col3:
        if not binance_df.empty:
            buy_count = len(binance_df[binance_df['side'] == 'BUY'])
            st.metric("📈 Achats", buy_count)
        else:
            st.metric("📈 Achats", 0)
            
    with col4:
        if not binance_df.empty:
            sell_count = len(binance_df[binance_df['side'] == 'SELL'])
            st.metric("📉 Ventes", sell_count)
        else:
            st.metric("📉 Ventes", 0)
            
    with col5:
        if account_info['balances']:
            usdc_balance = next((b['total'] for b in account_info['balances'] if b['asset'] == 'USDC'), 0)
            st.metric("💰 USDC", f"{usdc_balance:.2f}")
        else:
            st.metric("💰 USDC", "N/A")
    
    # Status de trading
    if account_info.get('canTrade'):
        st.success("✅ Compte autorisé au trading")
    else:
        st.error("🚨 Trading désactivé sur le compte")
    
    # Graphiques temps réel
    if not binance_df.empty:
        display_trading_charts(binance_df)
    
    # Comparaison Binance vs Firebase
    display_data_comparison(binance_df, firebase_df)
    
    # Détails des trades
    display_trade_tables(binance_df, firebase_df)


def display_trading_charts(binance_df: pd.DataFrame):
    """Affichage des graphiques de trading"""
    st.subheader("📊 Activité de Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume par paire
        if not binance_df.empty:
            volume_by_pair = binance_df.groupby('symbol')['quoteQty'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=volume_by_pair.index,
                y=volume_by_pair.values,
                title="Volume de trading par paire (USDC)",
                labels={'x': 'Paire', 'y': 'Volume USDC'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Evolution temporelle
        if not binance_df.empty:
            # Agrégation par heure
            binance_df['hour'] = binance_df['time'].dt.floor('h')
            hourly_volume = binance_df.groupby(['hour', 'side'])['quoteQty'].sum().reset_index()
            
            fig = px.line(
                hourly_volume, 
                x='hour', 
                y='quoteQty', 
                color='side',
                title="Volume horaire BUY vs SELL",
                labels={'hour': 'Heure', 'quoteQty': 'Volume USDC'}
            )
            st.plotly_chart(fig, use_container_width=True)


def display_data_comparison(binance_df: pd.DataFrame, firebase_df: pd.DataFrame):
    """Comparaison des données"""
    st.subheader("🔍 Comparaison Binance vs Firebase")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Ratio Firebase/Binance", 
                 f"{len(firebase_df)/max(len(binance_df), 1)*100:.1f}%" if len(binance_df) > 0 else "N/A")
    
    with col2:
        # Dernière activité Binance
        if not binance_df.empty:
            last_binance = binance_df['time'].max()
            st.metric("Dernière activité Binance", last_binance.strftime("%H:%M:%S"))
        else:
            st.metric("Dernière activité Binance", "Aucune")
    
    with col3:
        # Dernière activité Firebase
        if not firebase_df.empty:
            last_firebase = firebase_df['timestamp'].max()
            st.metric("Dernière activité Firebase", last_firebase.strftime("%H:%M:%S"))
        else:
            st.metric("Dernière activité Firebase", "Aucune")
    
    # Alertes
    if len(binance_df) > 0 and len(firebase_df) == 0:
        st.error("🚨 Activité Binance détectée mais aucun log Firebase!")
    elif len(firebase_df) > len(binance_df):
        st.warning("⚠️ Plus de logs Firebase que de trades Binance")
    elif len(binance_df) > 0 and len(firebase_df) > 0:
        st.success("✅ Activité détectée sur les deux sources")


def display_trade_tables(binance_df: pd.DataFrame, firebase_df: pd.DataFrame):
    """Affichage des tables de trades"""
    
    tab1, tab2 = st.tabs(["🎯 Trades Binance", "🔥 Logs Firebase"])
    
    with tab1:
        if not binance_df.empty:
            st.success(f"✅ {len(binance_df)} trades Binance récents")
            
            # Formatage pour l'affichage
            display_binance = binance_df.copy()
            display_binance['time'] = display_binance['time'].dt.strftime('%H:%M:%S')
            display_binance['price'] = display_binance['price'].round(2)
            display_binance['qty'] = display_binance['qty'].round(4)
            display_binance['quoteQty'] = display_binance['quoteQty'].round(2)
            
            st.dataframe(
                display_binance[['time', 'symbol', 'side', 'price', 'qty', 'quoteQty']],
                use_container_width=True
            )
        else:
            st.info("ℹ️ Aucun trade Binance dans la période")
    
    with tab2:
        if not firebase_df.empty:
            st.success(f"✅ {len(firebase_df)} logs Firebase récents")
            
            # Formatage pour l'affichage
            display_firebase = firebase_df.copy()
            display_firebase['timestamp'] = display_firebase['timestamp'].dt.strftime('%H:%M:%S')
            display_firebase['entry_price'] = display_firebase['entry_price'].round(2)
            display_firebase['exit_price'] = display_firebase['exit_price'].round(2)
            display_firebase['pnl_amount'] = display_firebase['pnl_amount'].round(2)
            
            st.dataframe(
                display_firebase[['timestamp', 'pair', 'action', 'entry_price', 'exit_price', 'pnl_amount']],
                use_container_width=True
            )
        else:
            st.info("ℹ️ Aucun log Firebase dans la période")


if __name__ == "__main__":
    main()

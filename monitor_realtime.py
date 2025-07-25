"""
Monitoring en temps réel des trades - Interface Streamlit (Version Proxy VPS)
Surveillance via données Firebase collectées par le VPS (proxy Binance)
Plus de connexion directe Binance - Lecture des données proxy
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import Firebase direct (plus besoin de Binance Client)
import firebase_admin
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from firebase_admin import credentials, firestore


class RealTimeTradingMonitor:
    """Monitoring en temps réel - Lecture des données proxy Firebase (VPS)"""
    
    def __init__(self):
        self.setup_firebase()
        
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

    def get_proxy_binance_trades(self, symbols: List[str], hours_back: int = 24) -> pd.DataFrame:
        """Récupère les trades Binance via le proxy VPS Firebase"""
        try:
            # Lire les données du proxy VPS
            doc = self.firebase_db.collection("binance_live").document("recent_trades").get()
            
            if not doc.exists:
                st.warning("⚠️ Aucune donnée proxy Binance trouvée")
                return pd.DataFrame()
            
            data = doc.to_dict()
            proxy_timestamp = pd.to_datetime(data.get('timestamp'))
            
            # Vérifier la fraîcheur des données (alerte si > 5 minutes)
            now = pd.Timestamp.now()
            data_age_minutes = (now - proxy_timestamp).total_seconds() / 60
            
            if data_age_minutes > 5:
                st.error(f"🚨 Données VPS obsolètes - Dernière MAJ : {proxy_timestamp.strftime('%H:%M:%S')} ({data_age_minutes:.1f}min)")
            else:
                st.success(f"✅ Données VPS fraîches - MAJ : {proxy_timestamp.strftime('%H:%M:%S')}")
            
            # Filtrer les trades par paires demandées et période
            trades = data.get('trades', [])
            filtered_trades = []
            
            cutoff_time = now - timedelta(hours=hours_back)
            
            # Stats pour affichage
            total_trades_vps = len(trades)
            pairs_detected_vps = data.get('pairs_detected', data.get('pairs_monitored', []))
            
            for trade in trades:
                trade_time = pd.to_datetime(trade.get('time'))
                if (trade.get('symbol') in symbols and 
                    trade_time >= cutoff_time):
                    filtered_trades.append({
                        'symbol': trade.get('symbol'),
                        'time': trade_time,
                        'side': trade.get('side'),
                        'price': float(trade.get('price', 0)),
                        'qty': float(trade.get('qty', 0)),
                        'quoteQty': float(trade.get('quoteQty', 0)),
                        'orderId': trade.get('orderId'),
                        'commission': float(trade.get('commission', 0))
                    })
            
            # Afficher les stats VPS
            if pairs_detected_vps:
                with st.expander(f"📊 Stats VPS - {len(pairs_detected_vps)} paires USDC détectées"):
                    st.write(f"**Total trades VPS (toutes paires):** {total_trades_vps}")
                    st.write(f"**Paires actives:** {', '.join(pairs_detected_vps[:10])}")
                    if len(pairs_detected_vps) > 10:
                        st.write(f"**+{len(pairs_detected_vps) - 10} autres paires...**")
            
            return pd.DataFrame(filtered_trades) if filtered_trades else pd.DataFrame()
            
        except Exception as e:
            st.error(f"❌ Erreur lecture proxy trades: {e}")
            return pd.DataFrame()

    def aggregate_binance_trades(self, binance_df: pd.DataFrame) -> pd.DataFrame:
        """Agrège les trades Binance fragmentés pour comparaison avec Firebase
        
        Binance retourne des trades fragmentés (plusieurs exécutions par ordre)
        Firebase stocke des trades agrégés (un enregistrement par ordre complet)
        Cette fonction agrège les trades Binance par orderId pour une comparaison équitable
        """
        if binance_df.empty:
            return pd.DataFrame()
        
        try:
            # Grouper par orderId et agréger
            aggregated = binance_df.groupby(['orderId', 'symbol', 'side']).agg({
                'time': 'first',  # Prendre la première exécution pour le timestamp
                'price': 'mean',  # Prix moyen pondéré pourrait être plus précis, mais moyenne simple pour simplifier
                'qty': 'sum',     # Quantité totale
                'quoteQty': 'sum', # Valeur totale
                'commission': 'sum' # Commission totale
            }).reset_index()
            
            # Recalculer le prix moyen pondéré correct
            aggregated['avg_price'] = aggregated['quoteQty'] / aggregated['qty']
            
            # Ajouter métadonnées pour traçabilité
            aggregated['trade_type'] = 'AGGREGATED_BINANCE'
            aggregated['fragments_count'] = binance_df.groupby('orderId').size().values
            
            return aggregated
            
        except Exception as e:
            st.error(f"❌ Erreur agrégation trades Binance: {e}")
            return binance_df  # Retourner les données non agrégées en cas d'erreur

    def get_recent_firebase_trades(self, hours_back: int = 24) -> pd.DataFrame:
        """Récupère les trades Firebase récents"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            docs = self.firebase_db.collection("trades").where(
                "timestamp", ">=", start_time.isoformat()
            ).where(
                "timestamp", "<=", end_time.isoformat()
            ).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
            
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

    def get_proxy_account_info(self) -> Dict:
        """Récupère les infos compte via le proxy VPS Firebase"""
        try:
            # Lire les données du proxy VPS
            doc = self.firebase_db.collection("binance_live").document("account_info").get()
            
            if not doc.exists:
                st.warning("⚠️ Aucune donnée proxy account trouvée")
                return {'balances': [], 'canTrade': False}
            
            data = doc.to_dict()
            proxy_timestamp = pd.to_datetime(data.get('timestamp'))
            
            # Vérifier la fraîcheur des données
            now = pd.Timestamp.now()
            data_age_minutes = (now - proxy_timestamp).total_seconds() / 60
            
            if data_age_minutes > 5:
                st.warning(f"⚠️ Données compte VPS obsolètes ({data_age_minutes:.1f}min)")
            
            return {
                'balances': data.get('balances', []),
                'canTrade': data.get('canTrade', False),
                'canWithdraw': data.get('canWithdraw', False),
                'accountType': data.get('accountType', 'UNKNOWN'),
                'last_update': proxy_timestamp
            }
            
        except Exception as e:
            st.error(f"❌ Erreur lecture proxy account: {e}")
            return {'balances': [], 'canTrade': False}


def main():
    """Interface principale Streamlit"""
    st.set_page_config(
        page_title="🔍 Trading Monitor - Temps Réel",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Trading Monitor - Temps Réel (VPS Proxy)")
    st.markdown("**Surveillance via proxy VPS Firebase (résout problème IP Binance)**")
    
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
        if 'detected_pairs' not in st.session_state:
            st.session_state.detected_pairs = ['BNBUSDC', 'ETHUSDC', 'BTCUSDC', 'SOLUSDC']
        
        # Récupérer les paires détectées par le VPS
        if 'monitor' in st.session_state:
            try:
                doc = st.session_state.monitor.firebase_db.collection("binance_live").document("recent_trades").get()
                if doc.exists:
                    data = doc.to_dict()
                    vps_pairs = data.get('pairs_detected', data.get('pairs_monitored', []))
                    if vps_pairs:
                        st.session_state.detected_pairs = sorted(vps_pairs)
            except:
                pass  # Ignorer les erreurs silencieusement
        
        # Interface de sélection
        all_available_pairs = st.session_state.detected_pairs + ['ADAUSDC', 'XRPUSDC', 'DOGEUSDC', 'AVAXUSDC', 'DOTUSDC']
        all_available_pairs = sorted(list(set(all_available_pairs)))  # Supprimer les doublons
        
        monitored_pairs = st.multiselect(
            f"Paires à surveiller ({len(st.session_state.detected_pairs)} détectées par VPS)",
            options=all_available_pairs,
            default=st.session_state.detected_pairs[:10],  # Limiter à 10 par défaut pour l'affichage
            help=f"Paires USDC détectées automatiquement par le VPS: {', '.join(st.session_state.detected_pairs[:5])}{'...' if len(st.session_state.detected_pairs) > 5 else ''}"
        )
        
        # Auto-refresh
        refresh_rate = st.slider("Auto-refresh (secondes)", 10, 120, 30)
        auto_refresh = st.checkbox("🔄 Auto-refresh activé", value=False)
        
        # Bouton refresh manuel
        if st.button("🔄 Actualiser maintenant", type="primary"):
            st.cache_data.clear()
    
    # Initialisation du monitor
    if 'monitor' not in st.session_state:
        with st.spinner("🔄 Connexion Firebase (proxy VPS)..."):
            try:
                st.session_state.monitor = RealTimeTradingMonitor()
            except Exception as e:
                st.error(f"❌ Erreur d'initialisation: {e}")
                return
    
    monitor = st.session_state.monitor
    
    # Récupération des données via proxy VPS
    with st.spinner("📊 Récupération données proxy VPS..."):
        # Données Binance via proxy
        binance_df = monitor.get_proxy_binance_trades(monitored_pairs, hours_back)
        
        # IMPORTANT: Agrégation des trades Binance pour comparaison équitable
        binance_aggregated_df = monitor.aggregate_binance_trades(binance_df)
        
        # Données Firebase (trades bot)
        firebase_df = monitor.get_recent_firebase_trades(hours_back)
        
        # Infos compte via proxy
        account_info = monitor.get_proxy_account_info()
    
    # Interface principale
    display_real_time_dashboard(binance_df, binance_aggregated_df, firebase_df, account_info, hours_back)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()


def display_real_time_dashboard(binance_df: pd.DataFrame, binance_aggregated_df: pd.DataFrame, 
                               firebase_df: pd.DataFrame, account_info: Dict, hours_back: int):
    """Affichage du dashboard temps réel avec comparaison trades fragmentés vs agrégés"""
    
    # Métriques principales avec distinction fragmenté/agrégé
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🎯 Trades Binance Bruts", len(binance_df))
        
    with col2:
        st.metric("🎯 Ordres Binance Agrégés", len(binance_aggregated_df))
        
    with col3:
        st.metric("🔥 Trades Firebase (Bot)", len(firebase_df))
            
    with col4:
        if not binance_df.empty:
            buy_count = len(binance_df[binance_df['side'] == 'BUY'])
            sell_count = len(binance_df[binance_df['side'] == 'SELL'])
            st.metric("� Ratio Buy/Sell", f"{buy_count}/{sell_count}")
        else:
            st.metric("� Ratio Buy/Sell", "0/0")
            
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
        display_trading_charts(binance_df, binance_aggregated_df)
    
    # Comparaison Binance (agrégé) vs Firebase avec métrique de fragmentation
    display_data_comparison(binance_aggregated_df, firebase_df, len(binance_df))
    
    # Détails des trades avec onglets fragmentés/agrégés
    display_trade_tables(binance_df, binance_aggregated_df, firebase_df)


def display_trading_charts(binance_df: pd.DataFrame, binance_aggregated_df: pd.DataFrame):
    """Affichage des graphiques de trading avec comparaison fragmenté/agrégé"""
    st.subheader("📊 Activité de Trading - Analyse Fragmentation")
    
    if binance_df.empty and binance_aggregated_df.empty:
        st.info("ℹ️ Aucune donnée de trading à afficher")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume par paire (données agrégées pour précision)
        if not binance_aggregated_df.empty:
            volume_by_pair = binance_aggregated_df.groupby('symbol')['quoteQty'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=volume_by_pair.index,
                y=volume_by_pair.values,
                title="Volume de trading par paire (USDC) - Données Agrégées",
                labels={'x': 'Paire', 'y': 'Volume USDC'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Comparaison fragmentation
        if not binance_df.empty and not binance_aggregated_df.empty:
            fragmentation_data = binance_aggregated_df[['symbol', 'fragments_count']].groupby('symbol')['fragments_count'].mean()
            
            fig = px.bar(
                x=fragmentation_data.index,
                y=fragmentation_data.values,
                title="Fragmentation moyenne par paire",
                labels={'x': 'Paire', 'y': 'Fragments par ordre'}
            )
            st.plotly_chart(fig, use_container_width=True)
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


def display_data_comparison(binance_aggregated_df: pd.DataFrame, firebase_df: pd.DataFrame, total_fragments: int):
    """Comparaison des données proxy VPS vs Firebase bot avec métriques de fragmentation"""
    st.subheader("🔍 Comparaison Binance (Agrégé) vs Firebase (Bot)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ratio Bot/Binance (Agrégé)", 
                 f"{len(firebase_df)/max(len(binance_aggregated_df), 1)*100:.1f}%" if len(binance_aggregated_df) > 0 else "N/A")
    
    with col2:
        fragmentation_ratio = total_fragments / max(len(binance_aggregated_df), 1)
        st.metric("Taux Fragmentation", f"{fragmentation_ratio:.1f}x")
    
    with col3:
        # Dernière activité Binance (via VPS)
        if not binance_aggregated_df.empty:
            last_binance = binance_aggregated_df['time'].max()
            st.metric("Dernière activité Binance", last_binance.strftime("%H:%M:%S"))
        else:
            st.metric("Dernière activité Binance", "Aucune")
    
    with col4:
        # Dernière activité Firebase (bot)
        if not firebase_df.empty:
            last_firebase = firebase_df['timestamp'].max()
            st.metric("Dernière activité Bot", last_firebase.strftime("%H:%M:%S"))
        else:
            st.metric("Dernière activité Bot", "Aucune")
    
    # Alertes adaptées à l'agrégation
    if len(binance_aggregated_df) > 0 and len(firebase_df) == 0:
        st.error("🚨 Ordres Binance détectés mais aucun log Bot!")
    elif len(firebase_df) > len(binance_aggregated_df):
        st.warning("⚠️ Plus de logs Bot que d'ordres Binance (normal si bot très actif)")
    elif len(binance_aggregated_df) > 0 and len(firebase_df) > 0:
        ratio = len(firebase_df) / len(binance_aggregated_df)
        if ratio > 0.8:  # Seuil de correspondance
            st.success(f"✅ Bonne correspondance Bot/Binance (ratio: {ratio:.2f})")
        else:
            st.warning(f"⚠️ Correspondance partielle Bot/Binance (ratio: {ratio:.2f})")
    
    # Information pédagogique
    with st.expander("ℹ️ À propos de l'agrégation"):
        st.markdown("""
        **Pourquoi agréger les trades Binance ?**
        
        - **Binance** : Retourne des trades fragmentés (plusieurs exécutions par ordre)
        - **Firebase** : Stocke des trades agrégés (un enregistrement par ordre complet)
        - **Comparaison** : Nécessite d'agréger les fragments Binance par `orderId`
        
        **Métriques :**
        - `Taux Fragmentation` : Nombre de fragments par ordre moyen
        - `Ratio Bot/Binance` : Correspondance entre logs bot et ordres réels
        """)


def display_trade_tables(binance_df: pd.DataFrame, binance_aggregated_df: pd.DataFrame, firebase_df: pd.DataFrame):
    """Affichage des tables de trades avec distinction fragmenté/agrégé"""
    
    tab1, tab2, tab3 = st.tabs(["🎯 Trades Binance (Bruts)", "🎯 Ordres Binance (Agrégés)", "🔥 Logs Bot Firebase"])
    
    with tab1:
        if not binance_df.empty:
            st.success(f"✅ {len(binance_df)} trades Binance fragmentés (via VPS)")
            
            # Formatage pour l'affichage
            display_binance = binance_df.copy()
            display_binance['time'] = display_binance['time'].dt.strftime('%H:%M:%S')
            display_binance['price'] = display_binance['price'].round(2)
            display_binance['qty'] = display_binance['qty'].round(4)
            display_binance['quoteQty'] = display_binance['quoteQty'].round(2)
            
            st.dataframe(
                display_binance[['time', 'symbol', 'side', 'price', 'qty', 'quoteQty', 'orderId']],
                use_container_width=True
            )
        else:
            st.info("ℹ️ Aucun trade Binance fragmenté dans la période")
    
    with tab2:
        if not binance_aggregated_df.empty:
            st.success(f"✅ {len(binance_aggregated_df)} ordres Binance agrégés")
            
            # Formatage pour l'affichage
            display_aggregated = binance_aggregated_df.copy()
            display_aggregated['time'] = display_aggregated['time'].dt.strftime('%H:%M:%S')
            display_aggregated['avg_price'] = display_aggregated['avg_price'].round(2)
            display_aggregated['qty'] = display_aggregated['qty'].round(4)
            display_aggregated['quoteQty'] = display_aggregated['quoteQty'].round(2)
            
            st.dataframe(
                display_aggregated[['time', 'symbol', 'side', 'avg_price', 'qty', 'quoteQty', 'fragments_count', 'orderId']],
                use_container_width=True
            )
        else:
            st.info("ℹ️ Aucun ordre Binance agrégé dans la période")
    
    with tab3:
        if not firebase_df.empty:
            st.success(f"✅ {len(firebase_df)} logs bot récents")
            
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
            st.info("ℹ️ Aucun log bot dans la période")


if __name__ == "__main__":
    main()

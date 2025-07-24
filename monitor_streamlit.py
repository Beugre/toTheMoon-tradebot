"""
Monitoring en temps réel des trades - Audit Binance vs Firebase
Interface Streamlit pour surveillance continue de l'intégrité des données
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from binance.client import Client
from dotenv import load_dotenv

# Import de l'auditeur amélioré
from audit_trades_simple import TradeAuditorSimple
from utils.firebase_logger import FirebaseLogger


class TradingMonitor:
    """Monitoring en temps réel des trades avec interface Streamlit"""
    
    def __init__(self):
        load_dotenv()
        self.setup_binance_client()
        self.setup_firebase()
        self.auditor = TradeAuditorSimple(self.binance_client, self.firebase_logger.firestore_db)
        
    def setup_binance_client(self):
        """Configuration du client Binance"""
        try:
            self.binance_client = Client(
                api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_SECRET_KEY')
            )
        except Exception as e:
            st.error(f"❌ Erreur Binance: {e}")
            raise
            
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            self.firebase_logger = FirebaseLogger()
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            raise


def main():
    """Interface principale Streamlit"""
    st.set_page_config(
        page_title="🔍 Trading Monitor - Audit Temps Réel",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Trading Monitor - Audit Temps Réel")
    st.markdown("**Surveillance continue de l'intégrité des trades Binance vs Firebase**")
    
    # Sidebar pour les contrôles
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Sélection de la période
        monitoring_mode = st.selectbox(
            "Mode de monitoring",
            ["Temps réel (1h)", "Dernières 24h", "Dernières 4h", "Personnalisé"]
        )
        
        if monitoring_mode == "Personnalisé":
            hours_back = st.slider("Heures en arrière", 1, 168, 24)
        elif monitoring_mode == "Temps réel (1h)":
            hours_back = 1
        elif monitoring_mode == "Dernières 4h":
            hours_back = 4
        else:  # Dernières 24h
            hours_back = 24
            
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        
        # Paires à surveiller
        default_pairs = ['BNBUSDC', 'ETHUSDC', 'BTCUSDC', 'SOLUSDC']
        monitored_pairs = st.multiselect(
            "Paires à surveiller",
            options=default_pairs + ['ADAUSDC', 'XRPUSDC', 'DOGEUSDC'],
            default=default_pairs
        )
        
        # Seuils d'alerte
        st.subheader("🚨 Seuils d'alerte")
        price_tolerance = st.slider("Tolérance prix (%)", 0.1, 5.0, 2.0, 0.1)
        time_tolerance = st.slider("Tolérance temps (min)", 5, 240, 60, 5)
        
        # Bouton de rafraîchissement manuel
        if st.button("🔄 Actualiser", type="primary"):
            st.cache_data.clear()
    
    # Initialisation du monitor
    if 'monitor' not in st.session_state:
        with st.spinner("🔄 Initialisation du monitoring..."):
            try:
                st.session_state.monitor = TradingMonitor()
                st.success("✅ Monitor initialisé")
            except Exception as e:
                st.error(f"❌ Erreur d'initialisation: {e}")
                return
    
    monitor = st.session_state.monitor
    
    # Période d'analyse
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours_back)
    
    # Affichage de la période
    st.info(f"📅 Période analysée: {start_date.strftime('%Y-%m-%d %H:%M')} → {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Récupération des données
    with st.spinner(f"🔄 Récupération des données ({monitoring_mode})..."):
        try:
            # Données Binance
            binance_df = monitor.auditor.get_binance_trades(monitored_pairs, start_date, end_date)
            
            # Données Firebase
            firebase_df = monitor.auditor.get_firebase_trades(start_date, end_date)
            
            # Comparaison intelligente
            matched_df, unmatched_binance, unmatched_firebase = monitor.auditor.compare_trades(binance_df, firebase_df)
            
            # Analyse des cycles
            cycle_analysis = monitor.auditor.analyze_trading_cycles(binance_df, firebase_df)
            
            # Métriques
            metrics = monitor.auditor.calculate_metrics(matched_df, unmatched_binance, unmatched_firebase)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des données: {e}")
            return
    
    # Interface principale
    display_monitoring_dashboard(
        binance_df, firebase_df, matched_df, unmatched_binance, unmatched_firebase,
        cycle_analysis, metrics, monitoring_mode, price_tolerance, time_tolerance
    )
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()


def display_monitoring_dashboard(binance_df, firebase_df, matched_df, unmatched_binance, 
                               unmatched_firebase, cycle_analysis, metrics, monitoring_mode,
                               price_tolerance, time_tolerance):
    """Affichage du dashboard principal"""
    
    # Métriques en temps réel
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🎯 Trades Binance", metrics['total_binance_trades'])
        if not binance_df.empty and 'fragment_count' in binance_df.columns:
            fragments = binance_df['fragment_count'].sum()
            st.caption(f"🧩 {fragments} fragments")
            
    with col2:
        st.metric("🔥 Trades Firebase", metrics['total_firebase_trades'])
        
    with col3:
        match_rate = metrics['match_rate']
        st.metric("✅ Taux de match", f"{match_rate:.1f}%")
        
    with col4:
        st.metric("❌ Manqués", metrics['missing_in_firebase'])
        
    with col5:
        st.metric("👻 Fantômes", metrics['phantom_in_firebase'])
    
    # Status global
    st.subheader("🎯 Status Global")
    
    if metrics['match_rate'] >= 90:
        st.success(f"✅ Système fonctionnel - Taux de match: {metrics['match_rate']:.1f}%")
    elif metrics['match_rate'] >= 50:
        st.warning(f"⚠️ Attention - Taux de match: {metrics['match_rate']:.1f}%")
    else:
        st.error(f"🚨 Problème détecté - Taux de match: {metrics['match_rate']:.1f}%")
    
    # Alertes spécifiques
    if cycle_analysis['orphaned_closes'] > 0:
        st.error(f"🚨 {cycle_analysis['orphaned_closes']} SELL orphelins détectés!")
        
    if cycle_analysis['orphaned_opens'] > 0:
        st.warning(f"⚠️ {cycle_analysis['orphaned_opens']} BUY orphelins détectés!")
    
    # Graphiques
    if not matched_df.empty:
        display_matching_charts(matched_df)
    
    # Cycles de trading
    display_trading_cycles(cycle_analysis, binance_df, firebase_df)
    
    # Détails des trades
    display_trade_details(binance_df, firebase_df, matched_df, unmatched_binance, unmatched_firebase)
    
    # Cycles incomplets
    if cycle_analysis['incomplete_cycles']:
        display_incomplete_cycles(cycle_analysis['incomplete_cycles'])


def display_matching_charts(matched_df):
    """Affichage des graphiques de matching"""
    st.subheader("📊 Analyse des Matches")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de confiance de matching
        if 'match_confidence' in matched_df.columns:
            fig = px.histogram(
                matched_df, x='match_confidence',
                title="Distribution de la confiance de matching",
                nbins=10,
                labels={'match_confidence': 'Confiance (%)', 'count': 'Nombre de trades'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Différences de prix
        if 'price_diff_percent' in matched_df.columns:
            fig = px.histogram(
                matched_df, x='price_diff_percent',
                title="Distribution des différences de prix (%)",
                nbins=10,
                labels={'price_diff_percent': 'Différence prix (%)', 'count': 'Nombre de trades'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


def display_trading_cycles(cycle_analysis, binance_df, firebase_df):
    """Affichage des cycles de trading"""
    st.subheader("🔄 Cycles de Trading")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 BUY Binance", cycle_analysis['binance_buy_orders'])
        
    with col2:
        st.metric("📉 SELL Binance", cycle_analysis['binance_sell_orders'])
        
    with col3:
        st.metric("🟢 BUY Firebase", cycle_analysis['firebase_open_trades'])
        
    with col4:
        st.metric("🔴 SELL Firebase", cycle_analysis['firebase_close_trades'])
    
    # Fragmentation
    if not binance_df.empty and 'fragment_count' in binance_df.columns:
        total_fragments = binance_df['fragment_count'].sum()
        fragmented_trades = len(binance_df[binance_df['fragment_count'] > 1])
        st.info(f"🧩 Fragmentation: {total_fragments} fragments → {len(binance_df)} trades ({fragmented_trades} fragmentés)")


def display_trade_details(binance_df, firebase_df, matched_df, unmatched_binance, unmatched_firebase):
    """Affichage des détails des trades"""
    
    st.subheader("📋 Détails des Trades")
    
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Trades Matchés", "🎯 Binance", "🔥 Firebase", "❌ Non Matchés"])
    
    with tab1:
        if not matched_df.empty:
            st.success(f"✅ {len(matched_df)} trades matchés avec succès")
            
            # Résumé des matches
            if 'match_confidence' in matched_df.columns:
                avg_confidence = matched_df['match_confidence'].mean()
                st.info(f"📊 Confiance moyenne: {avg_confidence:.1f}%")
            
            # Affichage du DataFrame
            display_cols = [
                'symbol_binance', 'time_binance', 'price_binance', 'trade_type_binance',
                'pair_firebase', 'timestamp_firebase', 'action_firebase'
            ]
            
            if 'match_confidence' in matched_df.columns:
                display_cols.extend(['match_confidence', 'price_diff_percent', 'time_diff_minutes'])
            
            available_cols = [col for col in display_cols if col in matched_df.columns]
            
            if available_cols:
                st.dataframe(matched_df[available_cols], use_container_width=True)
            else:
                st.dataframe(matched_df, use_container_width=True)
        else:
            st.warning("⚠️ Aucun trade matché")
    
    with tab2:
        if not binance_df.empty:
            st.success(f"🎯 {len(binance_df)} trades Binance")
            st.dataframe(binance_df, use_container_width=True)
        else:
            st.info("ℹ️ Aucun trade Binance dans la période")
    
    with tab3:
        if not firebase_df.empty:
            st.success(f"🔥 {len(firebase_df)} trades Firebase")
            st.dataframe(firebase_df, use_container_width=True)
        else:
            st.info("ℹ️ Aucun trade Firebase dans la période")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ Manqués dans Firebase")
            if not unmatched_binance.empty:
                st.error(f"🚨 {len(unmatched_binance)} trades non loggés dans Firebase")
                st.dataframe(unmatched_binance, use_container_width=True)
            else:
                st.success("✅ Aucun trade manqué")
        
        with col2:
            st.subheader("👻 Fantômes dans Firebase")
            if not unmatched_firebase.empty:
                st.warning(f"⚠️ {len(unmatched_firebase)} trades fantômes dans Firebase")
                st.dataframe(unmatched_firebase, use_container_width=True)
            else:
                st.success("✅ Aucun trade fantôme")


def display_incomplete_cycles(incomplete_cycles):
    """Affichage des cycles incomplets"""
    st.subheader("🚨 Cycles de Trading Incomplets")
    
    for cycle in incomplete_cycles:
        if cycle['type'] == 'ORPHANED_CLOSE':
            with st.expander(f"🔴 SELL Orphelin - {cycle['pair']} - {cycle['close_time'].strftime('%Y-%m-%d %H:%M')}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Paire**: {cycle['pair']}")
                    st.write(f"**Timestamp**: {cycle['close_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.write(f"**Prix entrée**: {cycle.get('entry_price', 'N/A')}")
                    st.write(f"**Prix sortie**: {cycle.get('exit_price', 'N/A')}")
                
                with col3:
                    st.write(f"**Trade ID**: {cycle.get('trade_id', 'N/A')}")
                    st.write(f"**Problème**: {cycle['issue']}")
                
                st.error("⚠️ Trade SELL enregistré sans BUY correspondant dans Firebase")
                
        elif cycle['type'] == 'ORPHANED_OPEN':
            with st.expander(f"🟡 BUY Orphelin - {cycle['pair']} - {cycle['open_time'].strftime('%Y-%m-%d %H:%M')}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Paire**: {cycle['pair']}")
                    st.write(f"**Timestamp**: {cycle['open_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.write(f"**Prix entrée**: {cycle.get('entry_price', 'N/A')}")
                    st.write(f"**Trade ID**: {cycle.get('trade_id', 'N/A')}")
                
                st.warning("⚠️ Trade BUY enregistré sans SELL correspondant dans Firebase")


if __name__ == "__main__":
    main()

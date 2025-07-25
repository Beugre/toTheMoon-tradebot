"""
Monitoring en temps réel des trades - Audit Binance vs Firebase
Interface Streamlit pour surveillance continue de l'intégrité des données
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from binance.client import Client
from dotenv import load_dotenv
import os

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
            st.success("✅ Binance connecté")
        except Exception as e:
            st.error(f"❌ Erreur Binance: {e}")
            
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            self.firebase_logger = FirebaseLogger()
            st.success("✅ Firebase connecté")
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")


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
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
        
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
        
    # Initialisation du monitor
    if 'monitor' not in st.session_state:
        with st.spinner("🔄 Initialisation du monitoring..."):
            try:
                st.session_state.monitor = TradingMonitor()
            except Exception as e:
                st.error(f"❌ Erreur d'initialisation: {e}")
                return
    
    monitor = st.session_state.monitor
    
    # Période d'analyse
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours_back)
    
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
    
    # Alertes si problèmes détectés
    if metrics['match_rate'] < 90:
        st.warning(f"⚠️ Taux de match faible: {metrics['match_rate']:.1f}%")
        
    if cycle_analysis['orphaned_closes'] > 0:
        st.error(f"🚨 {cycle_analysis['orphaned_closes']} SELL orphelins détectés!")
        
    if cycle_analysis['orphaned_opens'] > 0:
        st.warning(f"⚠️ {cycle_analysis['orphaned_opens']} BUY orphelins détectés!")
    
    # Graphiques
    if not matched_df.empty:
        display_matching_charts(matched_df)
    
    # Détails des trades
    display_trade_details(binance_df, firebase_df, matched_df, unmatched_binance, unmatched_firebase)
    
    # Cycles incomplets
    if cycle_analysis['incomplete_cycles']:
        display_incomplete_cycles(cycle_analysis['incomplete_cycles'])


def display_matching_charts(matched_df):
    """Affichage des graphiques de matching"""
    st.subheader("📊 Analyse des matches")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de confiance de matching
        if 'match_confidence' in matched_df.columns:
            fig = px.histogram(
                matched_df, x='match_confidence',
                title="Distribution de la confiance de matching",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Différences de prix
        if 'price_diff_percent' in matched_df.columns:
            fig = px.histogram(
                matched_df, x='price_diff_percent',
                title="Distribution des différences de prix (%)",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)


def display_trade_details(binance_df, firebase_df, matched_df, unmatched_binance, unmatched_firebase):
    """Affichage des détails des trades"""
    
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Trades Matchés", "🎯 Binance", "🔥 Firebase", "❌ Non Matchés"])
    
    with tab1:
        if not matched_df.empty:
            st.dataframe(matched_df, use_container_width=True)
        else:
            st.info("Aucun trade matché")
    
    with tab2:
        if not binance_df.empty:
            st.dataframe(binance_df, use_container_width=True)
        else:
            st.info("Aucun trade Binance")
    
    with tab3:
        if not firebase_df.empty:
            st.dataframe(firebase_df, use_container_width=True)
        else:
            st.info("Aucun trade Firebase")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Manqués dans Firebase")
            if not unmatched_binance.empty:
                st.dataframe(unmatched_binance, use_container_width=True)
            else:
                st.success("Aucun trade manqué")
        
        with col2:
            st.subheader("Fantômes dans Firebase")
            if not unmatched_firebase.empty:
                st.dataframe(unmatched_firebase, use_container_width=True)
            else:
                st.success("Aucun trade fantôme")


def display_incomplete_cycles(incomplete_cycles):
    """Affichage des cycles incomplets"""
    st.subheader("🚨 Cycles de Trading Incomplets")
    
    for cycle in incomplete_cycles:
        if cycle['type'] == 'ORPHANED_CLOSE':
            st.error(f"""
            **🔴 SELL Orphelin** - {cycle['pair']}
            - **Timestamp**: {cycle['close_time'].strftime('%Y-%m-%d %H:%M:%S')}
            - **Prix entrée**: {cycle.get('entry_price', 'N/A')}
            - **Prix sortie**: {cycle.get('exit_price', 'N/A')}
            - **Trade ID**: {cycle.get('trade_id', 'N/A')}
            - **Problème**: {cycle['issue']}
            """)
        elif cycle['type'] == 'ORPHANED_OPEN':
            st.warning(f"""
            **🟡 BUY Orphelin** - {cycle['pair']}
            - **Timestamp**: {cycle['open_time'].strftime('%Y-%m-%d %H:%M:%S')}
            - **Prix entrée**: {cycle.get('entry_price', 'N/A')}
            - **Trade ID**: {cycle.get('trade_id', 'N/A')}
            - **Problème**: {cycle['issue']}
            """)


if __name__ == "__main__":
    main()
            return pd.DataFrame()
        
        df = pd.DataFrame(all_trades)
        
        # Conversion et nettoyage
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['price'] = pd.to_numeric(df['price'])
        df['qty'] = pd.to_numeric(df['qty'])
        df['commission'] = pd.to_numeric(df['commission'])
        df['quoteQty'] = pd.to_numeric(df['quoteQty'])
        
        # Clé de matching robuste
        df['match_key'] = df.apply(lambda row: f"{row['symbol']}_{row['orderId']}_{int(row['time'].timestamp())}", axis=1)
        
        return df
    
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
            st.error(f"❌ Erreur récupération Firebase: {e}")
            return pd.DataFrame()
    
    def _create_firebase_match_key(self, row) -> str:
        """Crée une clé de matching pour Firebase"""
        binance_id = row.get('binance_order_id', 'UNKNOWN')
        timestamp = int(pd.to_datetime(row['timestamp']).timestamp())
        return f"{row['pair']}_{binance_id}_{timestamp}"
    
    def compare_trades(self, binance_df: pd.DataFrame, firebase_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Compare les trades entre Binance et Firebase"""
        # Cas où les deux DataFrames sont vides
        if binance_df.empty and firebase_df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Cas où seul Binance est vide
        if binance_df.empty:
            return pd.DataFrame(), pd.DataFrame(), firebase_df.copy()
        
        # Cas où seul Firebase est vide
        if firebase_df.empty:
            return pd.DataFrame(), binance_df.copy(), pd.DataFrame()
        
        # Cas normal - les deux ont des données
        # Vérifier que les clés de matching existent
        if 'match_key' not in binance_df.columns:
            st.error("❌ Colonne 'match_key' manquante dans les données Binance")
            return pd.DataFrame(), binance_df.copy(), firebase_df.copy()
        
        if 'match_key' not in firebase_df.columns:
            st.error("❌ Colonne 'match_key' manquante dans les données Firebase")
            return pd.DataFrame(), binance_df.copy(), firebase_df.copy()
        
        # Merge sur la clé de matching
        merged = pd.merge(
            binance_df, 
            firebase_df, 
            on='match_key', 
            how='outer', 
            indicator=True,
            suffixes=('_binance', '_firebase')
        )
        
        # Séparation des résultats
        matched = merged[merged['_merge'] == 'both'].copy()
        only_binance = merged[merged['_merge'] == 'left_only'].copy()
        only_firebase = merged[merged['_merge'] == 'right_only'].copy()
        
        return matched, only_binance, only_firebase
    
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

def main():
    """Interface Streamlit principale"""
    st.set_page_config(
        page_title="🔍 Audit Trades Binance vs Firebase",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Audit des Trades : Binance vs Firebase")
    st.markdown("**Comparaison et validation de l'intégrité des données de trading**")
    
    # Configuration des dates
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "📅 Date de début",
            value=datetime.now() - timedelta(days=7),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "📅 Date de fin",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # Sélection des paires
    try:
        from config import PRIORITY_USDC_PAIRS
        available_pairs = PRIORITY_USDC_PAIRS
    except ImportError:
        # Fallback si PRIORITY_USDC_PAIRS n'est pas disponible
        available_pairs = ['BNBUSDC', 'ETHUSDC', 'BTCUSDC', 'ADAUSDC', 'SOLUSDC']
    
    selected_pairs = st.multiselect(
        "🎯 Paires à analyser",
        options=available_pairs,
        default=available_pairs[:5]
    )
    
    if st.button("🚀 Lancer l'audit", type="primary"):
        if not selected_pairs:
            st.warning("⚠️ Veuillez sélectionner au moins une paire")
            return
        
        # Initialisation des services
        try:
            from utils.firebase_logger import FirebaseLogger
            firebase_logger = FirebaseLogger()
            
            # Configuration Binance (à adapter selon votre setup)
            import os

            from binance.client import Client
            
            binance_client = Client(
                api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_API_SECRET')
            )
            
            auditor = TradeAuditor(binance_client, firebase_logger.firestore_db)
            
        except Exception as e:
            st.error(f"❌ Erreur d'initialisation: {e}")
            return
        
        # Récupération des données
        with st.spinner("🔄 Récupération des données Binance..."):
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            binance_df = auditor.get_binance_trades(selected_pairs, start_datetime, end_datetime)
        
        with st.spinner("🔄 Récupération des données Firebase..."):
            firebase_df = auditor.get_firebase_trades(start_datetime, end_datetime)
        
        # Comparaison
        matched, only_binance, only_firebase = auditor.compare_trades(binance_df, firebase_df)
        metrics = auditor.calculate_metrics(matched, only_binance, only_firebase)
        
        # Affichage des métriques
        st.header("📊 Résumé de l'audit")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Trades Binance", metrics['total_binance_trades'])
        with col2:
            st.metric("🔥 Trades Firebase", metrics['total_firebase_trades'])
        with col3:
            st.metric("✅ Matchés", metrics['matched_trades'])
        with col4:
            st.metric("📈 Taux de match", f"{metrics['match_rate']:.1f}%")
        
        # Graphique de cohérence
        st.subheader("📈 Visualisation de la cohérence")
        
        fig = go.Figure(data=[
            go.Bar(name='Matchés', x=['Trades'], y=[metrics['matched_trades']], marker_color='green'),
            go.Bar(name='Manqués Firebase', x=['Trades'], y=[metrics['missing_in_firebase']], marker_color='orange'),
            go.Bar(name='Fantômes Firebase', x=['Trades'], y=[metrics['phantom_in_firebase']], marker_color='red')
        ])
        
        fig.update_layout(
            title="Répartition des trades par catégorie",
            barmode='stack',
            yaxis_title="Nombre de trades"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Détails des incohérences
        if len(only_binance) > 0:
            st.subheader("❌ Trades manqués dans Firebase")
            st.warning(f"⚠️ {len(only_binance)} trades exécutés sur Binance mais non enregistrés dans Firebase")
            
            display_cols = ['symbol', 'time', 'price', 'qty', 'quoteQty', 'commission', 'orderId']
            available_cols = [col for col in display_cols if col in only_binance.columns]
            st.dataframe(only_binance[available_cols])
        
        if len(only_firebase) > 0:
            st.subheader("❌ Trades fantômes dans Firebase")
            st.error(f"🚨 {len(only_firebase)} trades enregistrés dans Firebase mais non trouvés sur Binance")
            
            display_cols = ['pair', 'timestamp', 'entry_price', 'size', 'pnl_amount', 'trade_id']
            available_cols = [col for col in display_cols if col in only_firebase.columns]
            st.dataframe(only_firebase[available_cols])
        
        # Trades matchés avec différences
        if len(matched) > 0:
            st.subheader("✅ Trades matchés")
            st.success(f"✅ {len(matched)} trades correctement synchronisés")
            
            # Analyse des différences de prix/quantité
            if 'price' in matched.columns and 'entry_price' in matched.columns:
                matched['price_diff'] = abs(matched['price'] - matched['entry_price'])
                matched['price_diff_pct'] = (matched['price_diff'] / matched['price']) * 100
                
                significant_diffs = matched[matched['price_diff_pct'] > 0.1]  # Plus de 0.1% de différence
                
                if len(significant_diffs) > 0:
                    st.warning(f"⚠️ {len(significant_diffs)} trades avec différences de prix significatives")
                    
                    display_cols = ['symbol', 'time', 'price', 'entry_price', 'price_diff_pct']
                    available_cols = [col for col in display_cols if col in significant_diffs.columns]
                    st.dataframe(significant_diffs[available_cols])
        
        # Recommandations
        st.header("💡 Recommandations")
        
        if metrics['match_rate'] < 95:
            st.error("🚨 Taux de cohérence critique ! Vérifiez le système de logging.")
        elif metrics['match_rate'] < 98:
            st.warning("⚠️ Taux de cohérence à améliorer.")
        else:
            st.success("✅ Excellente cohérence des données !")
        
        if metrics['missing_in_firebase'] > 0:
            st.info(f"💡 Ajoutez l'ID Binance dans vos logs Firebase pour améliorer le matching")
        
        if metrics['phantom_in_firebase'] > 0:
            st.info(f"💡 Vérifiez la logique de validation des trades avant enregistrement")

if __name__ == "__main__":
    main()

"""
Dashboard Streamlit pour ToTheMoon Trading Bot
Interface temps réel connectée à Firebase - VERSION CORRIGÉE AVEC VRAIS P&L
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import firebase_admin
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from firebase_admin import credentials, firestore

# Configuration de la page
st.set_page_config(
    page_title="🚀 ToTheMoon Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_firebase():
    """Initialise la connexion Firebase"""
    try:
        # Vérifier si l'app existe déjà
        firebase_admin.get_app()
    except ValueError:
        # Initialiser Firebase avec les credentials
        try:
            cred = credentials.Certificate('firebase_credentials.json')
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erreur d'initialisation Firebase: {str(e)}")
            return None
    
    return firestore.client()

def get_real_time_data(db, collection_name: str, limit: int = 100) -> List[Dict]:
    """Récupère les données en temps réel depuis Firebase"""
    try:
        if db is None:
            return []
        
        docs = db.collection(collection_name)\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            data.append(doc_data)
        
        return data
    except Exception as e:
        st.error(f"Erreur récupération {collection_name}: {str(e)}")
        return []

def show_overview(db):
    """Page Vue d'ensemble"""
    st.header("🎯 Vue d'Ensemble")
    
    # Récupération des données
    trades = get_real_time_data(db, "trades", 10)
    metrics = get_real_time_data(db, "metrics", 50)
    
    if trades:
        df_trades = pd.DataFrame(trades)
        
        # Calcul des vrais P&L
        df_trades['real_pnl'] = df_trades['capital_after'] - df_trades['capital_before']
        df_pnl = df_trades[df_trades['real_pnl'] != 0]
        
        # Métriques rapides
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            capital_current = df_trades['capital_after'].iloc[0] if len(df_trades) > 0 else 0
            st.metric("💰 Capital", f"{capital_current:,.2f} USDC")
        
        with col2:
            if len(df_pnl) > 0:
                total_pnl = df_pnl['real_pnl'].sum()
                st.metric("📊 P&L Total", f"{total_pnl:+.4f} USDC")
            else:
                st.metric("📊 P&L Total", "0.0000 USDC")
        
        with col3:
            if len(df_pnl) > 0:
                profitable = len(df_pnl[df_pnl['real_pnl'] > 0])
                win_rate = (profitable / len(df_pnl)) * 100
                st.metric("🎯 Taux Réussite", f"{win_rate:.1f}%")
            else:
                st.metric("🎯 Taux Réussite", "N/A")
        
        with col4:
            st.metric("📈 Total Trades", len(df_trades))

def show_performance(db):
    """Page Performance avec analyse réelle des P&L"""
    st.header("📈 Performance Trading - Analyse Réelle")
    
    # Récupération des trades (30 derniers pour analyse approfondie)
    trades = get_real_time_data(db, "trades", 30)
    
    if not trades:
        st.error("❌ Aucun trade trouvé dans Firebase")
        return
    
    # Conversion en DataFrame
    df_trades = pd.DataFrame(trades)
    df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
    df_trades = df_trades.sort_values('timestamp')
    
    # Calcul des vrais P&L (capital_after - capital_before)
    df_trades['real_pnl'] = df_trades['capital_after'] - df_trades['capital_before']
    
    # Filtrer seulement les trades avec P&L réel (non nuls)
    df_pnl = df_trades[df_trades['real_pnl'] != 0].copy()
    
    # === MÉTRIQUES PRINCIPALES ===
    st.subheader("🎯 Résumé Exécutif")
    
    if len(df_pnl) > 0:
        total_pnl = df_pnl['real_pnl'].sum()
        profitable = len(df_pnl[df_pnl['real_pnl'] > 0])
        losing = len(df_pnl[df_pnl['real_pnl'] < 0])
        win_rate = (profitable / len(df_pnl)) * 100 if len(df_pnl) > 0 else 0
        avg_pnl = df_pnl['real_pnl'].mean()
        
        # Capital évolution
        capital_start = df_trades['capital_before'].iloc[0] if len(df_trades) > 0 else 0
        capital_current = df_trades['capital_after'].iloc[-1] if len(df_trades) > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💰 Capital Actuel", f"{capital_current:,.2f} USDC")
        
        with col2:
            color = "normal" if total_pnl >= 0 else "inverse"
            st.metric("📊 P&L Total", f"{total_pnl:+.4f} USDC", delta=f"{avg_pnl:+.4f} avg", delta_color=color)
        
        with col3:
            color = "normal" if win_rate >= 50 else "inverse"
            st.metric("🎯 Taux Réussite", f"{win_rate:.1f}%", delta=f"{profitable}W/{losing}L", delta_color=color)
        
        with col4:
            best_trade = df_pnl['real_pnl'].max()
            st.metric("🚀 Meilleur Trade", f"{best_trade:+.4f} USDC")
        
        with col5:
            worst_trade = df_pnl['real_pnl'].min()
            st.metric("💥 Pire Trade", f"{worst_trade:+.4f} USDC")
        
        # === ALERTES DE PERFORMANCE ===
        if win_rate == 0:
            st.error("🚨 ALERTE CRITIQUE: 0% de taux de réussite - Arrêt recommandé!")
        elif win_rate < 30:
            st.warning("⚠️ ALERTE: Taux de réussite très faible")
        elif total_pnl < -50:
            st.warning("⚠️ ALERTE: Pertes importantes détectées")
        
        # === PERFORMANCE PAR PAIRE ===
        st.subheader("🔄 Performance par Paire")
        
        if 'pair' in df_pnl.columns:
            pair_stats = df_pnl.groupby('pair').agg({
                'real_pnl': ['count', 'sum', 'mean'],
                'duration_seconds': 'mean'
            }).round(4)
            
            pair_data = []
            for pair in pair_stats.index:
                count = int(pair_stats.loc[pair, ('real_pnl', 'count')])
                total_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'sum')]
                avg_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'mean')]
                avg_duration = pair_stats.loc[pair, ('duration_seconds', 'mean')] / 60 if not pd.isna(pair_stats.loc[pair, ('duration_seconds', 'mean')]) else 0
                
                profitable_pair = len(df_pnl[(df_pnl['pair'] == pair) & (df_pnl['real_pnl'] > 0)])
                win_rate_pair = (profitable_pair / count) * 100 if count > 0 else 0
                
                pair_data.append({
                    'Paire': pair,
                    'Trades': count,
                    'P&L Total': f"{total_pnl_pair:+.4f}",
                    'P&L Moyen': f"{avg_pnl_pair:+.4f}",
                    'Taux Réussite': f"{win_rate_pair:.1f}%",
                    'Durée Moy': f"{avg_duration:.1f}min"
                })
            
            df_pair_display = pd.DataFrame(pair_data)
            st.dataframe(df_pair_display, use_container_width=True)
        
        # === GRAPHIQUES ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 P&L Cumulé")
            df_pnl_sorted = df_pnl.sort_values('timestamp')
            df_pnl_sorted['pnl_cumule'] = df_pnl_sorted['real_pnl'].cumsum()
            
            fig_cumul = px.line(df_pnl_sorted, x='timestamp', y='pnl_cumule',
                               title="Évolution P&L Cumulé",
                               color_discrete_sequence=['green' if total_pnl >= 0 else 'red'])
            fig_cumul.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_cumul, use_container_width=True)
        
        with col2:
            st.subheader("💰 P&L par Paire")
            if 'pair' in df_pnl.columns:
                pair_totals = df_pnl.groupby('pair')['real_pnl'].sum().sort_values(ascending=False)
                colors = ['green' if x > 0 else 'red' for x in pair_totals.values]
                
                fig_pairs = px.bar(x=pair_totals.index, y=pair_totals.values,
                                  title="P&L Total par Paire",
                                  color=colors, color_discrete_map={'green': 'green', 'red': 'red'})
                fig_pairs.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_pairs, use_container_width=True)
        
        # === TOP/WORST TRADES ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 5 Meilleurs Trades")
            if len(df_pnl) > 0:
                top_trades = df_pnl.nlargest(5, 'real_pnl')[['pair', 'real_pnl', 'timestamp']].copy()
                top_trades['P&L'] = top_trades['real_pnl'].apply(lambda x: f"{x:+.4f}")
                top_trades['Heure'] = top_trades['timestamp'].dt.strftime('%H:%M')
                st.dataframe(top_trades[['pair', 'P&L', 'Heure']], use_container_width=True)
        
        with col2:
            st.subheader("💥 Top 5 Pires Trades")
            if len(df_pnl) > 0:
                worst_trades = df_pnl.nsmallest(5, 'real_pnl')[['pair', 'real_pnl', 'timestamp']].copy()
                worst_trades['P&L'] = worst_trades['real_pnl'].apply(lambda x: f"{x:+.4f}")
                worst_trades['Heure'] = worst_trades['timestamp'].dt.strftime('%H:%M')
                st.dataframe(worst_trades[['pair', 'P&L', 'Heure']], use_container_width=True)
        
        # === ANALYSE TEMPORELLE ===
        st.subheader("⏰ Performance Temporelle")
        
        now = datetime.now()
        temporal_data = []
        
        for hours, label in [(1, "Dernière heure"), (6, "Dernières 6h"), (24, "Dernières 24h")]:
            cutoff = now - timedelta(hours=hours)
            recent = df_pnl[df_pnl['timestamp'] > cutoff]
            if len(recent) > 0:
                pnl_recent = recent['real_pnl'].sum()
                trades_recent = len(recent)
                temporal_data.append({
                    'Période': label,
                    'Trades': trades_recent,
                    'P&L': f"{pnl_recent:+.4f} USDC"
                })
        
        if temporal_data:
            df_temporal = pd.DataFrame(temporal_data)
            st.dataframe(df_temporal, use_container_width=True)
    
    else:
        st.warning("⚠️ Aucun trade avec P&L réel trouvé")
        st.info("Les colonnes 'capital_before' et 'capital_after' sont nécessaires pour calculer les vrais P&L")
    
    # === DONNÉES BRUTES ===
    with st.expander("🔍 Données Brutes (Derniers 10 trades)"):
        if len(df_trades) > 0:
            recent_trades = df_trades.head(10)[['pair', 'real_pnl', 'capital_before', 'capital_after', 'timestamp']]
            st.dataframe(recent_trades, use_container_width=True)

def show_trades(db):
    """Page Trades détaillés"""
    st.header("💹 Trades Détaillés")
    
    trades = get_real_time_data(db, "trades", 50)
    
    if trades:
        df = pd.DataFrame(trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        
        # Calcul P&L réel
        df['real_pnl'] = df['capital_after'] - df['capital_before']
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_pairs = st.multiselect("Paires", options=df['pair'].unique(), default=df['pair'].unique())
        
        with col2:
            pnl_filter = st.selectbox("P&L", ["Tous", "Gagnants", "Perdants"])
        
        with col3:
            time_filter = st.selectbox("Période", ["Toutes", "Dernière heure", "Dernières 6h", "Dernières 24h"])
        
        # Application des filtres
        df_filtered = df[df['pair'].isin(selected_pairs)]
        
        if pnl_filter == "Gagnants":
            df_filtered = df_filtered[df_filtered['real_pnl'] > 0]
        elif pnl_filter == "Perdants":
            df_filtered = df_filtered[df_filtered['real_pnl'] < 0]
        
        if time_filter != "Toutes":
            hours = {"Dernière heure": 1, "Dernières 6h": 6, "Dernières 24h": 24}[time_filter]
            cutoff = datetime.now() - timedelta(hours=hours)
            df_filtered = df_filtered[df_filtered['timestamp'] > cutoff]
        
        # Affichage du tableau
        display_cols = ['pair', 'real_pnl', 'entry_price', 'exit_price', 'duration_seconds', 'exit_reason', 'timestamp']
        if all(col in df_filtered.columns for col in display_cols):
            st.dataframe(df_filtered[display_cols], use_container_width=True)
        else:
            st.dataframe(df_filtered, use_container_width=True)
    
    else:
        st.info("Aucun trade disponible")

def show_logs(db):
    """Page Logs temps réel"""
    st.header("🔔 Logs Temps Réel")
    
    logs = get_real_time_data(db, "bot_logs", 100)
    
    if logs:
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            log_level = st.selectbox("Niveau", ["ALL", "INFO", "WARNING", "ERROR"])
        with col2:
            search_term = st.text_input("🔍 Rechercher dans les logs")
        
        # Application des filtres
        df_filtered = df.copy()
        
        if log_level != "ALL":
            df_filtered = df_filtered[df_filtered['level'] == log_level]
        
        if search_term:
            df_filtered = df_filtered[df_filtered['message'].str.contains(search_term, case=False, na=False)]
        
        # Affichage
        for _, log in df_filtered.head(50).iterrows():
            timestamp = log['timestamp'].strftime("%H:%M:%S")
            level = log.get('level', 'INFO')
            message = log.get('message', 'N/A')
            
            if level == "ERROR":
                st.error(f"[{timestamp}] {message}")
            elif level == "WARNING":
                st.warning(f"[{timestamp}] {message}")
            else:
                st.info(f"[{timestamp}] {message}")
    else:
        st.info("Aucun log disponible")

def main():
    """Fonction principale du dashboard"""
    # Titre principal
    st.title("🚀 ToTheMoon Trading Bot Dashboard")
    st.markdown("*Dashboard temps réel avec analyse des vrais P&L*")
    
    # Initialisation Firebase
    db = init_firebase()
    
    if db is None:
        st.error("❌ Impossible de se connecter à Firebase")
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", 
                           ["🎯 Vue d'ensemble", 
                            "📈 Performance", 
                            "💹 Trades", 
                            "🔔 Logs"])
    
    # Status en sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Status")
    st.sidebar.success("🔥 Firebase: Connecté")
    st.sidebar.info(f"🕐 Dernière MAJ: {datetime.now().strftime('%H:%M:%S')}")
    
    # Bouton de rafraîchissement
    if st.sidebar.button("🔄 Actualiser"):
        st.rerun()
    
    # Navigation vers les pages
    if page == "🎯 Vue d'ensemble":
        show_overview(db)
    elif page == "📈 Performance":
        show_performance(db)
    elif page == "💹 Trades":
        show_trades(db)
    elif page == "🔔 Logs":
        show_logs(db)

if __name__ == "__main__":
    main()

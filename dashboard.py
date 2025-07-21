"""
Dashboard Streamlit pour ToTheMoon Trading Bot
Interface temps réel connectée à Firebase - VERSION CORRIGÉE AVEC VRAIS P&L
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import firebase_admin
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz  # Pour le fuseau horaire Paris
import streamlit as st
from firebase_admin import credentials, firestore

# Configuration timezone Paris
PARIS_TZ = pytz.timezone('Europe/Paris')

def to_paris_time(dt):
    """Convertit datetime en timezone Paris"""
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(PARIS_TZ)

def now_paris():
    """Retourne l'heure actuelle Paris"""
    return datetime.now(PARIS_TZ)

# Configuration de la page
st.set_page_config(
    page_title="🚀 ToTheMoon Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import de la configuration avec gestion d'erreur améliorée
TradingConfig = None
APIConfig = None
BLACKLISTED_PAIRS = []
PRIORITY_USDC_PAIRS = []

try:
    # Ajouter le répertoire actuel au path si nécessaire
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from config import BLACKLISTED_PAIRS, PRIORITY_USDC_PAIRS, APIConfig, TradingConfig
    st.success("✅ Configuration chargée avec succès")
except ImportError as e:
    st.warning(f"⚠️ Importation partielle de la configuration: {str(e)}")
    try:
        # Essayer d'importer individuellement
        from config import TradingConfig
        st.info("✅ TradingConfig chargé")
    except:
        st.error("❌ TradingConfig non disponible")
    
    try:
        from config import APIConfig
        st.info("✅ APIConfig chargé")
    except:
        st.error("❌ APIConfig non disponible")
    
    try:
        from config import BLACKLISTED_PAIRS
        st.info("✅ BLACKLISTED_PAIRS chargé")
    except:
        BLACKLISTED_PAIRS = []
        st.warning("⚠️ BLACKLISTED_PAIRS par défaut")
    
    try:
        from config import PRIORITY_USDC_PAIRS
        st.info("✅ PRIORITY_USDC_PAIRS chargé")
    except:
        PRIORITY_USDC_PAIRS = []
        st.warning("⚠️ PRIORITY_USDC_PAIRS par défaut")

except Exception as e:
    st.error(f"❌ Erreur lors du chargement de la configuration: {str(e)}")
    st.info("📝 Utilisation des valeurs par défaut")

def init_firebase():
    """Initialise la connexion Firebase - CORRIGÉ pour éviter double initialisation"""
    try:
        # Essayer de récupérer une app Firebase existante
        app = firebase_admin.get_app()
        return firestore.client(app)
    except ValueError:
        # Aucune app existe, donc on peut l'initialiser
        try:
            # Essayer d'abord les secrets Streamlit Cloud
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                # Utiliser les secrets Streamlit Cloud
                firebase_credentials = dict(st.secrets['firebase'])
                cred = credentials.Certificate(firebase_credentials)
                app = firebase_admin.initialize_app(cred)
                st.success("🔥 Firebase initialisé avec les secrets Streamlit Cloud")
                return firestore.client(app)
            else:
                # Fallback sur le fichier local
                cred = credentials.Certificate('firebase_credentials.json')
                app = firebase_admin.initialize_app(cred)
                st.success("🔥 Firebase initialisé avec le fichier local")
                return firestore.client(app)
        except Exception as e:
            st.error(f"Erreur d'initialisation Firebase: {str(e)}")
            st.info("💡 Vérifiez que les secrets Firebase sont configurés dans Streamlit Cloud")
            return None

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

def get_total_trades_count(db) -> int:
    """Récupère le nombre total de trades dans Firebase"""
    try:
        if db is None:
            return 0
        
        # Compter tous les documents dans la collection trades
        docs = db.collection("trades").stream()
        count = sum(1 for _ in docs)
        return count
    except Exception as e:
        st.error(f"Erreur comptage trades: {str(e)}")
        return 0

def show_overview(db):
    """Page Vue d'ensemble - CORRIGÉE"""
    st.header("🎯 Vue d'Ensemble")
    
    # Indicateur de refresh temps réel
    st.caption(f"🔄 Données mises à jour: {now_paris().strftime('%H:%M:%S')}")
    
    # Récupération des données récentes pour affichage
    recent_trades = get_real_time_data(db, "trades", 10)
    
    # Récupération du nombre total de trades
    total_trades_count = get_total_trades_count(db)
    
    # Récupération de TOUS les trades pour les calculs P&L
    all_trades = get_real_time_data(db, "trades", 1000)  # Augmenter la limite
    
    if recent_trades:
        df_recent = pd.DataFrame(recent_trades)
        
        # Métriques basées sur les trades récents pour affichage capital actuel
        capital_current = df_recent['capital_after'].iloc[0] if len(df_recent) > 0 else 0
        
        # Calculs P&L sur TOUS les trades
        if all_trades:
            df_all = pd.DataFrame(all_trades)
            df_all['real_pnl'] = df_all['capital_after'] - df_all['capital_before']
            df_pnl = df_all[df_all['real_pnl'] != 0]
            
            total_pnl = df_pnl['real_pnl'].sum() if len(df_pnl) > 0 else 0
            profitable = len(df_pnl[df_pnl['real_pnl'] > 0]) if len(df_pnl) > 0 else 0
            win_rate = (profitable / len(df_pnl)) * 100 if len(df_pnl) > 0 else 0
        else:
            total_pnl = 0
            win_rate = 0
        
        # Métriques rapides
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Capital", f"{capital_current:,.2f} USDC")
        
        with col2:
            st.metric("📊 P&L Total", f"{total_pnl:+.4f} USDC")
        
        with col3:
            st.metric("🎯 Taux Réussite", f"{win_rate:.1f}%")
        
        with col4:
            # Afficher le VRAI nombre total de trades
            st.metric("📈 Total Trades", f"{total_trades_count}")
        
        # Section trades récents
        st.subheader("📋 Derniers Trades (10 plus récents)")
        if len(df_recent) > 0:
            df_recent['real_pnl'] = df_recent['capital_after'] - df_recent['capital_before']
            df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])
            
            display_recent = df_recent[['pair', 'real_pnl', 'capital_after', 'timestamp']].copy()
            display_recent['P&L'] = display_recent['real_pnl'].apply(lambda x: f"{x:+.4f}")
            display_recent['Heure'] = display_recent['timestamp'].dt.strftime('%H:%M:%S')
            display_recent = display_recent[['pair', 'P&L', 'capital_after', 'Heure']]
            display_recent.columns = ['Paire', 'P&L', 'Capital Après', 'Heure']
            
            st.dataframe(display_recent, use_container_width=True)
    else:
        st.info("Aucun trade disponible")

def show_performance(db):
    """Page Performance avec analyse réelle des P&L - CORRIGÉE"""
    st.header("📈 Performance Trading - Analyse Réelle")
    
    # Indicateur de refresh temps réel
    st.caption(f"🔄 Données mises à jour: {now_paris().strftime('%H:%M:%S')}")
    
    # Récupération de TOUS les trades (augmenter limite pour avoir toutes les données)
    trades = get_real_time_data(db, "trades", 1000)
    
    if not trades:
        st.error("❌ Aucun trade trouvé dans Firebase")
        return
    
    # Conversion en DataFrame
    df_trades = pd.DataFrame(trades)
    df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
    # Les données viennent déjà triées DESCENDING de Firebase, donc df_trades[0] = plus récent
    
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
        
        # Capital évolution - CORRIGÉ
        # df_trades[0] = plus récent (DESCENDING), df_trades[-1] = plus ancien
        capital_current = df_trades['capital_after'].iloc[0] if len(df_trades) > 0 else 0  # Plus récent
        capital_start = df_trades['capital_before'].iloc[-1] if len(df_trades) > 0 else 0   # Plus ancien
        
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
                count = int(pair_stats.loc[pair, ('real_pnl', 'count')]) #type: ignore
                total_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'sum')]
                avg_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'mean')]
                avg_duration = pair_stats.loc[pair, ('duration_seconds', 'mean')] / 60 if not pd.isna(pair_stats.loc[pair, ('duration_seconds', 'mean')]) else 0 #type: ignore
                
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
            # Trier par timestamp pour cumul chronologique
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
    
    # === DONNÉES BRUTES (10 PLUS RÉCENTS) - CORRIGÉ ===
    with st.expander("🔍 Données Brutes (10 plus récents)"):
        if len(df_trades) > 0:
            # df_trades est déjà trié DESCENDING, donc les 10 premiers sont les plus récents
            recent_trades = df_trades.head(10)[['pair', 'real_pnl', 'capital_before', 'capital_after', 'timestamp']]
            st.dataframe(recent_trades, use_container_width=True)

def show_trades(db):
    """Page Trades détaillés - CORRIGÉE"""
    st.header("💹 Trades Détaillés")
    
    # Indicateur de refresh temps réel
    st.caption(f"🔄 Données mises à jour: {now_paris().strftime('%H:%M:%S')}")
    
    # Récupérer plus de trades pour avoir toutes les données
    trades = get_real_time_data(db, "trades", 1000)
    
    if trades:
        df = pd.DataFrame(trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Les données viennent déjà triées DESCENDING, donc les plus récents en premier
        
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
    
    # Indicateur de refresh temps réel
    st.caption(f"🔄 Données mises à jour: {now_paris().strftime('%H:%M:%S')}")
    
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

def show_config():
    """Page Configuration - NOUVEAU"""
    st.header("⚙️ Configuration du Bot")
    
    # Indicateur de refresh temps réel
    st.caption(f"🔄 Configuration chargée: {now_paris().strftime('%H:%M:%S')}")
    
    if TradingConfig is None:
        st.error("❌ Configuration TradingConfig non disponible - Vérifiez config.py")
        return
    
    try:
        config = TradingConfig()
        
        # === PARAMÈTRES DE CAPITAL ===
        st.subheader("💰 Paramètres de Capital")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🎯 Objectif Quotidien", f"{config.DAILY_TARGET_PERCENT}%")
            st.metric("🛑 Stop Loss Quotidien", f"{config.DAILY_STOP_LOSS_PERCENT}%")
            st.metric("💼 Taille Position Base", f"{config.BASE_POSITION_SIZE_PERCENT}%")
            st.metric("💰 Position Min", f"{config.MIN_POSITION_SIZE_USDC} USDC")
        
        with col2:
            st.metric("💰 Position Max", f"{config.MAX_POSITION_SIZE_USDC} USDC")
            st.metric("📈 Positions Max", f"{config.MAX_OPEN_POSITIONS}")
            st.metric("🔄 Trades/Paire Max", f"{config.MAX_TRADES_PER_PAIR}")
            st.metric("📊 Exposition Max/Asset", f"{config.MAX_EXPOSURE_PER_ASSET_PERCENT}%")
        
        # === PARAMÈTRES DE TRADING ===
        st.subheader("🎯 Paramètres de Trading")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🔻 Stop Loss", f"{config.STOP_LOSS_PERCENT}%")
            st.metric("🔺 Take Profit", f"{config.TAKE_PROFIT_PERCENT}%")
            st.metric("📈 Trailing Activation", f"{config.TRAILING_ACTIVATION_PERCENT}%")
            st.metric("📊 Trailing Step", f"{config.TRAILING_STEP_PERCENT}%")
        
        with col2:
            st.metric("⏱️ Intervalle Min Trades", f"{config.MIN_TRADE_INTERVAL_SECONDS}s")
            st.metric("⏰ Trades Max/Heure", f"{config.MAX_TRADES_PER_HOUR}")
            st.metric("🔄 Scan Interval", f"{config.SCAN_INTERVAL}s")
            st.metric("📊 Timeframe", config.TIMEFRAME)
        
        # === NOUVEAUX PARAMÈTRES OPTIMISÉS ===
        st.subheader("🚀 Optimisations Récentes")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💥 Pertes Consécutives Max", f"{config.MAX_CONSECUTIVE_LOSSES}")
            st.metric("⏸️ Pause après Pertes", f"{config.CONSECUTIVE_LOSS_PAUSE_MINUTES} min")
            breakout_status = "✅ Activé" if config.ENABLE_BREAKOUT_CONFIRMATION else "❌ Désactivé"
            st.metric("🎯 Confirmation Cassure", breakout_status)
            st.metric("📊 Seuil Cassure", f"{config.BREAKOUT_CONFIRMATION_PERCENT}%")
        
        with col2:
            consecutive_protection = "✅ Activé" if config.ENABLE_CONSECUTIVE_LOSS_PROTECTION else "❌ Désactivé"
            st.metric("🛡️ Protection Pertes", consecutive_protection)
            auto_resume = "✅ Activé" if config.AUTO_RESUME_AFTER_PAUSE else "❌ Désactivé"
            st.metric("🔄 Reprise Auto", auto_resume)
            st.metric("💹 Volume Min", f"{config.MIN_VOLUME_USDC:,.0f}")
            st.metric("📈 Spread Max", f"{config.MAX_SPREAD_PERCENT}%")
        
        # === INDICATEURS TECHNIQUES ===
        st.subheader("📊 Indicateurs Techniques")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**EMA**")
            st.metric("EMA Rapide", f"{config.EMA_FAST_PERIOD}")
            st.metric("EMA Lente", f"{config.EMA_SLOW_PERIOD}")
        
        with col2:
            st.write("**RSI & MACD**")
            st.metric("RSI Période", f"{config.RSI_PERIOD}")
            st.metric("RSI Survente", f"{config.RSI_OVERSOLD_LEVEL}")
            st.metric("MACD Rapide", f"{config.MACD_FAST_PERIOD}")
        
        with col3:
            st.write("**Bollinger**")
            st.metric("BB Période", f"{config.BOLLINGER_PERIOD}")
            st.metric("BB Écart-Type", f"{config.BOLLINGER_STD_DEV}")
            st.metric("Conditions Min", f"{config.MIN_SIGNAL_CONDITIONS}")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'accès à TradingConfig: {str(e)}")
    
    # === PAIRES BLACKLISTÉES ===
    st.subheader("⚫ Paires Blacklistées")
    if BLACKLISTED_PAIRS:
        st.write("Ces paires sont exclues du trading :")
        cols = st.columns(min(4, len(BLACKLISTED_PAIRS)))
        for i, pair in enumerate(BLACKLISTED_PAIRS):
            with cols[i % len(cols)]:
                st.error(f"❌ {pair}")
    else:
        st.info("Aucune paire blacklistée")
    
    # === PAIRES PRIORITAIRES ===
    st.subheader("✅ Paires Prioritaires")
    if PRIORITY_USDC_PAIRS:
        st.write("Ces paires sont privilégiées pour le trading :")
        cols = st.columns(min(3, len(PRIORITY_USDC_PAIRS)))
        for i, pair in enumerate(PRIORITY_USDC_PAIRS):
            with cols[i % len(cols)]:
                st.success(f"✅ {pair}")
    else:
        st.info("Aucune paire prioritaire définie")
    
    # === CONFIGURATION API ===
    if APIConfig:
        st.subheader("🔑 Configuration API")
        try:
            api_config = APIConfig()
            
            col1, col2 = st.columns(2)
            with col1:
                testnet_status = "🧪 TESTNET" if api_config.TESTNET else "🔥 PRODUCTION"
                st.metric("Mode", testnet_status)
                binance_status = "✅ Configuré" if api_config.BINANCE_API_KEY else "❌ Manquant"
                st.metric("Binance API", binance_status)
            
            with col2:
                telegram_status = "✅ Configuré" if api_config.TELEGRAM_BOT_TOKEN else "❌ Manquant"
                st.metric("Telegram", telegram_status)
                sheets_status = "✅ Activé" if api_config.ENABLE_GOOGLE_SHEETS else "❌ Désactivé"
                st.metric("Google Sheets", sheets_status)
        except Exception as e:
            st.error(f"❌ Erreur lors de l'accès à APIConfig: {str(e)}")
    else:
        st.warning("⚠️ Configuration API non disponible")

def main():
    """Fonction principale du dashboard - CORRIGÉE"""
    # Titre principal
    st.title("🚀 ToTheMoon Trading Bot Dashboard")
    st.markdown("*Dashboard temps réel avec analyse des vrais P&L*")
    
    # Initialisation Firebase
    db = init_firebase()
    
    if db is None:
        st.error("❌ Impossible de se connecter à Firebase")
        st.stop()
    
    # Sidebar navigation - AJOUT ONGLET CONFIG
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", 
                           ["🎯 Vue d'ensemble", 
                            "📈 Performance", 
                            "💹 Trades", 
                            "🔔 Logs",
                            "⚙️ Configuration"])
    
    # Status en sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Status")
    st.sidebar.success("🔥 Firebase: Connecté")
    st.sidebar.info(f"🕐 Dernière MAJ: {now_paris().strftime('%H:%M:%S')}")
    
    # 🔄 AUTO-REFRESH GLOBAL (corrigé)
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (10s)", value=True, key="global_refresh")
    
    # Bouton de rafraîchissement manuel
    if st.sidebar.button("🔄 Actualiser"):
        st.rerun()
    
    # Initialiser session state pour auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = now_paris()
    
    # Auto-refresh logic fiable
    if auto_refresh:
        now = now_paris()
        time_since_refresh = (now - st.session_state.last_refresh).total_seconds()
        
        if time_since_refresh >= 10:  # 10 secondes écoulées
            st.session_state.last_refresh = now
            st.rerun()
    
    # Navigation vers les pages (toujours afficher le contenu)
    if page == "🎯 Vue d'ensemble":
        show_overview(db)
    elif page == "📈 Performance":
        show_performance(db)
    elif page == "💹 Trades":
        show_trades(db)
    elif page == "🔔 Logs":
        show_logs(db)
    elif page == "⚙️ Configuration":
        show_config()

if __name__ == "__main__":
    main()
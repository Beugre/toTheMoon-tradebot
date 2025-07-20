"""
Dashboard Streamlit pour ToTheMoon Trading Bot
Interface temps réel connectée à Firebase
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

# CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #2ca02c;
    }
    .warning-metric {
        border-left-color: #ff7f0e;
    }
    .danger-metric {
        border-left-color: #d62728;
    }
    .status-active {
        color: #2ca02c;
        font-weight: bold;
    }
    .status-inactive {
        color: #d62728;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_firebase():
    """Initialise Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            # Priorité 1: Streamlit Cloud secrets
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
                firebase_admin.initialize_app(cred)
            # Priorité 2: Fichier local
            elif os.path.exists("firebase_credentials.json"):
                cred = credentials.Certificate("firebase_credentials.json")
                firebase_admin.initialize_app(cred)
            else:
                st.error("❌ Configuration Firebase non trouvée. Ajoutez firebase_credentials.json ou configurez les secrets Streamlit.")
                return None
        
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"❌ Erreur Firebase: {e}")
        return None

def get_real_time_data(db, collection: str, limit: int = 50) -> List[Dict]:
    """Récupère les données en temps réel depuis Firebase"""
    try:
        docs = db.collection(collection).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            data.append(doc_data)
        return data
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des données {collection}: {e}")
        return []

def format_timestamp(timestamp):
    """Formate un timestamp pour l'affichage"""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp
    elif hasattr(timestamp, 'timestamp'):
        dt = datetime.fromtimestamp(timestamp.timestamp())
        return dt.strftime("%H:%M:%S")
    else:
        return str(timestamp)

def main():
    # Titre principal
    st.title("🚀 ToTheMoon Trading Bot Dashboard")
    st.markdown("---")
    
    # Initialisation Firebase
    db = init_firebase()
    if not db:
        st.stop()
    
    # Sidebar pour navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox(
        "Choisir une page:",
        ["📊 Vue d'ensemble", "💹 Trades", "📈 Performance", "🔔 Logs temps réel", "⚙️ Configuration"]
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
    if auto_refresh:
        st.sidebar.info("⏱️ Refresh automatique activé")
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Manuel"):
        st.rerun()
    
    # Navigation des pages
    if page == "📊 Vue d'ensemble":
        show_overview(db)
    elif page == "💹 Trades":
        show_trades(db)
    elif page == "📈 Performance":
        show_performance(db)
    elif page == "🔔 Logs temps réel":
        show_logs(db)
    elif page == "⚙️ Configuration":
        show_config()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

def show_overview(db):
    """Page Vue d'ensemble"""
    st.header("📊 Vue d'ensemble")
    
    # Récupération des données récentes
    logs = get_real_time_data(db, "bot_logs", 10)
    trades = get_real_time_data(db, "trades", 10)
    metrics = get_real_time_data(db, "metrics", 5)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Statut du bot
        if logs:
            last_log = logs[0]
            if "RUNNING" in last_log.get('message', ''):
                st.markdown('<p class="status-active">🟢 Bot Actif</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="status-inactive">🔴 Bot Inactif</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-inactive">❓ Statut Inconnu</p>', unsafe_allow_html=True)
    
    with col2:
        # Capital total
        if metrics:
            capital = metrics[0].get('capital_total', 0)
            st.metric("💰 Capital Total", f"{capital:,.2f} USDC")
        else:
            st.metric("💰 Capital Total", "N/A")
    
    with col3:
        # Trades aujourd'hui
        today = datetime.now().date()
        trades_today = [t for t in trades if datetime.fromisoformat(t.get('timestamp', '').replace('Z', '+00:00')).date() == today]
        st.metric("📈 Trades Aujourd'hui", len(trades_today))
    
    with col4:
        # Dernière activité
        if logs:
            last_activity = format_timestamp(logs[0].get('timestamp'))
            st.metric("⏰ Dernière Activité", last_activity)
        else:
            st.metric("⏰ Dernière Activité", "N/A")
    
    st.markdown("---")
    
    # Graphique de performance récente
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Performance Récente")
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            if 'timestamp' in df_metrics.columns and 'capital_total' in df_metrics.columns:
                fig = px.line(df_metrics, x='timestamp', y='capital_total', 
                            title="Évolution du Capital")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pas assez de données pour le graphique")
        else:
            st.info("Aucune donnée de performance disponible")
    
    with col2:
        st.subheader("🔔 Derniers Logs")
        if logs:
            for log in logs[:5]:
                timestamp = format_timestamp(log.get('timestamp'))
                level = log.get('level', 'INFO')
                message = log.get('message', '')
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] {message}")
                else:
                    st.info(f"[{timestamp}] {message}")
        else:
            st.info("Aucun log disponible")

def show_trades(db):
    """Page Trades"""
    st.header("💹 Trades")
    
    trades = get_real_time_data(db, "trades", 100)
    
    if trades:
        df = pd.DataFrame(trades)
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            pairs = df['pair'].unique() if 'pair' in df.columns else []
            selected_pairs = st.multiselect("Paires", pairs, default=pairs)
        
        with col2:
            statuses = df['status'].unique() if 'status' in df.columns else []
            selected_statuses = st.multiselect("Statut", statuses, default=statuses)
        
        with col3:
            date_filter = st.date_input("Date", datetime.now().date())
        
        # Filtrage des données
        if selected_pairs:
            df = df[df['pair'].isin(selected_pairs)]
        if selected_statuses:
            df = df[df['status'].isin(selected_statuses)]
        
        # Affichage du tableau
        st.dataframe(df, use_container_width=True)
        
        # Statistiques
        st.subheader("📊 Statistiques")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", len(df))
        with col2:
            profitable = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
            st.metric("Trades Rentables", profitable)
        with col3:
            if 'pnl' in df.columns:
                total_pnl = df['pnl'].sum()
                st.metric("P&L Total", f"{total_pnl:.2f} USDC")
        with col4:
            if len(df) > 0 and 'pnl' in df.columns:
                win_rate = (profitable / len(df)) * 100
                st.metric("Taux de Réussite", f"{win_rate:.1f}%")
    
    else:
        st.info("Aucun trade disponible")

def show_performance(db):
    """Page Performance"""
    st.header("📈 Performance")
    
    metrics = get_real_time_data(db, "metrics", 500)
    
    if metrics:
        df = pd.DataFrame(metrics)
        
        # Graphique principal
        if 'timestamp' in df.columns and 'capital_total' in df.columns:
            fig = px.line(df, x='timestamp', y='capital_total', 
                        title="Évolution du Capital Total")
            st.plotly_chart(fig, use_container_width=True)
        
        # Métriques de performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Répartition du Portefeuille")
            if 'usdc_balance' in df.columns and 'crypto_value' in df.columns:
                latest = df.iloc[0]
                labels = ['USDC', 'Crypto']
                values = [latest['usdc_balance'], latest['crypto_value']]
                
                fig = px.pie(values=values, names=labels, title="Répartition USDC vs Crypto")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Statistiques")
            if len(df) > 1:
                first_capital = df.iloc[-1]['capital_total']
                last_capital = df.iloc[0]['capital_total']
                total_return = ((last_capital - first_capital) / first_capital) * 100
                
                st.metric("🎯 Rendement Total", f"{total_return:.2f}%")
                st.metric("💰 Capital Début", f"{first_capital:,.2f} USDC")
                st.metric("💰 Capital Actuel", f"{last_capital:,.2f} USDC")
    
    else:
        st.info("Aucune donnée de performance disponible")

def show_logs(db):
    """Page Logs temps réel"""
    st.header("🔔 Logs Temps Réel")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.selectbox("Niveau", ["ALL", "INFO", "WARNING", "ERROR"])
    with col2:
        search_term = st.text_input("🔍 Rechercher dans les logs")
    
    # Récupération des logs
    logs = get_real_time_data(db, "bot_logs", 200)
    
    if logs:
        # Filtrage
        if log_level != "ALL":
            logs = [log for log in logs if log.get('level') == log_level]
        
        if search_term:
            logs = [log for log in logs if search_term.lower() in log.get('message', '').lower()]
        
        # Affichage
        st.subheader(f"📝 {len(logs)} logs trouvés")
        
        for log in logs:
            timestamp = format_timestamp(log.get('timestamp'))
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            
            if level == 'ERROR':
                st.error(f"[{timestamp}] {message}")
            elif level == 'WARNING':
                st.warning(f"[{timestamp}] {message}")
            else:
                st.info(f"[{timestamp}] {message}")
    
    else:
        st.info("Aucun log disponible")

def show_config():
    """Page Configuration"""
    st.header("⚙️ Configuration")
    
    st.subheader("🔧 Paramètres du Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Connexion Firebase**")
        if os.path.exists("firebase_credentials.json"):
            st.success("✅ Credentials Firebase trouvés")
        else:
            st.error("❌ Credentials Firebase manquants")
        
        st.write("**Collections Firebase**")
        st.info("📊 bot_logs - Logs du bot")
        st.info("💹 trades - Historique des trades")
        st.info("📈 metrics - Métriques de performance")
        st.info("🔔 performance - Données de performance")
    
    with col2:
        st.write("**Actions**")
        
        if st.button("🧹 Nettoyer le Cache"):
            st.cache_resource.clear()
            st.success("Cache nettoyé !")
        
        if st.button("🔄 Tester Connexion Firebase"):
            db = init_firebase()
            if db:
                st.success("✅ Connexion Firebase OK")
            else:
                st.error("❌ Problème de connexion Firebase")

if __name__ == "__main__":
    main()

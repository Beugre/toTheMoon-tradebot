"""
Version simplifiée du dashboard avec données de test
Pour tester l'interface sans Firebase
"""

import json
import os
import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="🚀 ToTheMoon Bot Dashboard (Demo)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_sample_data():
    """Charge les données de test"""
    if os.path.exists('sample_data.json'):
        with open('sample_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Génération de données de base si le fichier n'existe pas
        return {
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': '🟢 [RUNNING] Bot lancé avec succès',
                    'component': 'TradingBot'
                }
            ],
            'trades': [],
            'metrics': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'capital_total': 22859.56,
                    'usdc_balance': 19247.10,
                    'crypto_value': 3612.46,
                    'daily_pnl': 125.40,
                    'trades_count': 12,
                    'win_rate': 66.7
                }
            ]
        }

def main():
    # Titre principal
    st.title("🚀 ToTheMoon Trading Bot Dashboard")
    st.markdown("*Version Demo avec données de test*")
    st.markdown("---")
    
    # Chargement des données
    data = load_sample_data()
    
    # Sidebar pour navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox(
        "Choisir une page:",
        ["📊 Vue d'ensemble", "💹 Trades", "📈 Performance", "🔔 Logs", "🛠️ Outils"]
    )
    
    # Navigation des pages
    if page == "📊 Vue d'ensemble":
        show_overview(data)
    elif page == "💹 Trades":
        show_trades(data)
    elif page == "📈 Performance":
        show_performance(data)
    elif page == "🔔 Logs":
        show_logs(data)
    elif page == "🛠️ Outils":
        show_tools()

def show_overview(data):
    """Page Vue d'ensemble"""
    st.header("📊 Vue d'ensemble")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<p style="color: green; font-weight: bold;">🟢 Bot Actif</p>', unsafe_allow_html=True)
        st.caption("Statut en temps réel")
    
    with col2:
        if data['metrics']:
            capital = data['metrics'][0]['capital_total']
            st.metric("💰 Capital Total", f"{capital:,.2f} USDC", "+2.3%")
        else:
            st.metric("💰 Capital Total", "22,859.56 USDC", "+2.3%")
    
    with col3:
        trades_today = len([t for t in data['trades'] if 'timestamp' in t])
        st.metric("📈 Trades Aujourd'hui", trades_today, "+3")
    
    with col4:
        st.metric("⏰ Dernière Activité", "Il y a 2 min")
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Performance Récente")
        
        # Données simulées pour le graphique
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
        capital_values = []
        base_capital = 22000
        
        for i, date in enumerate(dates):
            change = random.uniform(-20, 50)
            base_capital += change
            capital_values.append(base_capital)
        
        df_perf = pd.DataFrame({
            'Date': dates,
            'Capital': capital_values
        })
        
        fig = px.line(df_perf, x='Date', y='Capital', title="Évolution du Capital (7 jours)")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Répartition du Portefeuille")
        
        if data['metrics']:
            latest = data['metrics'][0]
            labels = ['USDC', 'Crypto']
            values = [latest['usdc_balance'], latest['crypto_value']]
        else:
            labels = ['USDC', 'Crypto']
            values = [19247, 3612]
        
        fig = px.pie(values=values, names=labels, title="USDC vs Crypto")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Derniers logs
    st.subheader("🔔 Derniers Events")
    for log in data['logs'][:5]:
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        timestamp = log.get('timestamp', '')
        
        if level == 'ERROR':
            st.error(f"[{timestamp[:19]}] {message}")
        elif level == 'WARNING':
            st.warning(f"[{timestamp[:19]}] {message}")
        else:
            st.info(f"[{timestamp[:19]}] {message}")

def show_trades(data):
    """Page Trades"""
    st.header("💹 Trades")
    
    if data['trades']:
        df = pd.DataFrame(data['trades'])
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            pairs = df['pair'].unique() if 'pair' in df.columns else ['EURUSDT']
            selected_pairs = st.multiselect("Paires", pairs, default=pairs)
        
        with col2:
            statuses = df['status'].unique() if 'status' in df.columns else ['OPEN', 'CLOSED']
            selected_statuses = st.multiselect("Statut", statuses, default=statuses)
        
        with col3:
            date_filter = st.date_input("Date", datetime.now().date())
        
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
            else:
                st.metric("P&L Total", "N/A")
        with col4:
            if len(df) > 0 and profitable > 0:
                win_rate = (profitable / len(df)) * 100
                st.metric("Taux de Réussite", f"{win_rate:.1f}%")
            else:
                st.metric("Taux de Réussite", "N/A")
    
    else:
        st.info("Aucun trade disponible")
        st.markdown("### 📝 Exemple de structure de trade:")
        st.code("""
        {
            "timestamp": "2025-07-21T10:30:00",
            "pair": "EURUSDT",
            "side": "LONG",
            "entry_price": 1.0850,
            "exit_price": 1.0875,
            "quantity": 500.0,
            "pnl": 12.50,
            "status": "CLOSED"
        }
        """, language="json")

def show_performance(data):
    """Page Performance"""
    st.header("📈 Performance")
    
    if data['metrics']:
        df = pd.DataFrame(data['metrics'])
        
        # Conversion des timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Graphique principal
        if 'capital_total' in df.columns:
            fig = px.line(df, x='timestamp', y='capital_total', 
                        title="Évolution du Capital Total")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Métriques de performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Métriques Clés")
            if len(df) > 1:
                first_capital = df.iloc[-1]['capital_total']
                last_capital = df.iloc[0]['capital_total']
                total_return = ((last_capital - first_capital) / first_capital) * 100
                
                st.metric("🎯 Rendement Total", f"{total_return:.2f}%")
                st.metric("💰 Capital Début", f"{first_capital:,.2f} USDC")
                st.metric("💰 Capital Actuel", f"{last_capital:,.2f} USDC")
                
                # Max/Min capital
                max_capital = df['capital_total'].max()
                min_capital = df['capital_total'].min()
                st.metric("📈 Capital Max", f"{max_capital:,.2f} USDC")
                st.metric("📉 Capital Min", f"{min_capital:,.2f} USDC")
        
        with col2:
            st.subheader("📈 P&L Journalier")
            if 'daily_pnl' in df.columns:
                fig = px.bar(df.head(30), x='timestamp', y='daily_pnl', 
                           title="P&L Journalier (30 derniers jours)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Aucune donnée de performance disponible")

def show_logs(data):
    """Page Logs"""
    st.header("🔔 Logs du Bot")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.selectbox("Niveau", ["ALL", "INFO", "WARNING", "ERROR"])
    with col2:
        search_term = st.text_input("🔍 Rechercher")
    
    # Filtrage des logs
    logs = data['logs']
    if log_level != "ALL":
        logs = [log for log in logs if log.get('level') == log_level]
    
    if search_term:
        logs = [log for log in logs if search_term.lower() in log.get('message', '').lower()]
    
    # Affichage
    st.subheader(f"📝 {len(logs)} logs trouvés")
    
    for log in logs:
        timestamp = log.get('timestamp', '')[:19]
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        component = log.get('component', '')
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if level == 'ERROR':
                st.error(f"[{timestamp}] {message}")
            elif level == 'WARNING':
                st.warning(f"[{timestamp}] {message}")
            else:
                st.info(f"[{timestamp}] {message}")
        with col2:
            st.caption(f"📦 {component}")

def show_tools():
    """Page Outils"""
    st.header("🛠️ Outils")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Génération de Données")
        
        if st.button("🎲 Générer Données de Test"):
            # Simulation de génération
            with st.spinner("Génération en cours..."):
                import time
                time.sleep(2)
            st.success("✅ Données de test générées!")
            st.info("Rechargez la page pour voir les nouvelles données")
        
        st.subheader("🔧 Configuration")
        
        refresh_rate = st.slider("Taux de rafraîchissement (secondes)", 5, 60, 30)
        st.write(f"Rafraîchissement configuré à {refresh_rate}s")
        
        dark_mode = st.checkbox("🌙 Mode sombre", value=False)
        if dark_mode:
            st.info("Mode sombre activé!")
    
    with col2:
        st.subheader("📈 Statistiques Système")
        
        st.metric("🔗 Connexion Firebase", "Demo Mode")
        st.metric("📊 Collections", "3 (logs, trades, metrics)")
        st.metric("⚡ Performance", "Excellent")
        
        st.subheader("🚀 Actions Rapides")
        
        if st.button("🔄 Simuler Refresh"):
            st.success("Données actualisées!")
        
        if st.button("📤 Export Données"):
            st.info("Export simulé - fichier demo_export.json")
        
        if st.button("🧹 Reset Demo"):
            st.warning("Reset de la demo effectué!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🔥 Analyseur Firebase - Bot Trading
Analyse temps réel des 30 derniers trades et performances
"""

import json
import os
from datetime import datetime, timedelta

import firebase_admin
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from firebase_admin import credentials, firestore
from plotly.subplots import make_subplots


def init_firebase():
    """Initialise la connexion Firebase"""
    # Chemin vers le fichier de credentials
    cred_path = "credentials.json"
    
    if not os.path.exists(cred_path):
        print("❌ Fichier credentials.json non trouvé")
        print("📥 Téléchargez-le depuis Firebase Console → Project Settings → Service Accounts")
        return None
    
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("✅ Connexion Firebase établie")
        return db
    except Exception as e:
        print(f"❌ Erreur connexion Firebase: {e}")
        return None

def get_firebase_data(db, collection_name, limit=100):
    """Récupère les données d'une collection Firebase"""
    try:
        docs = db.collection(collection_name).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            data.append(doc_data)
        
        print(f"📊 Collection '{collection_name}': {len(data)} documents récupérés")
        return data
    except Exception as e:
        print(f"❌ Erreur récupération {collection_name}: {e}")
        return []

def analyze_trades(trades_data):
    """Analyse les données de trading"""
    if not trades_data:
        print("⚠️ Aucune donnée de trade trouvée")
        return None
    
    df = pd.DataFrame(trades_data)
    
    # Conversion des timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
    print(f"\n📈 ANALYSE DES {len(df)} DERNIERS TRADES")
    print("="*50)
    
    # Statistiques générales
    if 'pnl' in df.columns:
        total_pnl = df['pnl'].sum()
        profitable_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        win_rate = (profitable_trades / len(df)) * 100 if len(df) > 0 else 0
        
        print(f"💰 P&L Total: {total_pnl:.2f} USDC")
        print(f"✅ Trades gagnants: {profitable_trades}")
        print(f"❌ Trades perdants: {losing_trades}")
        print(f"🎯 Taux de réussite: {win_rate:.1f}%")
        
        if 'pnl' in df.columns:
            avg_win = df[df['pnl'] > 0]['pnl'].mean() if profitable_trades > 0 else 0
            avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            print(f"📊 Gain moyen: {avg_win:.2f} USDC")
            print(f"📉 Perte moyenne: {avg_loss:.2f} USDC")
    
    # Analyse par paires
    if 'pair' in df.columns:
        print(f"\n📊 ANALYSE PAR PAIRES:")
        pair_stats = df.groupby('pair').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(2)
        pair_stats.columns = ['Trades', 'P&L Total', 'P&L Moyen']
        print(pair_stats.sort_values('P&L Total', ascending=False))
    
    # Trades récents
    print(f"\n🕒 5 DERNIERS TRADES:")
    recent_cols = ['timestamp', 'pair', 'pnl', 'status'] if all(col in df.columns for col in ['timestamp', 'pair', 'pnl', 'status']) else df.columns[:4]
    print(df[recent_cols].head().to_string(index=False))
    
    return df

def analyze_metrics(metrics_data):
    """Analyse les métriques de performance"""
    if not metrics_data:
        print("⚠️ Aucune donnée de métrique trouvée")
        return None
    
    df = pd.DataFrame(metrics_data)
    
    # Conversion des timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
    print(f"\n💹 MÉTRIQUES DE PERFORMANCE")
    print("="*30)
    
    # Dernières métriques
    if len(df) > 0:
        latest = df.iloc[-1]
        
        # Affichage des métriques disponibles
        for col in df.columns:
            if col != 'timestamp' and col != 'id':
                value = latest[col]
                if isinstance(value, (int, float)):
                    if 'capital' in col.lower() or 'balance' in col.lower():
                        print(f"💰 {col}: {value:,.2f} USDC")
                    elif 'pnl' in col.lower():
                        print(f"📈 {col}: {value:+.2f} USDC")
                    elif 'rate' in col.lower() or 'percent' in col.lower():
                        print(f"📊 {col}: {value:.1f}%")
                    else:
                        print(f"📊 {col}: {value}")
    
    return df

def create_performance_charts(trades_df, metrics_df):
    """Crée les graphiques de performance"""
    print(f"\n📊 GÉNÉRATION DES GRAPHIQUES...")
    
    # Graphique P&L cumulé
    if trades_df is not None and 'pnl' in trades_df.columns and 'timestamp' in trades_df.columns:
        trades_df['pnl_cumule'] = trades_df['pnl'].cumsum()
        
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Scatter(
            x=trades_df['timestamp'],
            y=trades_df['pnl_cumule'],
            mode='lines+markers',
            name='P&L Cumulé',
            line=dict(color='green')
        ))
        
        fig_pnl.update_layout(
            title="📈 P&L Cumulé des Trades",
            xaxis_title="Temps",
            yaxis_title="P&L (USDC)",
            template="plotly_dark"
        )
        
        # Sauvegarde
        fig_pnl.write_html("performance_pnl.html")
        print("✅ Graphique P&L sauvé: performance_pnl.html")
    
    # Graphique évolution capital
    if metrics_df is not None:
        capital_cols = [col for col in metrics_df.columns if 'capital' in col.lower()]
        if capital_cols and 'timestamp' in metrics_df.columns:
            fig_capital = go.Figure()
            
            for col in capital_cols:
                fig_capital.add_trace(go.Scatter(
                    x=metrics_df['timestamp'],
                    y=metrics_df[col],
                    mode='lines',
                    name=col
                ))
            
            fig_capital.update_layout(
                title="💰 Évolution du Capital",
                xaxis_title="Temps",
                yaxis_title="Capital (USDC)",
                template="plotly_dark"
            )
            
            fig_capital.write_html("performance_capital.html")
            print("✅ Graphique Capital sauvé: performance_capital.html")

def generate_summary_report(trades_df, metrics_df):
    """Génère un rapport de synthèse"""
    report = f"""
# 🚀 RAPPORT DE PERFORMANCE - {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 📊 RÉSUMÉ EXÉCUTIF
"""
    
    if trades_df is not None and len(trades_df) > 0:
        total_pnl = trades_df['pnl'].sum()
        total_trades = len(trades_df)
        win_rate = (len(trades_df[trades_df['pnl'] > 0]) / total_trades * 100) if total_trades > 0 else 0
        
        report += f"""
### Trades
- **Total trades analysés**: {total_trades}
- **P&L total**: {total_pnl:+.2f} USDC
- **Taux de réussite**: {win_rate:.1f}%
- **Période**: {trades_df['timestamp'].min()} → {trades_df['timestamp'].max()}
"""
    
    if metrics_df is not None and len(metrics_df) > 0:
        latest_metrics = metrics_df.iloc[-1]
        report += f"""
### Capital
"""
        for col in metrics_df.columns:
            if col not in ['timestamp', 'id'] and isinstance(latest_metrics[col], (int, float)):
                report += f"- **{col}**: {latest_metrics[col]:,.2f}\n"
    
    # Sauvegarde du rapport
    with open("rapport_performance.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("✅ Rapport sauvé: rapport_performance.md")
    print(report)

def main():
    """Fonction principale"""
    print("🔥 ANALYSEUR FIREBASE - BOT TRADING")
    print("="*50)
    
    # Connexion Firebase
    db = init_firebase()
    if not db:
        return
    
    # Récupération des données
    print("\n📥 RÉCUPÉRATION DES DONNÉES...")
    trades_data = get_firebase_data(db, "trades", 30)
    metrics_data = get_firebase_data(db, "metrics", 50)
    logs_data = get_firebase_data(db, "bot_logs", 20)
    
    # Analyse des trades
    trades_df = analyze_trades(trades_data)
    
    # Analyse des métriques
    metrics_df = analyze_metrics(metrics_data)
    
    # Génération des graphiques
    create_performance_charts(trades_df, metrics_df)
    
    # Rapport de synthèse
    generate_summary_report(trades_df, metrics_df)
    
    # Logs récents
    if logs_data:
        print(f"\n🔔 5 DERNIERS LOGS:")
        for i, log in enumerate(logs_data[:5]):
            timestamp = log.get('timestamp', 'N/A')
            level = log.get('level', 'INFO')
            message = log.get('message', '')[:100] + "..." if len(log.get('message', '')) > 100 else log.get('message', '')
            print(f"{i+1}. [{timestamp}] {level}: {message}")
    
    print(f"\n✅ ANALYSE TERMINÉE")
    print("📁 Fichiers générés:")
    print("   - performance_pnl.html")
    print("   - performance_capital.html") 
    print("   - rapport_performance.md")

if __name__ == "__main__":
    main()

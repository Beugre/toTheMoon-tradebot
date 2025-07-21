#!/usr/bin/env python3
"""
Analyseur de performances Firebase CORRIGÉ - Analyse réelle des P&L
"""

import json
from datetime import datetime, timedelta

import firebase_admin
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from firebase_admin import credentials, firestore
from plotly.subplots import make_subplots


def init_firebase():
    """Initialise la connexion Firebase"""
    try:
        firebase_admin.get_app()
        print("✅ Firebase déjà initialisé")
    except ValueError:
        cred = credentials.Certificate('firebase_credentials.json')
        firebase_admin.initialize_app(cred)
        print("🔥 Firebase initialisé avec succès")
    
    return firestore.client()

def get_trades_data(db, limit=30):
    """Récupère les derniers trades depuis Firebase"""
    print(f"📊 Récupération des {limit} derniers trades...")
    
    trades_ref = db.collection('trades')
    docs = trades_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
    
    trades = []
    for doc in docs:
        trade_data = doc.to_dict()
        trade_data['id'] = doc.id
        trades.append(trade_data)
    
    print(f"✅ {len(trades)} trades récupérés")
    return trades

def analyze_real_performance(trades_data):
    """Analyse CORRECTE des performances avec pnl_net"""
    print("\n🎯 ANALYSE PERFORMANCE RÉELLE (PNL_NET)")
    print("=" * 60)
    
    if not trades_data:
        print("❌ Aucun trade trouvé")
        return None
    
    df = pd.DataFrame(trades_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_sorted = df.sort_values('timestamp')
    
    # Utiliser pnl_net (le vrai P&L après fees)
    if 'pnl_net' in df.columns:
        total_pnl = df['pnl_net'].sum()
        profitable = len(df[df['pnl_net'] > 0])
        losing = len(df[df['pnl_net'] < 0])
        breakeven = len(df[df['pnl_net'] == 0])
        win_rate = (profitable / len(df)) * 100 if len(df) > 0 else 0
        
        print(f"💰 P&L NET TOTAL: {total_pnl:+.4f} USDC")
        print(f"✅ Trades gagnants: {profitable}")
        print(f"❌ Trades perdants: {losing}")
        print(f"➖ Trades breakeven: {breakeven}")
        print(f"🎯 Taux de réussite: {win_rate:.1f}%")
        print(f"📈 P&L moyen: {df['pnl_net'].mean():+.4f} USDC")
        print(f"🚀 Meilleur trade: {df['pnl_net'].max():+.4f} USDC")
        print(f"💥 Pire trade: {df['pnl_net'].min():+.4f} USDC")
        
        # Évolution du capital
        if 'capital_after' in df.columns:
            capital_initial = df_sorted['capital_before'].iloc[0]
            capital_final = df_sorted['capital_after'].iloc[-1]
            evolution = capital_final - capital_initial
            
            print(f"\n💼 ÉVOLUTION DU CAPITAL:")
            print(f"   🏁 Capital initial: {capital_initial:,.2f} USDC")
            print(f"   🏆 Capital final: {capital_final:,.2f} USDC")
            print(f"   📊 Évolution: {evolution:+.2f} USDC ({(evolution/capital_initial)*100:+.2f}%)")
    
    # Analyse par paire (P&L net)
    if 'pair' in df.columns and 'pnl_net' in df.columns:
        print(f"\n🔄 PERFORMANCE PAR PAIRE (P&L NET):")
        pair_stats = df.groupby('pair').agg({
            'pnl_net': ['count', 'sum', 'mean'],
            'capital_after': 'last'
        }).round(4)
        
        for pair in pair_stats.index:
            count = pair_stats.loc[pair, ('pnl_net', 'count')]
            total_pnl = pair_stats.loc[pair, ('pnl_net', 'sum')]
            avg_pnl = pair_stats.loc[pair, ('pnl_net', 'mean')]
            
            profitable_pair = len(df[(df['pair'] == pair) & (df['pnl_net'] > 0)])
            win_rate_pair = (profitable_pair / count) * 100 if count > 0 else 0
            
            print(f"   {pair}: {count} trades, P&L: {total_pnl:+.4f}, Avg: {avg_pnl:+.4f}, WR: {win_rate_pair:.1f}%")
    
    # Analyse de durée
    if 'duration_seconds' in df.columns:
        print(f"\n⏱️ ANALYSE DE DURÉE:")
        avg_duration = df['duration_seconds'].mean()
        max_duration = df['duration_seconds'].max()
        min_duration = df['duration_seconds'].min()
        
        print(f"   📊 Durée moyenne: {avg_duration/60:.1f} minutes")
        print(f"   🔝 Durée max: {max_duration/60:.1f} minutes")
        print(f"   ⚡ Durée min: {min_duration/60:.1f} minutes")
        
        # Corrélation durée/performance
        if 'pnl_net' in df.columns:
            correlation = df['duration_seconds'].corr(df['pnl_net'])
            print(f"   🔗 Corrélation durée/P&L: {correlation:.3f}")
    
    # Analyse temporelle récente
    print(f"\n⏰ ANALYSE TEMPORELLE:")
    now = datetime.now()
    
    # Dernière heure
    last_hour = now - timedelta(hours=1)
    recent_1h = df[df['timestamp'] > last_hour]
    if len(recent_1h) > 0:
        pnl_1h = recent_1h['pnl_net'].sum()
        print(f"   🕐 Dernière heure: {len(recent_1h)} trades, P&L: {pnl_1h:+.4f}")
    
    # Dernières 6 heures
    last_6h = now - timedelta(hours=6)
    recent_6h = df[df['timestamp'] > last_6h]
    if len(recent_6h) > 0:
        pnl_6h = recent_6h['pnl_net'].sum()
        print(f"   🕕 Dernières 6h: {len(recent_6h)} trades, P&L: {pnl_6h:+.4f}")
    
    # Dernières 24 heures
    last_24h = now - timedelta(hours=24)
    recent_24h = df[df['timestamp'] > last_24h]
    if len(recent_24h) > 0:
        pnl_24h = recent_24h['pnl_net'].sum()
        print(f"   📅 Dernières 24h: {len(recent_24h)} trades, P&L: {pnl_24h:+.4f}")
    
    return df

def create_performance_charts(df):
    """Crée des graphiques de performance"""
    if df is None or len(df) == 0:
        return
    
    print(f"\n📊 GÉNÉRATION DES GRAPHIQUES")
    
    # P&L cumulé
    df_sorted = df.sort_values('timestamp')
    df_sorted['pnl_cumule'] = df_sorted['pnl_net'].cumsum()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sorted['timestamp'], 
        y=df_sorted['pnl_cumule'],
        mode='lines+markers',
        name='P&L Cumulé',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title="📈 Évolution P&L Cumulé (30 derniers trades)",
        xaxis_title="Temps",
        yaxis_title="P&L Cumulé (USDC)",
        hovermode='x unified'
    )
    
    fig.write_html("pnl_cumule.html")
    print("💾 Graphique P&L sauvegardé: pnl_cumule.html")
    
    # Performance par paire
    if 'pair' in df.columns:
        pair_perf = df.groupby('pair')['pnl_net'].sum().sort_values(ascending=False)
        
        fig_pair = go.Figure(data=[
            go.Bar(x=pair_perf.index, y=pair_perf.values, 
                   marker_color=['green' if x > 0 else 'red' for x in pair_perf.values])
        ])
        
        fig_pair.update_layout(
            title="💰 Performance par Paire (P&L Net)",
            xaxis_title="Paire",
            yaxis_title="P&L Net (USDC)"
        )
        
        fig_pair.write_html("performance_par_paire.html")
        print("💾 Graphique par paire sauvegardé: performance_par_paire.html")

def main():
    """Fonction principale d'analyse"""
    print("🚀 ANALYSE PERFORMANCE FIREBASE CORRIGÉE")
    print("=" * 60)
    
    # Initialisation
    db = init_firebase()
    
    # Récupération des trades
    trades_data = get_trades_data(db, 30)
    
    # Analyse corrigée
    df = analyze_real_performance(trades_data)
    
    # Graphiques
    if df is not None:
        create_performance_charts(df)
        
        # Sauvegarde
        df.to_csv('trades_performance_analysis.csv', index=False)
        print("\n💾 Données sauvegardées: trades_performance_analysis.csv")
    
    print("\n🎉 Analyse terminée!")
    return df

if __name__ == "__main__":
    df_result = main()

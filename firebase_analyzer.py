#!/usr/bin/env python3
"""
Analyseur de performances Firebase en temps réel
Analyse les 30 derniers trades et métriques de performance
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
        # Vérifier si déjà initialisé
        firebase_admin.get_app()
        print("✅ Firebase déjà initialisé")
    except ValueError:
        # Initialiser Firebase
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

def get_metrics_data(db, limit=100):
    """Récupère les dernières métriques depuis Firebase"""
    print(f"📈 Récupération des {limit} dernières métriques...")
    
    metrics_ref = db.collection('metrics')
    docs = metrics_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
    
    metrics = []
    for doc in docs:
        metric_data = doc.to_dict()
        metric_data['id'] = doc.id
        metrics.append(metric_data)
    
    print(f"✅ {len(metrics)} métriques récupérées")
    return metrics

def analyze_trades_performance(trades_data):
    """Analyse des performances des trades"""
    print("\n🔍 ANALYSE DES PERFORMANCES TRADES")
    print("=" * 50)
    
    if not trades_data:
        print("❌ Aucun trade trouvé")
        return None
    
    df = pd.DataFrame(trades_data)
    
    # Affichage des colonnes disponibles
    print("📋 Colonnes disponibles dans les trades:")
    for col in sorted(df.columns):
        print(f"   - {col}")
    
    # Analyse des P&L si disponible
    pnl_cols = [col for col in df.columns if 'pnl' in col.lower() or 'profit' in col.lower()]
    
    if pnl_cols:
        print(f"\n💰 Colonnes P&L trouvées: {pnl_cols}")
        
        for pnl_col in pnl_cols:
            if df[pnl_col].dtype in ['float64', 'int64']:
                total_pnl = df[pnl_col].sum()
                profitable = len(df[df[pnl_col] > 0])
                win_rate = (profitable / len(df)) * 100 if len(df) > 0 else 0
                
                print(f"\n📊 Statistiques {pnl_col}:")
                print(f"   💰 P&L Total: {total_pnl:+.4f} USDC")
                print(f"   ✅ Trades gagnants: {profitable}/{len(df)} ({win_rate:.1f}%)")
                print(f"   📈 P&L moyen: {df[pnl_col].mean():+.4f} USDC")
                print(f"   🎯 Meilleur trade: {df[pnl_col].max():+.4f} USDC")
                print(f"   ⚠️ Pire trade: {df[pnl_col].min():+.4f} USDC")
    
    # Analyse par paire
    if 'pair' in df.columns:
        print("\n🔄 Répartition par paire:")
        pair_stats = df['pair'].value_counts()
        for pair, count in pair_stats.head(10).items():
            pnl_pair = df[df['pair'] == pair][pnl_cols[0]].sum() if pnl_cols else 0
            print(f"   {pair}: {count} trades, P&L: {pnl_pair:+.4f}")
    
    # Analyse temporelle
    if 'timestamp' in df.columns:
        print("\n⏰ Analyse temporelle:")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_sorted = df.sort_values('timestamp')
        
        duration_total = (df_sorted['timestamp'].max() - df_sorted['timestamp'].min()).total_seconds() / 3600
        print(f"   📅 Période: {duration_total:.1f} heures")
        print(f"   ⚡ Fréquence: {len(df) / duration_total:.1f} trades/heure")
        
        # Dernières 24h
        last_24h = datetime.now() - timedelta(hours=24)
        recent_trades = df[df['timestamp'] > last_24h]
        if len(recent_trades) > 0:
            recent_pnl = recent_trades[pnl_cols[0]].sum() if pnl_cols else 0
            print(f"   📊 Dernières 24h: {len(recent_trades)} trades, P&L: {recent_pnl:+.4f}")
    
    return df

def analyze_metrics_performance(metrics_data):
    """Analyse des métriques de performance"""
    print("\n📈 ANALYSE DES MÉTRIQUES")
    print("=" * 50)
    
    if not metrics_data:
        print("❌ Aucune métrique trouvée")
        return None
    
    df = pd.DataFrame(metrics_data)
    
    # Affichage des colonnes disponibles
    print("📋 Colonnes disponibles dans les métriques:")
    for col in sorted(df.columns):
        sample_value = df[col].iloc[0] if len(df) > 0 else "N/A"
        print(f"   - {col}: {sample_value}")
    
    # Recherche de colonnes de capital
    capital_cols = [col for col in df.columns if 'capital' in col.lower() or 'balance' in col.lower()]
    
    if capital_cols:
        print(f"\n💰 Colonnes de capital trouvées: {capital_cols}")
        
        for col in capital_cols:
            if df[col].dtype in ['float64', 'int64']:
                latest_value = df[col].iloc[0] if len(df) > 0 else 0
                print(f"   {col}: {latest_value:,.2f}")
    
    # Analyse USDC spécifique
    usdc_cols = [col for col in df.columns if 'usdc' in col.lower()]
    if usdc_cols:
        print(f"\n💵 Colonnes USDC: {usdc_cols}")
        
        for col in usdc_cols:
            if df[col].dtype in ['float64', 'int64']:
                latest_value = df[col].iloc[0] if len(df) > 0 else 0
                print(f"   {col}: {latest_value:,.2f} USDC")
    
    return df

def generate_performance_report():
    """Génère un rapport complet de performance"""
    print("🚀 ANALYSE DES PERFORMANCES FIREBASE")
    print("=" * 60)
    
    # Initialisation Firebase
    db = init_firebase()
    
    # Récupération des données
    trades_data = get_trades_data(db, 30)
    metrics_data = get_metrics_data(db, 50)
    
    # Analyses
    trades_df = analyze_trades_performance(trades_data)
    metrics_df = analyze_metrics_performance(metrics_data)
    
    # Résumé exécutif
    print("\n🎯 RÉSUMÉ EXÉCUTIF")
    print("=" * 30)
    
    if trades_df is not None and len(trades_df) > 0:
        pnl_cols = [col for col in trades_df.columns if 'pnl' in col.lower()]
        if pnl_cols:
            total_pnl = trades_df[pnl_cols[0]].sum()
            profitable = len(trades_df[trades_df[pnl_cols[0]] > 0])
            win_rate = (profitable / len(trades_df)) * 100
            
            print(f"📊 {len(trades_df)} trades analysés")
            print(f"💰 P&L Total: {total_pnl:+.4f} USDC")
            print(f"🎯 Taux de réussite: {win_rate:.1f}%")
            
            if total_pnl > 0:
                print("✅ Performance POSITIVE")
            else:
                print("⚠️ Performance NÉGATIVE")
    
    if metrics_df is not None and len(metrics_df) > 0:
        capital_cols = [col for col in metrics_df.columns if 'capital' in col.lower() or 'balance' in col.lower()]
        if capital_cols:
            current_capital = metrics_df[capital_cols[0]].iloc[0]
            print(f"💰 Capital actuel: {current_capital:,.2f}")
    
    return trades_df, metrics_df

if __name__ == "__main__":
    # Génération du rapport
    trades_df, metrics_df = generate_performance_report()
    
    # Sauvegarde optionnelle
    if trades_df is not None:
        trades_df.to_csv('trades_analysis.csv', index=False)
        print(f"\n💾 Trades sauvegardés dans 'trades_analysis.csv'")
    
    if metrics_df is not None:
        metrics_df.to_csv('metrics_analysis.csv', index=False)
        print(f"💾 Métriques sauvegardées dans 'metrics_analysis.csv'")
    
    print("\n🎉 Analyse terminée!")

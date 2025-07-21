#!/usr/bin/env python3
"""
Analyseur de logs Firebase pour diagnostiquer les problèmes de performance
Identifie les causes des trades perdants
"""

from collections import Counter
from datetime import datetime, timedelta

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore


def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate('firebase_credentials.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_recent_logs(db, limit=200):
    """Récupère les logs récents"""
    print("📋 Récupération des logs récents...")
    
    logs_ref = db.collection('bot_logs')
    docs = logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream() # type: ignore
    
    logs = []
    for doc in docs:
        log_data = doc.to_dict()
        log_data['id'] = doc.id
        logs.append(log_data)
    
    print(f"✅ {len(logs)} logs récupérés")
    return logs

def analyze_exit_reasons(trades_data):
    """Analyse les raisons de sortie des trades"""
    print("\n🔍 ANALYSE DES RAISONS DE SORTIE")
    print("=" * 50)
    
    if not trades_data:
        return
    
    df = pd.DataFrame(trades_data)
    
    if 'exit_reason' in df.columns:
        exit_reasons = df['exit_reason'].value_counts()
        print("📊 Répartition des raisons de sortie:")
        for reason, count in exit_reasons.items():
            percentage = (count / len(df)) * 100
            print(f"   {reason}: {count} trades ({percentage:.1f}%)")
        
        # Analyse par raison de sortie
        df['real_pnl'] = df['capital_after'] - df['capital_before']
        df_pnl = df[df['real_pnl'] != 0]
        
        if len(df_pnl) > 0:
            print(f"\n💰 P&L par raison de sortie:")
            pnl_by_reason = df_pnl.groupby('exit_reason')['real_pnl'].agg(['count', 'sum', 'mean']).round(4)
            for reason in pnl_by_reason.index:
                count = pnl_by_reason.loc[reason, 'count']
                total = pnl_by_reason.loc[reason, 'sum']
                avg = pnl_by_reason.loc[reason, 'mean']
                print(f"   {reason}: {count} trades, Total: {total:+.4f}, Avg: {avg:+.4f}")

def analyze_signal_quality(logs_data):
    """Analyse la qualité des signaux d'entrée"""
    print("\n🎯 ANALYSE DE LA QUALITÉ DES SIGNAUX")
    print("=" * 50)
    
    df_logs = pd.DataFrame(logs_data)
    
    # Filtrer les logs de signaux
    signal_logs = df_logs[df_logs['message'].str.contains('signal|Signal', case=False, na=False)]
    insufficient_logs = df_logs[df_logs['message'].str.contains('insuffisant|insufficient', case=False, na=False)]
    
    print(f"📈 Logs de signaux trouvés: {len(signal_logs)}")
    print(f"⚠️ Signaux insuffisants: {len(insufficient_logs)}")
    
    if len(insufficient_logs) > 0:
        print(f"\n🔍 Derniers signaux insuffisants:")
        for _, log in insufficient_logs.head(5).iterrows():
            timestamp = pd.to_datetime(log['timestamp']).strftime('%H:%M:%S')
            message = log['message'][:100] + "..." if len(log['message']) > 100 else log['message']
            print(f"   [{timestamp}] {message}")

def analyze_momentum_exits(logs_data, trades_data):
    """Analyse les sorties momentum"""
    print("\n⚡ ANALYSE DES SORTIES MOMENTUM")
    print("=" * 50)
    
    df_logs = pd.DataFrame(logs_data)
    df_trades = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()
    
    # Logs de momentum
    momentum_logs = df_logs[df_logs['message'].str.contains('momentum|Momentum', case=False, na=False)]
    print(f"📊 Logs momentum trouvés: {len(momentum_logs)}")
    
    if len(momentum_logs) > 0:
        print(f"\n🔍 Derniers logs momentum:")
        for _, log in momentum_logs.head(10).iterrows():
            timestamp = pd.to_datetime(log['timestamp']).strftime('%H:%M:%S')
            message = log['message']
            print(f"   [{timestamp}] {message}")
    
    # Trades sortis par momentum
    if len(df_trades) > 0 and 'exit_reason' in df_trades.columns:
        momentum_trades = df_trades[df_trades['exit_reason'].str.contains('momentum|Momentum', case=False, na=False)]
        if len(momentum_trades) > 0:
            momentum_trades['real_pnl'] = momentum_trades['capital_after'] - momentum_trades['capital_before']
            momentum_pnl = momentum_trades[momentum_trades['real_pnl'] != 0]
            
            if len(momentum_pnl) > 0:
                avg_duration = momentum_trades['duration_seconds'].mean() / 60
                total_pnl = momentum_pnl['real_pnl'].sum()
                print(f"\n💰 Statistiques sorties momentum:")
                print(f"   📊 Nombre: {len(momentum_trades)} trades")
                print(f"   ⏱️ Durée moyenne: {avg_duration:.1f} minutes")
                print(f"   💰 P&L total: {total_pnl:+.4f} USDC")

def analyze_stop_loss_issues(logs_data, trades_data):
    """Analyse les problèmes de stop loss"""
    print("\n🛑 ANALYSE DES STOP LOSS")
    print("=" * 50)
    
    df_logs = pd.DataFrame(logs_data)
    df_trades = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()
    
    # Logs de stop loss
    sl_logs = df_logs[df_logs['message'].str.contains('stop.loss|stop_loss|SL', case=False, na=False)]
    print(f"📊 Logs stop loss trouvés: {len(sl_logs)}")
    
    if len(sl_logs) > 0:
        print(f"\n🔍 Derniers logs stop loss:")
        for _, log in sl_logs.head(5).iterrows():
            timestamp = pd.to_datetime(log['timestamp']).strftime('%H:%M:%S')
            message = log['message']
            print(f"   [{timestamp}] {message}")
    
    # Trades fermés par stop loss
    if len(df_trades) > 0 and 'exit_reason' in df_trades.columns:
        sl_trades = df_trades[df_trades['exit_reason'].str.contains('stop|SL', case=False, na=False)]
        if len(sl_trades) > 0:
            sl_trades['real_pnl'] = sl_trades['capital_after'] - sl_trades['capital_before']
            sl_pnl = sl_trades[sl_trades['real_pnl'] != 0]
            
            if len(sl_pnl) > 0:
                total_pnl = sl_pnl['real_pnl'].sum()
                avg_duration = sl_trades['duration_seconds'].mean() / 60
                print(f"\n💰 Impact des stop loss:")
                print(f"   📊 Nombre: {len(sl_trades)} trades")
                print(f"   ⏱️ Durée moyenne: {avg_duration:.1f} minutes")
                print(f"   💰 P&L total: {total_pnl:+.4f} USDC")

def analyze_entry_conditions(logs_data):
    """Analyse les conditions d'entrée"""
    print("\n🎯 ANALYSE DES CONDITIONS D'ENTRÉE")
    print("=" * 50)
    
    df_logs = pd.DataFrame(logs_data)
    
    # Logs d'analyse technique
    technical_logs = df_logs[df_logs['message'].str.contains('RSI|MACD|EMA|signal', case=False, na=False)]
    print(f"📈 Logs d'analyse technique: {len(technical_logs)}")
    
    # Logs d'ouverture de trades
    open_logs = df_logs[df_logs['message'].str.contains('ouverture|opening|BUY|ordre', case=False, na=False)]
    print(f"📊 Logs d'ouverture: {len(open_logs)}")
    
    if len(open_logs) > 0:
        print(f"\n🔍 Dernières ouvertures:")
        for _, log in open_logs.head(5).iterrows():
            timestamp = pd.to_datetime(log['timestamp']).strftime('%H:%M:%S')
            message = log['message'][:150] + "..." if len(log['message']) > 150 else log['message']
            print(f"   [{timestamp}] {message}")

def main():
    print("🔍 DIAGNOSTIC AVANCÉ DES PERFORMANCES")
    print("=" * 60)
    
    # Init Firebase
    db = init_firebase()
    
    # Récupération des données
    from firebase_final_analysis import get_trades_data
    trades_data = get_trades_data(db, 30)
    logs_data = get_recent_logs(db, 500)
    
    # Analyses spécialisées
    analyze_exit_reasons(trades_data)
    analyze_signal_quality(logs_data)
    analyze_momentum_exits(logs_data, trades_data)
    analyze_stop_loss_issues(logs_data, trades_data)
    analyze_entry_conditions(logs_data)
    
    # RECOMMANDATIONS
    print(f"\n🎯 RECOMMANDATIONS URGENTES")
    print("=" * 40)
    
    if trades_data:
        df = pd.DataFrame(trades_data)
        df['real_pnl'] = df['capital_after'] - df['capital_before']
        df_pnl = df[df['real_pnl'] != 0]
        
        if len(df_pnl) > 0:
            win_rate = (len(df_pnl[df_pnl['real_pnl'] > 0]) / len(df_pnl)) * 100
            
            if win_rate == 0:
                print("🚨 CRITIQUE: 0% taux de réussite")
                print("   1. Arrêter le bot IMMÉDIATEMENT")
                print("   2. Vérifier les seuils d'entrée (RSI, MACD)")
                print("   3. Ajuster les conditions momentum")
                print("   4. Revoir la configuration stop loss")
            elif win_rate < 30:
                print("⚠️ URGENT: Taux de réussite très faible")
                print("   1. Réduire la fréquence de trading")
                print("   2. Augmenter MIN_SIGNAL_CONDITIONS")
                print("   3. Ajuster MOMENTUM_RSI_THRESHOLD")
    
    print("\n🎉 Diagnostic terminé!")

if __name__ == "__main__":
    main()

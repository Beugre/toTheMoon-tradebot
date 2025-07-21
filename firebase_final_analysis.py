#!/usr/bin/env python3
"""
Analyse FINALE - Calcul des vrais P&L à partir de capital_before/after
"""

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

def get_trades_data(db, limit=30):
    trades_ref = db.collection('trades')
    docs = trades_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
    
    trades = []
    for doc in docs:
        trade_data = doc.to_dict()
        trade_data['id'] = doc.id
        trades.append(trade_data)
    
    return trades

def calculate_real_pnl(trades_data):
    """Calcule les vrais P&L à partir des changements de capital"""
    print("🎯 CALCUL DES VRAIS P&L (capital_after - capital_before)")
    print("=" * 70)
    
    if not trades_data:
        return None
    
    df = pd.DataFrame(trades_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Calcul du vrai P&L
    df['real_pnl'] = df['capital_after'] - df['capital_before']
    
    # Filtrer les P&L non nuls
    df_nonzero = df[df['real_pnl'] != 0].copy()
    
    if len(df_nonzero) == 0:
        print("❌ Aucun trade avec P&L non nul trouvé")
        return df
    
    print(f"📊 {len(df_nonzero)} trades avec P&L réel sur {len(df)} total")
    
    # Statistiques générales
    total_pnl = df_nonzero['real_pnl'].sum()
    profitable = len(df_nonzero[df_nonzero['real_pnl'] > 0])
    losing = len(df_nonzero[df_nonzero['real_pnl'] < 0])
    win_rate = (profitable / len(df_nonzero)) * 100 if len(df_nonzero) > 0 else 0
    
    print(f"💰 P&L TOTAL RÉEL: {total_pnl:+.4f} USDC")
    print(f"✅ Trades gagnants: {profitable}")
    print(f"❌ Trades perdants: {losing}")
    print(f"🎯 Taux de réussite: {win_rate:.1f}%")
    print(f"📈 P&L moyen: {df_nonzero['real_pnl'].mean():+.4f} USDC")
    print(f"🚀 Meilleur trade: {df_nonzero['real_pnl'].max():+.4f} USDC")
    print(f"💥 Pire trade: {df_nonzero['real_pnl'].min():+.4f} USDC")
    
    # Capital evolution
    capital_start = df['capital_before'].iloc[0]
    capital_end = df['capital_after'].iloc[-1]
    evolution = capital_end - capital_start
    evolution_pct = (evolution / capital_start) * 100 if capital_start > 0 else 0
    
    print(f"\n💼 ÉVOLUTION DU CAPITAL:")
    print(f"   🏁 Capital initial: {capital_start:,.2f} USDC")
    print(f"   🏆 Capital final: {capital_end:,.2f} USDC")
    print(f"   📊 Évolution: {evolution:+.2f} USDC ({evolution_pct:+.2f}%)")
    
    # Performance par paire (seulement trades avec P&L)
    print(f"\n🔄 PERFORMANCE PAR PAIRE (P&L RÉEL):")
    pair_stats = df_nonzero.groupby('pair').agg({
        'real_pnl': ['count', 'sum', 'mean'],
        'duration_seconds': 'mean'
    }).round(4)
    
    for pair in pair_stats.index:
        count = pair_stats.loc[pair, ('real_pnl', 'count')]
        total_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'sum')]
        avg_pnl_pair = pair_stats.loc[pair, ('real_pnl', 'mean')]
        avg_duration = pair_stats.loc[pair, ('duration_seconds', 'mean')] / 60
        
        profitable_pair = len(df_nonzero[(df_nonzero['pair'] == pair) & (df_nonzero['real_pnl'] > 0)])
        win_rate_pair = (profitable_pair / count) * 100 if count > 0 else 0
        
        print(f"   {pair:10}: {count:2} trades, P&L: {total_pnl_pair:+8.4f}, Avg: {avg_pnl_pair:+7.4f}, WR: {win_rate_pair:5.1f}%, Durée: {avg_duration:4.1f}min")
    
    # Top trades
    print(f"\n🏆 TOP 5 MEILLEURS TRADES:")
    top_trades = df_nonzero.nlargest(5, 'real_pnl')[['pair', 'real_pnl', 'duration_seconds', 'timestamp']]
    for idx, trade in top_trades.iterrows():
        duration_min = trade['duration_seconds'] / 60
        print(f"   {trade['pair']:10}: {trade['real_pnl']:+8.4f} USDC en {duration_min:4.1f}min - {trade['timestamp'].strftime('%H:%M')}")
    
    print(f"\n💥 TOP 5 PIRES TRADES:")
    worst_trades = df_nonzero.nsmallest(5, 'real_pnl')[['pair', 'real_pnl', 'duration_seconds', 'timestamp']]
    for idx, trade in worst_trades.iterrows():
        duration_min = trade['duration_seconds'] / 60
        print(f"   {trade['pair']:10}: {trade['real_pnl']:+8.4f} USDC en {duration_min:4.1f}min - {trade['timestamp'].strftime('%H:%M')}")
    
    # Analyse temporelle
    now = datetime.now()
    print(f"\n⏰ PERFORMANCE TEMPORELLE:")
    
    for hours, label in [(1, "Dernière heure"), (6, "Dernières 6h"), (24, "Dernières 24h")]:
        cutoff = now - timedelta(hours=hours)
        recent = df_nonzero[df_nonzero['timestamp'] > cutoff]
        if len(recent) > 0:
            pnl_recent = recent['real_pnl'].sum()
            trades_recent = len(recent)
            print(f"   {label:15}: {trades_recent:2} trades, P&L: {pnl_recent:+8.4f} USDC")
    
    return df

def main():
    print("🔥 ANALYSE FINALE DES PERFORMANCES - P&L RÉELS")
    print("=" * 70)
    
    # Init Firebase
    db = init_firebase()
    
    # Get data
    trades_data = get_trades_data(db, 30)
    
    # Analyze
    df = calculate_real_pnl(trades_data)
    
    if df is not None:
        # Sauvegarde avec P&L réels
        df.to_csv('trades_real_pnl_analysis.csv', index=False)
        print(f"\n💾 Analyse sauvegardée: trades_real_pnl_analysis.csv")
        
        # Résumé final
        df_nonzero = df[df['real_pnl'] != 0]
        if len(df_nonzero) > 0:
            total = df_nonzero['real_pnl'].sum()
            win_rate = (len(df_nonzero[df_nonzero['real_pnl'] > 0]) / len(df_nonzero)) * 100
            
            print(f"\n🎯 RÉSUMÉ FINAL:")
            print(f"   💰 P&L Total: {total:+.4f} USDC")
            print(f"   🎯 Taux de réussite: {win_rate:.1f}%")
            print(f"   📊 Capital: 22,735.17 USDC")
            
            if total > 0:
                print(f"   ✅ PERFORMANCE POSITIVE!")
            else:
                print(f"   ⚠️ Performance négative")
    
    print("\n🎉 Analyse terminée!")

if __name__ == "__main__":
    main()

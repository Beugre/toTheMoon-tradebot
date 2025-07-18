#!/usr/bin/env python3
"""
Script de génération de rapports pour investisseurs
"""

import asyncio
import json
import sys
from datetime import datetime

from utils.database import TradingDatabase


async def generate_investor_report(days: int = 30, output_file: str = None):  # type: ignore
    """Génère un rapport pour les investisseurs"""
    
    if output_file is None:
        output_file = f"investor_report_{datetime.now().strftime('%Y%m%d')}.json"
    
    try:
        # Initialisation de la base de données
        db = TradingDatabase()
        await db.initialize_database()
        
        print(f"📊 Génération du rapport investisseurs ({days} derniers jours)...")
        
        # Export des données
        report_file = await db.export_data_for_investors(output_file)
        
        print(f"✅ Rapport généré avec succès: {report_file}")
        
        # Affichage d'un résumé
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n📋 RÉSUMÉ DU RAPPORT:")
        print("=" * 50)
        
        if 'performance_summary' in data:
            perf = data['performance_summary']
            print(f"🔹 Période analysée: {days} jours")
            print(f"🔹 Total trades: {perf.get('total_trades', 0)}")
            print(f"🔹 Win rate: {perf.get('win_rate', 0):.1f}%")
            print(f"🔹 PnL total: {perf.get('total_pnl', 0):.2f} EUR")
            print(f"🔹 Meilleur trade: {perf.get('best_trade', 0):.2f} EUR")
            print(f"🔹 Pire trade: {perf.get('worst_trade', 0):.2f} EUR")
        
        if 'advanced_metrics' in data:
            metrics = data['advanced_metrics']
            print(f"🔹 Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"🔹 Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            print(f"🔹 Jours de trading: {metrics.get('total_trading_days', 0)}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        sys.exit(1)

async def show_performance_summary():
    """Affiche un résumé rapide des performances"""
    try:
        db = TradingDatabase()
        await db.initialize_database()
        
        print("📊 RÉSUMÉ DES PERFORMANCES")
        print("=" * 40)
        
        # Performances 7 derniers jours
        perf_7d = await db.get_performance_summary(7)
        summary_7d = perf_7d['summary']
        total_trades_7d = summary_7d['total_trades'] or 0
        winning_trades_7d = summary_7d['winning_trades'] or 0
        total_pnl_7d = summary_7d['total_pnl'] or 0
        print(f"\n🔹 7 derniers jours:")
        print(f"   Trades: {total_trades_7d}")
        win_rate_7d = (winning_trades_7d / max(total_trades_7d, 1)) * 100 if total_trades_7d > 0 else 0
        print(f"   Win rate: {win_rate_7d:.1f}%")
        print(f"   PnL: {total_pnl_7d:.2f} EUR")
        
        # Performances 30 derniers jours
        perf_30d = await db.get_performance_summary(30)
        summary_30d = perf_30d['summary']
        total_trades_30d = summary_30d['total_trades'] or 0
        winning_trades_30d = summary_30d['winning_trades'] or 0
        total_pnl_30d = summary_30d['total_pnl'] or 0
        print(f"\n🔹 30 derniers jours:")
        print(f"   Trades: {total_trades_30d}")
        win_rate_30d = (winning_trades_30d / max(total_trades_30d, 1)) * 100 if total_trades_30d > 0 else 0
        print(f"   Win rate: {win_rate_30d:.1f}%")
        print(f"   PnL: {total_pnl_30d:.2f} EUR")
        
        # Historique des trades récents
        trades = await db.get_trades_history(10)
        print(f"\n🔹 10 derniers trades:")
        for trade in trades[:5]:
            status_emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"   {status_emoji} {trade['symbol']}: {trade['pnl']:+.2f} EUR ({trade['pnl_percent']:+.1f}%)")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python investor_report.py summary          # Résumé rapide")
        print("  python investor_report.py report [days]    # Rapport complet")
        print("  python investor_report.py report 30 custom_report.json")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "summary":
        asyncio.run(show_performance_summary())
    
    elif command == "report":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        asyncio.run(generate_investor_report(days, output_file))  # type: ignore
    
    else:
        print("❌ Commande inconnue. Utilisez 'summary' ou 'report'")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script d'urgence : Vérification désynchronisation Binance vs DB
Analyse les positions fantômes dans la base de données
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta


def analyze_ghost_positions():
    """Analyse les positions fantômes dans la DB"""
    db_path = "data/trading_bot.db"
    
    print("🔍 ANALYSE DES POSITIONS FANTÔMES")
    print("=" * 50)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Positions marquées comme ouvertes dans la DB
            cursor.execute("""
                SELECT 
                    symbol, 
                    side, 
                    entry_price, 
                    quantity, 
                    capital_engaged, 
                    entry_time,
                    stop_loss,
                    take_profit
                FROM trades 
                WHERE status = 'OPEN' 
                ORDER BY entry_time DESC
            """)
            
            positions = cursor.fetchall()
            
            print(f"📊 Positions dans la DB : {len(positions)}")
            print(f"📊 Positions sur Binance : 0 (selon vous)")
            print(f"⚠️  DÉSYNCHRONISATION : {len(positions)} positions fantômes !")
            
            if positions:
                print("\n🔍 DÉTAIL DES POSITIONS FANTÔMES :")
                print("-" * 80)
                
                total_phantom = 0
                by_symbol = {}
                
                for pos in positions:
                    symbol, side, entry_price, qty, capital, entry_time, sl, tp = pos
                    
                    if symbol not in by_symbol:
                        by_symbol[symbol] = {'count': 0, 'capital': 0}
                    
                    by_symbol[symbol]['count'] += 1
                    by_symbol[symbol]['capital'] += capital
                    total_phantom += capital
                    
                    # Calcul durée depuis ouverture
                    entry_dt = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')
                    duration = datetime.now() - entry_dt
                    
                    print(f"{symbol:8} {side:4} | {entry_price:>10.4f} x {qty:>8.4f} = {capital:>8.2f}€ | {entry_time} ({duration.days}j {duration.seconds//3600}h)")
                
                print("-" * 80)
                print(f"💰 TOTAL CAPITAL FANTÔME : {total_phantom:,.2f}€")
                
                print("\n📈 RÉSUMÉ PAR SYMBOLE :")
                for symbol, data in sorted(by_symbol.items(), key=lambda x: x[1]['capital'], reverse=True):
                    print(f"  {symbol:8} : {data['count']:2d} positions = {data['capital']:>8.2f}€")
                
                # Analyse temporelle
                print("\n⏰ ANALYSE TEMPORELLE :")
                recent_24h = sum(1 for pos in positions if (datetime.now() - datetime.strptime(pos[5], '%Y-%m-%d %H:%M:%S.%f')).days == 0)
                recent_48h = sum(1 for pos in positions if (datetime.now() - datetime.strptime(pos[5], '%Y-%m-%d %H:%M:%S.%f')).days <= 1)
                
                print(f"  Dernières 24h : {recent_24h} positions")
                print(f"  Dernières 48h : {recent_48h} positions")
                print(f"  Plus anciennes : {len(positions) - recent_48h} positions")
                
                # Recommandations
                print(f"\n🚨 ACTIONS NÉCESSAIRES :")
                print(f"  1. Mettre à jour le statut des positions fermées dans la DB")
                print(f"  2. Resynchroniser avec l'API Binance")
                print(f"  3. Nettoyer les {len(positions)} positions fantômes")
                print(f"  4. Vérifier pourquoi le bot n'a pas détecté les fermetures")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse : {e}")

def generate_cleanup_script():
    """Génère un script de nettoyage"""
    print(f"\n📝 SCRIPT DE NETTOYAGE SUGGÉRÉ :")
    print("=" * 50)
    print("""
# Option 1: Marquer toutes les positions comme fermées avec PnL=0
UPDATE trades SET status='CLOSED', exit_reason='MANUAL_SYNC', exit_time=datetime('now') WHERE status='OPEN';

# Option 2: Supprimer complètement les positions fantômes (ATTENTION!)
DELETE FROM trades WHERE status='OPEN';

# Option 3: Marquer avec un statut spécial pour investigation
UPDATE trades SET status='PHANTOM', exit_reason='DESYNC_BINANCE' WHERE status='OPEN';
    """)

if __name__ == "__main__":
    analyze_ghost_positions()
    generate_cleanup_script()

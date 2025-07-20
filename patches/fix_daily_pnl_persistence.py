#!/usr/bin/env python3
"""
Patch urgent : Persistance du P&L journalier
Corrige le reset du stop loss quotidien au redémarrage
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import sqlite3
from datetime import date, datetime


class DailyPnLPersistence:
    def __init__(self, db_path="trading_data.db"):
        self.db_path = db_path
    
    def get_today_pnl(self):
        """Récupère le P&L cumulé d'aujourd'hui depuis la DB"""
        try:
            today = date.today().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Somme des P&L de tous les trades d'aujourd'hui
                cursor.execute("""
                    SELECT COALESCE(SUM(pnl_amount), 0) 
                    FROM trades 
                    WHERE DATE(close_time) = ?
                    AND status = 'closed'
                """, (today,))
                
                daily_pnl = cursor.fetchone()[0]
                
                # Compte le nombre de trades
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM trades 
                    WHERE DATE(close_time) = ?
                    AND status = 'closed'
                """, (today,))
                
                daily_trades = cursor.fetchone()[0]
                
                return daily_pnl, daily_trades
                
        except Exception as e:
            logging.error(f"Erreur récupération P&L journalier: {e}")
            return 0.0, 0
    
    def check_if_stop_loss_hit_today(self, daily_pnl, total_capital, stop_loss_percent=2.0):
        """Vérifie si le stop loss journalier a été atteint"""
        if total_capital == 0:
            return False
            
        daily_pnl_percent = (daily_pnl / total_capital) * 100
        return daily_pnl_percent <= -stop_loss_percent

def test_current_state():
    """Test de l'état actuel"""
    persistence = DailyPnLPersistence()
    daily_pnl, daily_trades = persistence.get_today_pnl()
    
    print(f"📊 P&L journalier actuel : {daily_pnl:+.2f} EUR")
    print(f"📈 Trades aujourd'hui : {daily_trades}")
    
    # Simulation avec capital typique
    test_capital = 19650
    is_stop_hit = persistence.check_if_stop_loss_hit_today(daily_pnl, test_capital)
    
    if daily_pnl != 0:
        pnl_percent = (daily_pnl / test_capital) * 100
        print(f"💎 Performance : {pnl_percent:+.2f}%")
        
        if is_stop_hit:
            print("🛑 STOP LOSS JOURNALIER ATTEINT !")
        else:
            print("✅ Stop loss non atteint")
    else:
        print("💤 Aucun trade aujourd'hui")

if __name__ == "__main__":
    test_current_state()

#!/usr/bin/env python3
"""
Script d'urgence : Nettoyage de la base de données
Ferme toutes les positions "fantômes" qui n'existent plus sur Binance
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import sqlite3
from datetime import date, datetime


class DatabaseCleaner:
    def __init__(self, db_path="data/trading_bot.db"):
        self.db_path = db_path
    
    def backup_database(self):
        """Crée une sauvegarde avant nettoyage"""
        backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Sauvegarde créée: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            return None
    
    def analyze_phantom_positions(self):
        """Analyse les positions ouvertes dans la DB"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Positions ouvertes par symbole
                cursor.execute("""
                    SELECT symbol, COUNT(*), SUM(capital_engaged), 
                           MIN(entry_time), MAX(entry_time)
                    FROM trades 
                    WHERE status = 'OPEN' 
                    GROUP BY symbol
                    ORDER BY SUM(capital_engaged) DESC
                """)
                
                positions = cursor.fetchall()
                
                print("🔍 ANALYSE DES POSITIONS FANTÔMES")
                print("=" * 50)
                
                total_phantom_capital = 0
                total_phantom_count = 0
                
                for symbol, count, capital, min_time, max_time in positions:
                    print(f"{symbol}:")
                    print(f"  📊 {count} positions = {capital:.2f}€")
                    print(f"  📅 Première: {min_time}")
                    print(f"  📅 Dernière: {max_time}")
                    print()
                    
                    total_phantom_capital += capital
                    total_phantom_count += count
                
                print(f"💰 TOTAL FANTÔME: {total_phantom_count} positions = {total_phantom_capital:.2f}€")
                
                return positions
                
        except Exception as e:
            print(f"❌ Erreur analyse: {e}")
            return []
    
    def close_phantom_positions(self, confirm=False):
        """Ferme toutes les positions fantômes"""
        if not confirm:
            print("⚠️  ATTENTION: Cette action fermera TOUTES les positions ouvertes")
            print("   Pour confirmer, utilisez: close_phantom_positions(confirm=True)")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupère toutes les positions ouvertes
                cursor.execute("SELECT id, symbol FROM trades WHERE status = 'OPEN'")
                open_trades = cursor.fetchall()
                
                if not open_trades:
                    print("✅ Aucune position ouverte à fermer")
                    return True
                
                # Ferme toutes les positions avec un PnL de 0 (positions fantômes)
                current_time = datetime.now().isoformat()
                
                cursor.execute("""
                    UPDATE trades 
                    SET status = 'CLOSED', 
                        exit_time = ?,
                        exit_reason = 'PHANTOM_CLEANUP',
                        exit_price = entry_price,
                        pnl_amount = 0,
                        pnl_percent = 0
                    WHERE status = 'OPEN'
                """, (current_time,))
                
                affected_rows = cursor.rowcount
                conn.commit()
                
                print(f"✅ {affected_rows} positions fantômes fermées")
                return True
                
        except Exception as e:
            print(f"❌ Erreur fermeture: {e}")
            return False
    
    def reset_daily_metrics(self):
        """Remet à zéro les métriques journalières"""
        today = date.today().strftime('%Y-%m-%d')
        print(f"🔄 Reset des métriques pour {today}")
        
        # Cette fonction sera appelée au startup du bot pour corriger le problème
        # de reset du daily_pnl
        pass

def main():
    print("🚨 NETTOYAGE D'URGENCE DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    cleaner = DatabaseCleaner()
    
    # 1. Sauvegarde
    backup = cleaner.backup_database()
    if not backup:
        print("❌ Impossible de créer une sauvegarde. Arrêt.")
        return
    
    # 2. Analyse
    positions = cleaner.analyze_phantom_positions()
    
    if not positions:
        print("✅ Aucune position fantôme détectée")
        return
    
    # 3. Proposition de nettoyage
    print("\n🤔 ACTIONS POSSIBLES:")
    print("1. cleaner.close_phantom_positions(confirm=True)  # Fermer toutes les positions")
    print("2. Analyser manuellement chaque position")
    print("3. Vérifier d'abord avec Binance API")
    
    return cleaner

if __name__ == "__main__":
    cleaner = main()

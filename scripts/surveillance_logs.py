#!/usr/bin/env python3
"""
Script de surveillance pour vérifier le logging Google Sheets
"""

import re
import subprocess
import time


def check_google_sheets_logs():
    """Vérifie les logs pour les entrées Google Sheets"""
    try:
        # Récupérer les logs récents
        result = subprocess.run([
            'ssh', 'root@213.199.41.168', 
            'journalctl -u tothemoon-tradebot.service --since "5 minutes ago" --no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logs = result.stdout
            
            # Chercher les entrées de trades et Google Sheets
            trade_lines = [line for line in logs.split('\n') 
                          if any(keyword in line.lower() 
                                for keyword in ['trade', 'position', 'achat', 'vente', 'google', 'sheets'])]
            
            if trade_lines:
                print("📝 Activité récente détectée:")
                for line in trade_lines[-10:]:  # Dernières 10 lignes
                    print(f"  {line}")
            else:
                print("⏳ Aucune activité de trading récente")
                
        else:
            print(f"❌ Erreur lors de la récupération des logs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🔍 Surveillance du logging Google Sheets...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            check_google_sheets_logs()
            print("-" * 50)
            time.sleep(30)  # Vérifier toutes les 30 secondes
    except KeyboardInterrupt:
        print("\n👋 Arrêt de la surveillance")

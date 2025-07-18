#!/usr/bin/env python3
"""
Monitoring avancé pour capital élevé
"""

import subprocess
import time
from datetime import datetime


class CapitalMonitor:
    """Surveillance renforcée pour capital important"""
    
    def __init__(self, capital_threshold=10000):
        self.capital_threshold = capital_threshold
        self.daily_loss_limit = capital_threshold * 0.02  # 2% max perte/jour
        
    def check_daily_performance(self):
        """Vérification performance quotidienne"""
        # Récupération des métriques via SSH
        try:
            result = subprocess.run([
                'ssh', 'root@213.199.41.168',
                'journalctl -u tothemoon-tradebot.service --since "today" --no-pager | grep -E "(P&L|Performance)"'
            ], capture_output=True, text=True)
            
            if "ALERTE" in result.stdout:
                self.send_emergency_alert()
                
        except Exception as e:
            print(f"Erreur monitoring: {e}")
    
    def send_emergency_alert(self):
        """Alerte d'urgence si dépassement seuils"""
        print("🚨 ALERTE: Seuils de risque dépassés!")
        # Ici on pourrait ajouter notification Telegram urgente
    
    def run_monitoring(self):
        """Surveillance continue"""
        print("🔍 Surveillance capital élevé activée...")
        while True:
            self.check_daily_performance()
            time.sleep(300)  # Check toutes les 5 minutes

if __name__ == "__main__":
    monitor = CapitalMonitor(15480)
    monitor.run_monitoring()

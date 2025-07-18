#!/usr/bin/env python3
"""
Script de transition vers capital élevé (+10K€)
"""

import os
import shutil
from datetime import datetime


def create_backup():
    """Sauvegarde complète avant transition"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup config
    shutil.copy("config.py", f"backups/config_before_10k_{timestamp}.py")
    
    # Backup .env si modif nécessaire
    if os.path.exists(".env"):
        shutil.copy(".env", f"backups/env_before_10k_{timestamp}")
    
    print(f"✅ Backup créé: config_before_10k_{timestamp}.py")
    return timestamp

def apply_high_capital_config():
    """Application de la config capital élevé"""
    
    # Copie de la config capital élevé
    shutil.copy("config_high_capital.py", "config.py")
    print("✅ Configuration capital élevé appliquée")
    
def show_transition_summary():
    """Affiche le résumé de la transition"""
    
    print("""
🚀 TRANSITION CAPITAL ÉLEVÉ - RÉSUMÉ

💰 NOUVEAU CAPITAL: 15 480€ (+10 000€)

📊 NOUVEAUX PARAMÈTRES:
- Position: 12% = 1 857€ (vs 822€)
- TP: +0.7% = +13€ par trade (vs +6.58€)
- SL: -0.35% = -6.5€ par trade (vs -3.29€)
- Positions max: 5 (vs 4)
- Scan: 40s (vs 45s)

🎯 OBJECTIFS QUOTIDIENS:
- Conservative: +0.6% = +92.88€
- Réaliste: +0.8% = +123.84€
- Optimiste: +1.0% = +154.80€

🛡️ SÉCURITÉS RENFORCÉES:
- Stop loss quotidien: -2% (-309.60€)
- Spread max réduit: 0.15% (vs 0.2%)
- Monitoring renforcé
- Configuration plus conservative

⚡ MULTIPLICATEUR DE PERFORMANCE:
- Gains quotidiens: x2.83
- Potentiel mensuel: 2 700€ - 3 400€
- Potentiel annuel: 31 000€ - 39 000€

🔥 PRÊT POUR LE TRADING HAUTE PERFORMANCE !
""")

def apply_to_vps():
    """Application sur le VPS"""
    import subprocess
    
    print("🚀 Synchronisation sur le VPS...")
    
    # Upload nouvelle config
    result = subprocess.run([
        "scp", "config.py", "root@213.199.41.168:/opt/toTheMoon_tradebot/"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Configuration synchronisée")
        
        # Restart bot
        restart_result = subprocess.run([
            "ssh", "root@213.199.41.168", 
            "systemctl restart tothemoon-tradebot.service"
        ], capture_output=True, text=True)
        
        if restart_result.returncode == 0:
            print("✅ Bot redémarré avec capital élevé")
            
            # Status check
            status_result = subprocess.run([
                "ssh", "root@213.199.41.168", 
                "systemctl status tothemoon-tradebot.service --no-pager | head -10"
            ], capture_output=True, text=True)
            
            print("📊 Statut du bot:")
            print(status_result.stdout)
        else:
            print("❌ Erreur redémarrage bot")
    else:
        print("❌ Erreur synchronisation")

def main():
    """Fonction principale"""
    print("💰 TRANSITION VERS CAPITAL ÉLEVÉ (+10K€)")
    print("=" * 60)
    
    # Vérification
    response = input("🔥 CONFIRMER la transition vers 15 480€ ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Transition annulée")
        return
    
    # Création des backups
    os.makedirs("backups", exist_ok=True)
    timestamp = create_backup()
    
    # Application config
    apply_high_capital_config()
    
    # Résumé
    show_transition_summary()
    
    # Application VPS
    response_vps = input("🚀 Appliquer sur le VPS maintenant ? (oui/non): ")
    if response_vps.lower() in ['oui', 'o', 'yes', 'y']:
        apply_to_vps()
    else:
        print("💡 Pour appliquer plus tard:")
        print("  scp config.py root@213.199.41.168:/opt/toTheMoon_tradebot/")
        print("  ssh root@213.199.41.168 'systemctl restart tothemoon-tradebot.service'")
    
    print(f"\n🎉 TRANSITION TERMINÉE !")
    print(f"📋 Backup sauvé: config_before_10k_{timestamp}.py")
    print(f"🚀 Bot configuré pour 15 480€ !")

if __name__ == "__main__":
    main()

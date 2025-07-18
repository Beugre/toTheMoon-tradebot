#!/usr/bin/env python3
"""
Script d'optimisation de la configuration pour +1% quotidien

⚠️ IMPORTANT: Ce script ne modifie PAS automatiquement le bot !
Il crée un fichier config_optimized.py que tu peux examiner avant application.

🔧 FONCTIONNEMENT:
1. Sauvegarde la config actuelle
2. Génère une config optimisée 
3. Affiche les prédictions de performance
4. TU DÉCIDES si tu l'appliques ou non

📋 ÉTAPES:
1. python scripts/optimize_config.py  # Génère config_optimized.py
2. Examine le fichier généré
3. Si OK: cp config_optimized.py config.py
4. Redémarre le bot

"""

import os
import shutil
from datetime import datetime


def show_script_info():
    """Affiche les informations sur le script"""
    print("🤖 SCRIPT D'OPTIMISATION CONFIGURATION")
    print("=" * 60)
    print("❌ CE SCRIPT NE MODIFIE PAS LE BOT AUTOMATIQUEMENT")
    print("✅ Il génère une configuration optimisée à examiner")
    print("🔍 TU GARDES LE CONTRÔLE TOTAL")
    print("=" * 60)
    print()

def backup_current_config():
    """Sauvegarde la configuration actuelle"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"config_backup_{timestamp}.py"
    shutil.copy("config.py", f"backups/{backup_file}")
    print(f"✅ Configuration sauvegardée: {backup_file}")

def apply_optimized_config():
    """Applique la configuration optimisée"""
    
    optimizations = {
        "POSITION_SIZE_PERCENT": 15.0,           # Réduction 17.5% → 15%
        "STOP_LOSS_PERCENT": 0.4,               # Réduction 0.5% → 0.4%
        "TAKE_PROFIT_PERCENT": 0.8,             # Réduction 1.0% → 0.8%
        "MIN_PROFIT_BEFORE_TIMEOUT": 0.15,      # Réduction 0.2% → 0.15%
        "MIN_SIGNAL_CONDITIONS": 4,             # Augmentation 3 → 4
        "MAX_OPEN_POSITIONS": 4,                # Augmentation 3 → 4
        "SCAN_INTERVAL": 45,                    # Réduction 60s → 45s
    }
    
    print("🔧 Application des optimisations:")
    for param, value in optimizations.items():
        print(f"   📊 {param}: {value}")
    
    # Lecture du fichier config actuel
    with open("config.py", "r", encoding="utf-8") as f:
        config_content = f.read()
    
    # Application des modifications
    for param, value in optimizations.items():
        # Recherche du pattern et remplacement
        import re
        pattern = f"{param}:\\s*\\w+\\s*=\\s*[0-9.]+[^\\n]*"
        
        if isinstance(value, float):
            replacement = f"{param}: float = {value}"
        else:
            replacement = f"{param}: int = {value}"
        
        config_content = re.sub(pattern, replacement, config_content)
    
    # Sauvegarde du fichier modifié
    with open("config_optimized.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print("✅ Configuration optimisée créée: config_optimized.py")
    print("💡 Pour appliquer: cp config_optimized.py config.py")

def show_performance_prediction():
    """Affiche les prédictions de performance"""
    
    print("\\n📈 PRÉDICTIONS DE PERFORMANCE:")
    print("=" * 50)
    
    # Calculs basés sur les nouvelles métriques
    position_size = 5480 * 0.15  # 15% de 5480€
    tp_gain = position_size * 0.008  # +0.8%
    sl_loss = position_size * 0.004  # -0.4%
    
    print(f"💰 Taille de position: {position_size:.2f}€")
    print(f"📈 Gain par TP: +{tp_gain:.2f}€")
    print(f"📉 Perte par SL: -{sl_loss:.2f}€")
    print(f"🎯 Ratio R/R: 1:2")
    
    print("\\n🎲 SCÉNARIOS QUOTIDIENS:")
    
    scenarios = [
        {"trades": 8, "win_rate": 0.75, "desc": "Journée normale"},
        {"trades": 12, "win_rate": 0.70, "desc": "Journée active"},
        {"trades": 6, "win_rate": 0.80, "desc": "Journée sélective"},
    ]
    
    for scenario in scenarios:
        trades = scenario["trades"]
        wr = scenario["win_rate"]
        wins = int(trades * wr)
        losses = trades - wins
        
        daily_pnl = (wins * tp_gain) - (losses * sl_loss)
        daily_percent = daily_pnl / 5480 * 100
        
        print(f"\\n   📊 {scenario['desc']}:")
        print(f"   🎯 {trades} trades - {wr*100:.0f}% WR")
        print(f"   ✅ {wins} gagnants (+{wins * tp_gain:.2f}€)")
        print(f"   ❌ {losses} perdants (-{losses * sl_loss:.2f}€)")
        print(f"   💰 P&L: {daily_pnl:+.2f}€ ({daily_percent:+.2f}%)")
        
        if daily_percent >= 0.8:
            print(f"   🎉 OBJECTIF ATTEINT !")

def main():
    """Fonction principale"""
    print("🚀 OPTIMISATION DE CONFIGURATION - Bot ToTheMoon")
    print("=" * 60)
    
    # Création du dossier de backup
    os.makedirs("backups", exist_ok=True)
    
    # Sauvegarde et optimisation
    backup_current_config()
    apply_optimized_config()
    show_performance_prediction()
    
    print("\\n" + "=" * 60)
    print("✨ Optimisation terminée !")
    print("\\n📋 PROCHAINES ÉTAPES:")
    print("1. Examiner config_optimized.py")
    print("2. Tester en mode simulation")
    print("3. Appliquer si satisfait")
    print("4. Surveiller les performances")

if __name__ == "__main__":
    show_script_info()
    main()

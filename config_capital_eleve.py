"""
Configuration optimisée pour capital élevé (15 480€)
"""

# Configuration conservative pour capital important
CAPITAL_ELEVE_CONFIG = {
    "POSITION_SIZE_PERCENT": 12.0,      # Plus conservateur (vs 15%)
    "MAX_OPEN_POSITIONS": 5,            # Plus d'opportunités  
    "DAILY_STOP_LOSS_PERCENT": 2.0,    # Stop loss quotidien à 2%
    "TAKE_PROFIT_PERCENT": 0.7,        # TP plus conservateur
    "STOP_LOSS_PERCENT": 0.35,         # SL plus serré
    "MIN_SIGNAL_CONDITIONS": 4,         # Maintenir sélectivité
}

# Calculs avec nouveau capital
CAPITAL = 15480
POSITION_SIZE = CAPITAL * 0.12  # 1857.60€ par position
GAIN_PAR_TP = POSITION_SIZE * 0.007  # +13.00€ par trade
PERTE_PAR_SL = POSITION_SIZE * 0.0035  # -6.50€ par trade

# Performance attendue quotidienne
OBJECTIF_QUOTIDIEN = CAPITAL * 0.008  # +0.8% = +123.84€

print(f"""
💰 CONFIGURATION CAPITAL ÉLEVÉ (15 480€)

📊 Paramètres:
- Position: 12% = {POSITION_SIZE:.2f}€
- TP: +0.7% = +{GAIN_PAR_TP:.2f}€ par trade
- SL: -0.35% = -{PERTE_PAR_SL:.2f}€ par trade
- Ratio R/R: 1:2

🎯 Objectifs:
- Quotidien: +{OBJECTIF_QUOTIDIEN:.2f}€ (+0.8%)
- Mensuel: +{OBJECTIF_QUOTIDIEN * 22:.2f}€
- Annuel: +{OBJECTIF_QUOTIDIEN * 250:.2f}€

🛡️ Sécurité:
- Stop loss quotidien: -2% (-309.60€)
- 5 positions max simultanées
- Monitoring renforcé activé
""")

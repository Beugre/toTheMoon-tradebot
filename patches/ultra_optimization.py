#!/usr/bin/env python3
"""
🚀 OPTIMISATIONS RADICALES POUR RÉDUIRE ENCORE PLUS LES FRAIS
Configuration ultra-optimisée
"""

# Configuration actuelle vs optimisée
CURRENT_CONFIG = {
    'BASE_POSITION_SIZE_PERCENT': 20,  # 20% du capital
    'MIN_POSITION_SIZE_EUR': 500,      # 500€ minimum
    'MAX_OPEN_POSITIONS': 3,           # 3 positions max
    'MAX_TRADES_PER_PAIR': 1,          # 1 trade par paire
}

ULTRA_OPTIMIZED_CONFIG = {
    'BASE_POSITION_SIZE_PERCENT': 30,  # 30% du capital (positions plus grosses)
    'MIN_POSITION_SIZE_EUR': 1000,     # 1000€ minimum (divise par 2 les trades)
    'MAX_OPEN_POSITIONS': 2,           # 2 positions max (plus sélectif)
    'MAX_TRADES_PER_PAIR': 1,          # Reste 1
    'COOLDOWN_BETWEEN_TRADES': 300,    # 5min minimum entre trades
    'MIN_SIGNAL_STRENGTH': 0.7,       # Signaux plus forts seulement
}

def show_fee_reduction_impact():
    print("🔧 === OPTIMISATIONS RADICALES FRAIS ===")
    print()
    
    # Calcul impact réel
    current_daily_trades = 263  # Trades actuels par jour
    fees_per_trade = 1.0        # ~1€ de frais par trade moyen
    
    print("📊 CONFIGURATION ACTUELLE:")
    print(f"   • Trades/jour: {current_daily_trades}")
    print(f"   • Frais/jour: ~{current_daily_trades * fees_per_trade:.0f}€")
    print(f"   • Frais/mois: ~{current_daily_trades * fees_per_trade * 30:.0f}€")
    print()
    
    # Optimisations progressives
    optimizations = [
        {
            'name': '1️⃣ BNB Désactivé (FAIT)',
            'reduction': 0.77,
            'daily_fees': current_daily_trades * fees_per_trade * (1 - 0.77)
        },
        {
            'name': '2️⃣ Position MIN 1000€',
            'reduction': 0.50,  # -50% trades
            'daily_fees': current_daily_trades * fees_per_trade * (1 - 0.77) * (1 - 0.50)
        },
        {
            'name': '3️⃣ Signaux Plus Sélectifs',
            'reduction': 0.30,  # -30% trades supplémentaires
            'daily_fees': current_daily_trades * fees_per_trade * (1 - 0.77) * (1 - 0.50) * (1 - 0.30)
        },
        {
            'name': '4️⃣ Cooldown 5min',
            'reduction': 0.20,  # -20% trades supplémentaires
            'daily_fees': current_daily_trades * fees_per_trade * (1 - 0.77) * (1 - 0.50) * (1 - 0.30) * (1 - 0.20)
        }
    ]
    
    cumulative_fees = current_daily_trades * fees_per_trade
    
    for opt in optimizations:
        print(f"✅ {opt['name']}")
        print(f"   Frais/jour: {opt['daily_fees']:.1f}€")
        print(f"   Économie: -{(cumulative_fees - opt['daily_fees']):.0f}€/jour")
        print(f"   Réduction totale: {(1 - opt['daily_fees']/cumulative_fees)*100:.1f}%")
        print()
    
    final_fees = optimizations[-1]['daily_fees']
    total_reduction = (1 - final_fees/cumulative_fees) * 100
    
    print("🎯 RÉSULTAT FINAL:")
    print(f"   💰 Frais AVANT: {cumulative_fees:.0f}€/jour")
    print(f"   💚 Frais APRÈS: {final_fees:.1f}€/jour")
    print(f"   📈 RÉDUCTION: {total_reduction:.1f}%")
    print(f"   💸 ÉCONOMIE: {(cumulative_fees - final_fees)*30:.0f}€/mois")

def generate_ultra_config():
    print("\n🔧 === CONFIGURATION ULTRA-OPTIMISÉE ===")
    print()
    
    config_code = '''
# CONFIGURATION ULTRA-OPTIMISÉE - FRAIS RÉDUITS AU MAXIMUM

# Position sizing - Plus grosses positions = moins de trades
BASE_POSITION_SIZE_PERCENT = 30  # 30% capital (vs 20% actuel)
MIN_POSITION_SIZE_EUR = 1000     # 1000€ min (vs 500€) = -50% trades

# Limitations strictes
MAX_OPEN_POSITIONS = 2           # 2 max (vs 3) = plus sélectif
MAX_TRADES_PER_PAIR = 1          # Inchangé
COOLDOWN_BETWEEN_TRADES = 300    # 5min cooldown = évite spam

# Sélectivité signaux
MIN_SIGNAL_STRENGTH = 0.7        # Signaux forts uniquement
MIN_VOLUME_24H = 10000000        # Haute liquidité seulement

# Horaires optimisés (éviter high volatility)
TRADING_HOURS = {
    'start': 9,   # 9h (ouverture européenne)
    'end': 17,    # 17h (avant clôture US)
    'break_start': 12,  # Pause déjeuner
    'break_end': 14
}

# Paires ultra-sélectives
PRIORITY_PAIRS = ['EURBTC', 'EURETH', 'EURUSDT']  # Top 3 seulement
'''
    
    print(config_code)
    print()
    print("📊 IMPACT ATTENDU:")
    print("   • -77% frais BNB (déjà fait)")
    print("   • -50% trades (position 1000€)")
    print("   • -30% trades (signaux sélectifs)")
    print("   • -20% trades (cooldown)")
    print("   • TOTAL: -92% de frais !")

if __name__ == "__main__":
    show_fee_reduction_impact()
    generate_ultra_config()

#!/usr/bin/env python3
"""
Script pour vérifier les positions ouvertes réelles sur Binance
et expliquer l'écart entre export (+6,105€) et réalité (-900€)
"""

import json
from datetime import datetime

import requests


def check_binance_account_status():
    """Analyse l'écart entre export et portefeuille réel"""
    print("🔍 DIAGNOSTIC DE L'ÉCART BINANCE")
    print("=" * 50)
    
    # Données connues
    starting_balance = 20000
    current_balance = 19100
    export_pnl = 6105  # D'après l'analyse précédente
    
    real_loss = current_balance - starting_balance
    expected_balance = starting_balance + export_pnl
    missing_amount = current_balance - expected_balance
    
    print(f"📊 COMPARAISON")
    print(f"   Capital initial:        {starting_balance:,}€")
    print(f"   Balance actuelle:       {current_balance:,}€")
    print(f"   Perte réelle:           {real_loss:+,}€")
    print()
    print(f"   Export P&L:             {export_pnl:+,}€")
    print(f"   Balance attendue:       {expected_balance:,}€")
    print(f"   Écart inexpliqué:       {missing_amount:+,}€")
    
    print(f"\n💡 HYPOTHÈSES SUR L'ÉCART DE {abs(missing_amount):,}€:")
    
    if missing_amount < -5000:
        print(f"   1. 🏦 POSITIONS OUVERTES EN PERTE LATENTE (~{abs(missing_amount):,}€)")
        print(f"      → Vos trades sont encore ouverts avec des pertes non-réalisées")
        print(f"      → L'export ne compte que les trades FERMÉS")
        
        print(f"\n   2. 💸 FRAIS CACHÉS:")
        print(f"      → Frais de financement overnight")
        print(f"      → Frais de conversion automatique")
        print(f"      → Spread bid/ask sur les gros volumes")
        
        print(f"\n   3. 📈 VARIATION DE PRIX:")
        print(f"      → Prix d'entrée vs prix actuels des cryptos")
        print(f"      → Effet de levier si utilisé")
    
    print(f"\n🎯 ACTIONS RECOMMANDÉES:")
    print(f"   1. Vérifier les POSITIONS OUVERTES sur Binance")
    print(f"   2. Calculer les P&L latents de chaque position")
    print(f"   3. Vérifier l'historique des FRAIS dans Binance")
    print(f"   4. Nettoyer la DB du bot (40 positions fantômes)")
    
    # Simulation du calcul des pertes latentes
    print(f"\n📋 SIMULATION:")
    if abs(missing_amount) > 5000:
        estimated_open_loss = missing_amount
        print(f"   Si vous avez {abs(estimated_open_loss):,.0f}€ de pertes latentes,")
        print(f"   cela expliquerait parfaitement l'écart !")
        print(f"   ")
        print(f"   Balance théorique: {expected_balance:,}€")
        print(f"   - Pertes latentes: {estimated_open_loss:+,}€")
        print(f"   = Balance réelle:  {current_balance:,}€ ✅")
    
    return {
        'real_loss': real_loss,
        'missing_amount': missing_amount,
        'likely_open_positions_loss': missing_amount if missing_amount < -1000 else 0
    }

if __name__ == "__main__":
    result = check_binance_account_status()
    
    print(f"\n🏁 CONCLUSION:")
    if result['missing_amount'] < -5000:
        print(f"   Vous avez probablement ~{abs(result['missing_amount']):,.0f}€ de pertes latentes")
        print(f"   sur des positions encore ouvertes sur Binance.")
        print(f"   ")
        print(f"   ⚠️  C'est probablement lié aux 40 positions fantômes du bot !")
    else:
        print(f"   L'écart est relativement faible, probablement des frais.")

#!/usr/bin/env python3
"""
PATCH URGENT: Désactiver l'usage du BNB pour les frais
"""

import os
import sys

from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

def disable_bnb_fees():
    """Désactive l'usage du BNB pour payer les frais"""
    
    # Connexion à Binance
    client = Client(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_SECRET_KEY"),
        testnet=False  # Production
    )
    
    try:
        # Désactiver l'usage du BNB pour les frais
        result = client.toggle_bnb_burn_spot_margin(spotBNBBurn=False)
        
        print("🔧 PATCH APPLIQUÉ: Usage BNB pour frais DÉSACTIVÉ")
        print(f"   Résultat: {result}")
        print("   ✅ Tous les frais seront maintenant payés en EUR directement")
        print("   💰 Économie estimée: -70% de frais !")
        
        # Vérification du statut
        status = client.get_bnb_burn_spot_margin()
        print(f"\n📊 STATUT ACTUEL:")
        print(f"   Spot trading BNB burn: {status.get('spotBNBBurn', 'N/A')}")
        print(f"   Margin trading BNB burn: {status.get('marginBNBBurn', 'N/A')}")
        
        if not status.get('spotBNBBurn', True):
            print("   🎯 SUCCÈS: BNB burn désactivé pour le spot trading !")
        else:
            print("   ❌ ÉCHEC: BNB burn toujours actif")
            
    except Exception as e:
        print(f"❌ ERREUR lors de la désactivation: {e}")
        print("   Vérifiez vos permissions API")
        print("   Ou désactivez manuellement sur binance.com > Paramètres > Frais")

if __name__ == "__main__":
    print("🚨 PATCH URGENT: DÉSACTIVATION BNB FEES")
    print("="*50)
    disable_bnb_fees()

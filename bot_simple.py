#!/usr/bin/env python3
"""
Bot de Trading Scalping - Version simplifiée pour test
"""

import asyncio
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class SimpleTradingBot:
    """Bot de trading simplifié pour test"""
    
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
        
        print("🚀 Bot de Trading Scalping - Version Test")
        print("=" * 50)
        print(f"📊 Mode: {'Testnet' if self.testnet else 'Production'}")
        print(f"📱 Telegram: {'Configuré' if self.telegram_token else 'Non configuré'}")
        print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
    
    async def initialize_binance(self):
        """Initialise la connexion Binance"""
        try:
            from binance.client import Client
            
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            
            # Test de connexion
            server_time = self.client.get_server_time()
            print(f"✅ Connexion Binance établie")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur Binance: {e}")
            return False
    
    async def initialize_telegram(self):
        """Initialise le bot Telegram"""
        try:
            if not self.telegram_token:
                print("❌ Token Telegram manquant")
                return False
                
            from telegram import Bot
            
            self.bot = Bot(token=self.telegram_token)
            
            # Test de connexion
            me = await self.bot.get_me() # type: ignore
            print(f"✅ Bot Telegram: @{me.username}")
            
            # Notification de démarrage
            message = f"""
🚀 **Bot de Trading Scalping Démarré**

⏰ **Heure**: {datetime.now().strftime('%H:%M:%S')}
📊 **Mode**: {'Testnet' if self.testnet else 'Production'}
🎯 **Statut**: En cours d'initialisation...

*Bot prêt pour le trading automatisé!*
"""
            if self.telegram_chat:
                await self.bot.send_message(chat_id=self.telegram_chat, text=message, parse_mode='Markdown') # type: ignore
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur Telegram: {e}")
            return False
    
    async def get_eur_pairs(self):
        """Récupère les paires EUR disponibles"""
        try:
            tickers = self.client.get_all_tickers()
            eur_pairs = [t for t in tickers if t['symbol'].endswith('EUR')]
            
            print(f"📊 {len(eur_pairs)} paires EUR disponibles")
            
            # Tri par volume (approximatif)
            eur_pairs.sort(key=lambda x: float(x['count']) if 'count' in x else 0, reverse=True)
            
            # Affichage des top 10
            print("🔝 Top 10 paires EUR:")
            for i, pair in enumerate(eur_pairs[:10]):
                print(f"   {i+1}. {pair['symbol']} - Prix: {pair['price']} EUR")
            
            return eur_pairs
            
        except Exception as e:
            print(f"❌ Erreur récupération paires: {e}")
            return []
    
    async def simulate_trading_loop(self):
        """Simule une boucle de trading"""
        print("\\n🔄 Simulation de trading...")
        
        for i in range(5):  # 5 cycles de test
            print(f"\\n📊 Cycle {i+1}/5 - {datetime.now().strftime('%H:%M:%S')}")
            
            # Simulation scan des paires
            pairs = await self.get_eur_pairs()
            if pairs:
                selected_pair = pairs[0]['symbol']
                price = float(pairs[0]['price'])
                
                print(f"🔍 Analyse de {selected_pair} à {price} EUR")
                
                # Simulation d'analyse technique
                print("📈 Analyse technique:")
                print("   - EMA(9) vs EMA(21): En cours...")
                print("   - RSI: Calcul...")
                print("   - Volume: Vérification...")
                
                # Simulation signal
                if i % 2 == 0:  # Signal positif alternant
                    print("✅ Signal LONG détecté!")
                    
                    # Notification Telegram
                    if self.telegram_token:
                        message = f"""
📈 **Signal Détecté - {selected_pair}**

💰 **Prix**: {price:.4f} EUR
🔍 **Analyse**: Signal LONG confirmé
⏰ **Heure**: {datetime.now().strftime('%H:%M:%S')}

*Simulation - Aucun trade réel effectué*
"""
                        await self.bot.send_message(
                            chat_id=self.telegram_chat, 
                            text=message, 
                            parse_mode='Markdown'
                        ) # type: ignore
                else:
                    print("⏸️ Aucun signal pour le moment")
            
            # Attente avant le prochain cycle
            await asyncio.sleep(10)
        
        print("\\n✅ Simulation terminée")
    
    async def run(self):
        """Lance le bot"""
        print("🚀 Démarrage du bot...")
        
        # Initialisation
        if not await self.initialize_binance():
            print("❌ Impossible d'initialiser Binance")
            return
        
        if not await self.initialize_telegram():
            print("❌ Impossible d'initialiser Telegram")
            return
        
        print("\\n✅ Toutes les connexions sont établies")
        print("🔄 Lancement de la simulation...")
        
        try:
            await self.simulate_trading_loop()
        except KeyboardInterrupt:
            print("\\n🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
        finally:
            # Notification de fin
            if self.telegram_token:
                message = f"""
🛑 **Bot de Trading Arrêté**

⏰ **Heure**: {datetime.now().strftime('%H:%M:%S')}
📊 **Statut**: Simulation terminée

*À bientôt pour le trading!*
"""
                await self.bot.send_message(
                    chat_id=self.telegram_chat, 
                    text=message, 
                    parse_mode='Markdown'
                ) # type: ignore
            
            print("\\n👋 Bot arrêté proprement")

async def main():
    """Point d'entrée principal"""
    bot = SimpleTradingBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)

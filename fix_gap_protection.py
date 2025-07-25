#!/usr/bin/env python3
"""
CORRECTIF URGENT: Protection anti-gap et utilisation des paramètres config.py
"""

import os
import re


def add_gap_protection_to_main():
    """Ajoute la logique de protection anti-gap dans main.py"""
    
    main_py_path = "main.py"
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Ajouter l'import des nouveaux paramètres de config après les imports existants
    import_section = """from config import API_CONFIG, BLACKLISTED_PAIRS, TradingConfig"""
    
    if "GAP_PROTECTION_THRESHOLD" not in content:
        print("🔧 Ajout des paramètres de protection anti-gap...")
        
        # Chercher la section des imports de config
        config_import_pattern = r"from config import API_CONFIG, BLACKLISTED_PAIRS, TradingConfig"
        
        if re.search(config_import_pattern, content):
            print("✅ Import config trouvé, pas besoin de modification")
        else:
            print("❌ Import config non trouvé, vérification manuelle requise")
    
    # 2. Ajouter la logique de blacklisting automatique dans manage_open_positions
    gap_protection_code = '''
                    # 🔥 PROTECTION ANTI-GAP AUTOMATIQUE
                    if gap_excess > self.config.MAX_ACCEPTABLE_GAP_PERCENT:
                        if self.config.BLACKLIST_ON_EXCESSIVE_GAP:
                            # Ajouter automatiquement à la blacklist
                            if trade.pair not in BLACKLISTED_PAIRS:
                                self.logger.error(f"🚨 BLACKLISTAGE AUTOMATIQUE: {trade.pair} ajouté à la blacklist (gap: {gap_excess:.2f}%)")
                                BLACKLISTED_PAIRS.append(trade.pair)
                                
                                # Notification Telegram d'urgence
                                if self.telegram_notifier:
                                    try:
                                        await self.telegram_notifier.send_message(
                                            f"🚨 BLACKLISTAGE AUTOMATIQUE\\n\\n"
                                            f"Paire: {trade.pair}\\n"
                                            f"Gap excessif: {gap_excess:.2f}%\\n"
                                            f"Perte: {actual_loss:.2f}% vs {expected_loss:.2f}% attendu\\n"
                                            f"Paire automatiquement blacklistée"
                                        )
                                    except Exception as e:
                                        self.logger.error(f"❌ Erreur notification blacklist: {e}")
'''
    
    # Chercher la section après logging du GAP
    gap_section_pattern = r"(\s+await self\.close_position\(trade_id, current_price, \"STOP_LOSS\"\)\s+continue)"
    
    if re.search(gap_section_pattern, content):
        # Insérer le code de protection avant la fermeture
        content = re.sub(
            gap_section_pattern,
            gap_protection_code + r"\1",
            content
        )
        print("✅ Protection anti-gap ajoutée dans manage_open_positions")
    else:
        print("⚠️ Section GAP non trouvée, ajout manuel requis")
    
    # 3. Ajouter la surveillance intensive
    intensive_monitoring_code = '''
                # 🔥 SURVEILLANCE INTENSIVE ANTI-GAP
                if self.config.ENABLE_INTENSIVE_MONITORING:
                    distance_to_stop = abs(current_price - trade.stop_loss) / trade.stop_loss * 100
                    if distance_to_stop <= self.config.GAP_PROTECTION_THRESHOLD:
                        self.logger.warning(f"🚨 SURVEILLANCE RENFORCÉE {trade.pair}: Prix {current_price:.4f} proche SL {trade.stop_loss:.4f} ({distance_to_stop:.2f}%)")
                        
                        # Vérification plus fréquente (toutes les 5 secondes au lieu de 40)
                        await asyncio.sleep(5)
                        
                        # Re-vérifier le prix immédiatement
                        fresh_ticker = self.binance_client.get_symbol_ticker(symbol=trade.pair)
                        fresh_price = float(fresh_ticker['price'])
                        
                        if fresh_price <= trade.stop_loss:
                            self.logger.error(f"🚨 STOP LOSS IMMÉDIAT {trade.pair}: {fresh_price:.4f} <= {trade.stop_loss:.4f}")
                            await self.close_position(trade_id, fresh_price, "STOP_LOSS_IMMEDIATE")
                            continue
'''
    
    # Ajouter la surveillance intensive après récupération du prix
    price_section_pattern = r"(# Calcul du P&L\s+pnl_percent = \(current_price - trade\.entry_price\) / trade\.entry_price \* 100)"
    
    if re.search(price_section_pattern, content):
        content = re.sub(
            price_section_pattern,
            r"\1" + intensive_monitoring_code,
            content
        )
        print("✅ Surveillance intensive ajoutée")
    else:
        print("⚠️ Section prix non trouvée pour surveillance intensive")
    
    # Sauvegarder le fichier modifié
    backup_path = "main.py.backup_gap_protection"
    
    # Créer une sauvegarde
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(main_py_path, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    
    print(f"💾 Sauvegarde créée: {backup_path}")
    
    # Écrire le nouveau contenu
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py mis à jour avec protection anti-gap")

def main():
    print("🔥 CORRECTIF PROTECTION ANTI-GAP")
    print("=" * 50)
    
    print("\n📋 PROBLÈMES IDENTIFIÉS:")
    print("1. ✅ STOP_LOSS_PERCENT réduit de 0.35% à 0.25%")
    print("2. ✅ ENAUSDC ajouté à la blacklist")
    print("3. ✅ Paramètres anti-gap ajoutés dans config.py")
    print("4. 🔧 RESTE: Utiliser ces paramètres dans main.py")
    
    print("\n🛠️ APPLICATION DES CORRECTIONS:")
    
    if os.path.exists("main.py"):
        add_gap_protection_to_main()
        print("\n✅ Corrections appliquées !")
        
        print("\n📌 PROCHAINES ÉTAPES:")
        print("1. Déployer sur le VPS: scp main.py root@213.199.41.168:/opt/toTheMoon_tradebot/")
        print("2. Redémarrer le bot sur le VPS")
        print("3. Surveiller les logs pour vérifier que la protection fonctionne")
        
    else:
        print("❌ main.py non trouvé dans le répertoire courant")

if __name__ == "__main__":
    main()
    main()

#!/usr/bin/env python3
"""
🔄 SCRIPT DE MIGRATION COMPLÈTE EUR → USDC
Modifie automatiquement tous les fichiers pour passer de EUR à USDC
"""

import os
import re


def migrate_files_to_usdc():
    print("🚀 === MIGRATION COMPLÈTE EUR → USDC ===")
    print()
    
    # Dictionnaire des remplacements
    replacements = {
        # Références de base
        "'EUR'": "'USDC'",
        '"EUR"': '"USDC"',
        "EUR": "USDC",
        
        # Références spécifiques
        "eur_balance": "usdc_balance",
        "EUR disponible": "USDC disponible",
        "Capital EUR": "Capital USDC",
        "volume_eur": "volume_usdc",
        "price_eur": "price_usdc", 
        "value_eur": "value_usdc",
        "MIN_VOLUME_EUR": "MIN_VOLUME_USDC",
        "MIN_POSITION_SIZE_EUR": "MIN_POSITION_SIZE_USDC",
        
        # Fonctions et méthodes
        "endswith('EUR')": "endswith('USDC')",
        'endswith("EUR")': 'endswith("USDC")',
        "replace('EUR', '')": "replace('USDC', '')",
        'replace("EUR", "")': 'replace("USDC", "")',
        "scan_eur_pairs": "scan_usdc_pairs",
        
        # Commentaires et logs
        "paires EUR": "paires USDC",
        "Scan des paires EUR": "Scan des paires USDC",
        "Stratégie multi-paires EUR": "Stratégie multi-paires USDC",
        
        # Formats de devises
        ":.2f} EUR": ":.2f} USDC",
        ":.2f EUR": ":.2f USDC",
        "1f}M EUR": "1f}M USDC",
        
        # Google Sheets et logs
        "avant: {.*:.2f} EUR, après: {.*:.2f} EUR": "avant: {capital_before_trade:.2f} USDC, après: {capital_after_trade:.2f} USDC",
    }
    
    # Fichiers à modifier
    files_to_modify = [
        "main.py",
        "config.py"
    ]
    
    for filename in files_to_modify:
        if not os.path.exists(filename):
            print(f"⚠️  Fichier {filename} non trouvé")
            continue
            
        print(f"📝 Migration de {filename}...")
        
        # Lire le fichier
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sauvegarder l'original
        backup_filename = f"{filename}.backup_eur"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   💾 Sauvegarde créée: {backup_filename}")
        
        # Compter les remplacements
        total_replacements = 0
        
        # Appliquer les remplacements
        for old_text, new_text in replacements.items():
            if old_text in content:
                count = content.count(old_text)
                content = content.replace(old_text, new_text)
                total_replacements += count
                print(f"   🔄 {old_text} → {new_text} ({count} fois)")
        
        # Écrire le fichier modifié
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ {filename} migré ({total_replacements} remplacements)")
        print()
    
    print("🎯 === REMPLACEMENTS SPÉCIAUX ===")
    
    # Remplacements spéciaux pour main.py
    if os.path.exists("main.py"):
        with open("main.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corrections spécifiques
        special_replacements = [
            # Correction des messages de log qui peuvent être complexes
            ("💶 USDC disponible", "💵 USDC disponible"),
            ("EUR + valeur crypto", "USDC + valeur crypto"),
            ("Aucun solde EUR ou crypto", "Aucun solde USDC ou crypto"),
            ("asset + 'EUR'", "asset + 'USDC'"),
            ("Volume minimum 100k EUR", "Volume minimum 50M USDC"),
            ("si pas de paire EUR", "si pas de paire USDC"),
            
            # Fix des expressions regex complexes
            ("📊 Google Sheets - Capital avant: {capital_before_trade:.2f} USDC, après: {capital_after_trade:.2f} USDC", 
             "📊 Google Sheets - Capital avant: {capital_before_trade:.2f} USDC, après: {capital_after_trade:.2f} USDC"),
        ]
        
        for old_text, new_text in special_replacements:
            if old_text in content:
                content = content.replace(old_text, new_text)
                print(f"   🔧 Correction spéciale: {old_text[:50]}...")
        
        with open("main.py", 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("✅ MIGRATION TERMINÉE!")
    print()
    print("📋 PROCHAINES ÉTAPES:")
    print("   1️⃣ Vérifier les fichiers modifiés")
    print("   2️⃣ Tester la compilation")
    print("   3️⃣ Convertir EUR → USDC sur Binance")
    print("   4️⃣ Redémarrer le bot")

if __name__ == "__main__":
    migrate_files_to_usdc()

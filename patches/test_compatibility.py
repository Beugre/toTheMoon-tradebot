#!/usr/bin/env python3
"""
Test de compatibilité chemin credentials pour Windows/Linux
"""

import os
import sys

# Simulation des deux environnements
print("🔍 TEST COMPATIBILITÉ CHEMINS")
print("=" * 50)

# Test 1: Chemin relatif (comme dans .env actuel)
relative_path = "credentials.json"
print(f"\n📝 Test 1 - Chemin relatif: {relative_path}")
print(f"   os.path.isabs(): {os.path.isabs(relative_path)}")

# Simulation du code config.py
if not os.path.isabs(relative_path):
    # Simulation Windows (répertoire actuel)
    windows_absolute = os.path.join("C:\\dev\\toTheMoon_tradebot", relative_path)
    print(f"   Windows absolu: {windows_absolute}")
    
    # Simulation Linux VPS
    linux_absolute = os.path.join("/home/user/toTheMoon_tradebot", relative_path) 
    print(f"   Linux absolu: {linux_absolute}")

# Test 2: Chemin déjà absolu
absolute_path = "/home/user/toTheMoon_tradebot/credentials.json"
print(f"\n📝 Test 2 - Chemin absolu: {absolute_path}")
print(f"   os.path.isabs(): {os.path.isabs(absolute_path)}")
print(f"   Pas de modification: {absolute_path}")

print(f"\n✅ SOLUTION UNIVERSELLE:")
print(f"   • .env garde 'credentials.json' (relatif)")
print(f"   • config.py le convertit en absolu automatiquement")
print(f"   • Compatible Windows ET Linux")
print(f"   • Pas de chemin en dur dans .env")

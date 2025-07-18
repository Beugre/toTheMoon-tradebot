"""
Script d'installation pour TA-Lib (Windows)
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def install_talib_windows():
    """Installation de TA-Lib sur Windows"""
    print("📦 Installation de TA-Lib pour Windows...")
    
    # Vérification de l'architecture
    architecture = platform.architecture()[0]
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    print(f"🔍 Python {python_version} - Architecture {architecture}")
    
    # URLs des wheels pré-compilés pour Windows
    if architecture == "64bit":
        if python_version == "3.12":
            wheel_url = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp312-cp312-win_amd64.whl"
        elif python_version == "3.11":
            wheel_url = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl"
        elif python_version == "3.10":
            wheel_url = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp310-cp310-win_amd64.whl"
        elif python_version == "3.9":
            wheel_url = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp39-cp39-win_amd64.whl"
        else:
            print(f"⚠️ Version Python {python_version} non supportée pour TA-Lib")
            return False
    else:
        print("⚠️ Architecture 32-bit non supportée")
        return False
    
    try:
        # Installation via pip avec le wheel
        print(f"📦 Installation depuis: {wheel_url}")
        subprocess.run([
            sys.executable, "-m", "pip", "install", wheel_url
        ], check=True)
        
        print("✅ TA-Lib installé avec succès!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de TA-Lib: {e}")
        print("💡 Essayez l'installation manuelle:")
        print("   1. Téléchargez le wheel depuis https://github.com/cgohlke/talib-build/releases")
        print("   2. Installez avec: pip install TA_Lib-0.4.28-cp312-cp312-win_amd64.whl")
        return False

def install_talib_alternative():
    """Installation alternative de TA-Lib"""
    print("📦 Tentative d'installation alternative...")
    
    try:
        # Essai avec conda si disponible
        subprocess.run([
            "conda", "install", "-c", "conda-forge", "ta-lib", "-y"
        ], check=True)
        
        print("✅ TA-Lib installé via conda!")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Conda non disponible")
    
    try:
        # Essai installation standard
        subprocess.run([
            sys.executable, "-m", "pip", "install", "TA-Lib"
        ], check=True)
        
        print("✅ TA-Lib installé via pip!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation standard échouée: {e}")
        return False

def test_talib_installation():
    """Test de l'installation de TA-Lib"""
    try:
        import talib
        print("✅ TA-Lib importé avec succès!")
        
        # Test d'une fonction simple
        import numpy as np
        test_data = np.array([1, 2, 3, 4, 5], dtype=float)
        sma = talib.SMA(test_data, timeperiod=3) # type: ignore
        print(f"✅ Test SMA: {sma}")
        
        return True
        
    except ImportError as e:
        print(f"❌ TA-Lib non importable: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("🚀 Installation de TA-Lib pour le Bot de Trading")
    print("=" * 50)
    
    # Test si TA-Lib est déjà installé
    if test_talib_installation():
        print("✅ TA-Lib déjà installé et fonctionnel!")
        return 0
    
    # Installation selon le système
    if platform.system() == "Windows":
        success = install_talib_windows()
        if not success:
            success = install_talib_alternative()
    else:
        success = install_talib_alternative()
    
    if success:
        # Test final
        if test_talib_installation():
            print("🎉 TA-Lib installé et testé avec succès!")
            return 0
        else:
            print("❌ TA-Lib installé mais non fonctionnel")
            return 1
    else:
        print("❌ Échec de l'installation de TA-Lib")
        print("\\n💡 Solutions alternatives:")
        print("1. Le bot peut fonctionner sans TA-Lib (fonctionnalités limitées)")
        print("2. Installation manuelle depuis https://github.com/cgohlke/talib-build")
        print("3. Utilisez un environnement conda")
        return 1

if __name__ == "__main__":
    sys.exit(main())

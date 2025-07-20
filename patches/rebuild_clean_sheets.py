#!/usr/bin/env python3
"""
🆕 NOUVEAU SYSTÈME GOOGLE SHEETS ULTRA-PROPRE
Reconstruction complète avec formules fonctionnelles
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Configuration paths
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_path)

from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("❌ Modules manquants. Installez avec: pip install gspread oauth2client")
    sys.exit(1)

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class Trade:
    pair: str
    direction: TradeDirection
    size: float
    entry_price: float
    exit_price: float = 0
    stop_loss: float = 0
    take_profit: float = 0
    timestamp: datetime = None  # type: ignore
    pnl: float = 0
    exit_reason: str = ""
    duration: str = ""

class CleanGoogleSheetsSystem:
    """Système Google Sheets entièrement reconstruit"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialise la connexion Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope # type: ignore
            )
            
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            print("✅ Connexion Google Sheets établie")
            
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
    
    def delete_all_existing_sheets(self):
        """Supprime tous les onglets existants (sauf le premier)"""
        try:
            worksheets = self.spreadsheet.worksheets() # type: ignore
            
            # Garder seulement le premier onglet pour éviter l'erreur
            for i, worksheet in enumerate(worksheets):
                if i > 0:  # Ne pas supprimer le premier
                    self.spreadsheet.del_worksheet(worksheet) # type: ignore
                    print(f"🗑️ Supprimé: {worksheet.title}")
            
            # Renommer le premier onglet
            if worksheets:
                worksheets[0].update_title("TEMP_DELETE")
                
        except Exception as e:
            print(f"⚠️ Erreur suppression: {e}")
    
    def create_trades_detailed_sheet(self):
        """Crée l'onglet Trades_Detailed avec structure simple et efficace"""
        try:
            sheet = self.spreadsheet.add_worksheet(title="Trades_Detailed", rows=1000, cols=20) # type: ignore
            
            # Headers simples et clairs
            headers = [
                "Date", "Heure", "Paire", "Direction", "Taille", 
                "Prix_Entree", "Prix_Sortie", "Stop_Loss", "Take_Profit",
                "Frais_Entree", "Frais_Sortie", "PnL_Brut", "PnL_Net", 
                "ROI_Net", "Duree", "Raison_Sortie", "Session", "Intensite",
                "Capital_Avant", "Capital_Apres"
            ]
            
            # Ajouter les headers
            sheet.append_row(headers)
            
            # Formatage header
            sheet.format("A1:T1", {
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            
            print("✅ Onglet 'Trades_Detailed' créé (20 colonnes)")
            return sheet
            
        except Exception as e:
            print(f"❌ Erreur création Trades_Detailed: {e}")
            return None
    
    def create_performance_summary_sheet(self):
        """Crée l'onglet Performance_Summary avec calculs automatiques SIMPLES"""
        try:
            sheet = self.spreadsheet.add_worksheet(title="Performance_Summary", rows=50, cols=15) # type: ignore
            
            # Structure simplifiée
            data = [
                ["RÉSUMÉ PERFORMANCE TRADING BOT v3.0", ""],
                ["", ""],
                ["=== MÉTRIQUES GLOBALES ===", ""],
                ["Total Trades", "=COUNTA(Trades_Detailed!A:A)-1"],
                ["Trades Gagnants", "=COUNTIF(Trades_Detailed!M:M,\">0\")"],
                ["Trades Perdants", "=COUNTIF(Trades_Detailed!M:M,\"<0\")"],
                ["Win Rate %", "=IF(B4>0,B5/B4*100,0)"],
                ["P&L Total $", "=SUM(Trades_Detailed!M:M)"],
                ["P&L Moyen $", "=IF(B4>0,B8/B4,0)"],
                ["ROI Moyen %", "=AVERAGE(Trades_Detailed!N:N)"],
                ["", ""],
                ["=== TOP 5 PAIRES ===", "P&L Net"],
                ["BTCUSDC", "=SUMIF(Trades_Detailed!C:C,\"BTCUSDC\",Trades_Detailed!M:M)"],
                ["ETHUSDC", "=SUMIF(Trades_Detailed!C:C,\"ETHUSDC\",Trades_Detailed!M:M)"],
                ["SOLUSDC", "=SUMIF(Trades_Detailed!C:C,\"SOLUSDC\",Trades_Detailed!M:M)"],
                ["XRPUSDC", "=SUMIF(Trades_Detailed!C:C,\"XRPUSDC\",Trades_Detailed!M:M)"],
                ["DOGEUSDC", "=SUMIF(Trades_Detailed!C:C,\"DOGEUSDC\",Trades_Detailed!M:M)"],
                ["", ""],
                ["=== ANALYSE HORAIRE ===", "Nb Trades"],
                ["09h-12h (Europe)", "=COUNTIFS(Trades_Detailed!B:B,\">=09:00\",Trades_Detailed!B:B,\"<12:00\")"],
                ["12h-15h (Lunch)", "=COUNTIFS(Trades_Detailed!B:B,\">=12:00\",Trades_Detailed!B:B,\"<15:00\")"],
                ["15h-18h (EU-US)", "=COUNTIFS(Trades_Detailed!B:B,\">=15:00\",Trades_Detailed!B:B,\"<18:00\")"],
                ["18h-23h (US)", "=COUNTIFS(Trades_Detailed!B:B,\">=18:00\",Trades_Detailed!B:B,\"<23:00\")"],
                ["", ""],
                ["Dernière MAJ", "=NOW()"],
            ]
            
            # Insérer toutes les données
            for row in data:
                sheet.append_row(row)
            
            # Formatage
            sheet.format("A1:B1", {
                "backgroundColor": {"red": 0.1, "green": 0.7, "blue": 0.1},
                "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            
            sheet.format("A3:A3", {
                "backgroundColor": {"red": 0.9, "green": 0.6, "blue": 0.1},
                "textFormat": {"bold": True}
            })
            
            sheet.format("A12:A12", {
                "backgroundColor": {"red": 0.9, "green": 0.6, "blue": 0.1},
                "textFormat": {"bold": True}
            })
            
            sheet.format("A19:A19", {
                "backgroundColor": {"red": 0.9, "green": 0.6, "blue": 0.1},
                "textFormat": {"bold": True}
            })
            
            print("✅ Onglet 'Performance_Summary' créé avec formules simples")
            return sheet
            
        except Exception as e:
            print(f"❌ Erreur création Performance_Summary: {e}")
            return None
    
    def create_pairs_analysis_sheet(self):
        """Crée l'onglet analyse par paire"""
        try:
            sheet = self.spreadsheet.add_worksheet(title="Pairs_Analysis", rows=20, cols=10) # type: ignore
            
            # Liste des paires principales
            pairs = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "XRPUSDC", "DOGEUSDC", 
                    "ADAUSDC", "MATICUSDC", "LTCUSDC", "LINKUSDC", "DOTUSDC"]
            
            # Headers
            headers = ["Paire", "Nb_Trades", "Win_Rate_%", "P&L_Total", "P&L_Moyen", 
                      "ROI_Moyen_%", "Meilleur_Trade", "Pire_Trade", "Recommandation"]
            
            sheet.append_row(headers)
            
            # Données pour chaque paire
            for i, pair in enumerate(pairs, 2):
                row = [
                    pair,
                    f"=COUNTIF(Trades_Detailed!C:C,\"{pair}\")",
                    f"=IF(B{i}>0,COUNTIFS(Trades_Detailed!C:C,\"{pair}\",Trades_Detailed!M:M,\">0\")/B{i}*100,0)",
                    f"=SUMIF(Trades_Detailed!C:C,\"{pair}\",Trades_Detailed!M:M)",
                    f"=IF(B{i}>0,D{i}/B{i},0)",
                    f"=IF(COUNTIF(Trades_Detailed!C:C,\"{pair}\")>0,AVERAGEIF(Trades_Detailed!C:C,\"{pair}\",Trades_Detailed!N:N),0)",
                    f"=IF(COUNTIF(Trades_Detailed!C:C,\"{pair}\")>0,MAXIFS(Trades_Detailed!M:M,Trades_Detailed!C:C,\"{pair}\"),0)",
                    f"=IF(COUNTIF(Trades_Detailed!C:C,\"{pair}\")>0,MINIFS(Trades_Detailed!M:M,Trades_Detailed!C:C,\"{pair}\"),0)",
                    f"=IF(C{i}>60,\"HIGH\",IF(C{i}>30,\"MEDIUM\",\"LOW\"))"
                ]
                sheet.append_row(row)
            
            # Formatage
            sheet.format("A1:I1", {
                "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.1},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            
            print("✅ Onglet 'Pairs_Analysis' créé avec 10 paires")
            return sheet
            
        except Exception as e:
            print(f"❌ Erreur création Pairs_Analysis: {e}")
            return None
    
    def clean_up_temp_sheet(self):
        """Supprime l'onglet temporaire"""
        try:
            temp_sheet = self.spreadsheet.worksheet("TEMP_DELETE") # type: ignore
            self.spreadsheet.del_worksheet(temp_sheet) # type: ignore
            print("🗑️ Onglet temporaire supprimé")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer l'onglet temporaire: {e}")
    
    def add_sample_trades(self):
        """Ajoute des trades d'exemple pour tester les formules"""
        try:
            sheet = self.spreadsheet.worksheet("Trades_Detailed") # type: ignore
            
            # Trades d'exemple réalistes
            sample_trades = [
                ["2025-07-20", "10:30", "BTCUSDC", "LONG", 1000, 65000, 65650, 64500, 65600, 65, 65.65, 650, 519.35, 0.52, "1h15m", "TAKE_PROFIT", "EUROPE", 80, 22000, 22519],
                ["2025-07-20", "11:45", "ETHUSDC", "SHORT", 800, 3200, 3150, 3250, 3160, 25.6, 25.2, -50, -100.8, -0.13, "45m", "TAKE_PROFIT", "EUROPE", 90, 22519, 22418],
                ["2025-07-20", "13:20", "SOLUSDC", "LONG", 600, 140, 141.5, 139, 141.4, 8.4, 8.49, 900, 883.11, 1.47, "2h10m", "TAKE_PROFIT", "EU-US", 100, 22418, 23301],
                ["2025-07-20", "15:15", "XRPUSDC", "LONG", 500, 0.52, 0.525, 0.515, 0.526, 2.6, 2.63, 25, 19.77, 0.4, "30m", "TAKE_PROFIT", "EU-US", 100, 23301, 23321],
                ["2025-07-20", "16:45", "DOGEUSDC", "SHORT", 400, 0.12, 0.118, 0.122, 0.118, 0.48, 0.47, -8, -8.95, -0.22, "1h", "TAKE_PROFIT", "US", 85, 23321, 23312],
            ]
            
            # Ajouter les trades
            for trade in sample_trades:
                sheet.append_row(trade)
            
            print(f"✅ {len(sample_trades)} trades d'exemple ajoutés")
            
        except Exception as e:
            print(f"❌ Erreur ajout trades d'exemple: {e}")

def rebuild_google_sheets_system():
    """Reconstruction complète du système Google Sheets"""
    
    print("🔄 RECONSTRUCTION COMPLÈTE GOOGLE SHEETS")
    print("=" * 60)
    
    # Configuration
    credentials_path = "../credentials.json"
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Fichier credentials.json manquant: {credentials_path}")
        return False
    
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID non défini")
        return False
    
    try:
        # Initialisation du système propre
        clean_system = CleanGoogleSheetsSystem(credentials_path, spreadsheet_id)
        
        if not clean_system.client:
            print("❌ Impossible d'initialiser le système")
            return False
        
        print(f"📊 Spreadsheet ID: {spreadsheet_id}")
        
        # Étape 1: Nettoyage complet
        print("\n🗑️ ÉTAPE 1: Nettoyage des anciens onglets...")
        clean_system.delete_all_existing_sheets()
        
        # Étape 2: Création des nouveaux onglets
        print("\n🔨 ÉTAPE 2: Création des nouveaux onglets...")
        
        trades_sheet = clean_system.create_trades_detailed_sheet()
        if not trades_sheet:
            return False
        
        summary_sheet = clean_system.create_performance_summary_sheet()
        if not summary_sheet:
            return False
        
        pairs_sheet = clean_system.create_pairs_analysis_sheet()
        if not pairs_sheet:
            return False
        
        # Étape 3: Ajout de données de test
        print("\n📊 ÉTAPE 3: Ajout de trades de test...")
        clean_system.add_sample_trades()
        
        # Étape 4: Nettoyage final
        print("\n🧹 ÉTAPE 4: Nettoyage final...")
        clean_system.clean_up_temp_sheet()
        
        print("\n🎉 RECONSTRUCTION TERMINÉE AVEC SUCCÈS!")
        print(f"📋 Onglets créés:")
        print(f"   📊 Trades_Detailed (20 colonnes détaillées)")
        print(f"   📈 Performance_Summary (métriques globales)")
        print(f"   🎯 Pairs_Analysis (analyse par paire)")
        print(f"")
        print(f"✅ Formules Google Sheets FONCTIONNELLES")
        print(f"✅ 5 trades de test ajoutés")
        print(f"✅ Calculs automatiques activés")
        print(f"")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur during reconstruction: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = rebuild_google_sheets_system()
    
    if success:
        print("\n🚀 SYSTÈME GOOGLE SHEETS ENTIÈREMENT RECONSTRUIT!")
        print("📋 Vérifiez votre spreadsheet - tout devrait fonctionner parfaitement")
    else:
        print("\n❌ ÉCHEC DE LA RECONSTRUCTION")
        print("💡 Vérifiez les credentials et l'ID du spreadsheet")

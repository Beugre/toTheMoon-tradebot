"""
Logger Google Sheets pour le suivi des performances
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

try:
    import gspread
    from gspread.exceptions import APIError, SpreadsheetNotFound
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("⚠️ gspread non installé. Installez avec: pip install gspread oauth2client")
    gspread = None

@dataclass
class TradeLog:
    """Structure pour le log des trades"""
    date: str
    heure: str
    paire: str
    direction: str
    taille: float
    prix_entree: float
    prix_sortie: float
    stop_loss: float
    take_profit: float
    pnl_eur: float
    pnl_percent: float
    duree: str
    raison_sortie: str
    capital_avant: float
    capital_apres: float

@dataclass
class PerformanceLog:
    """Structure pour le log des performances"""
    date: str
    capital_debut: float
    capital_fin: float
    pnl_eur: float
    pnl_percent: float
    nb_trades: int
    trades_gagnants: int
    trades_perdants: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    statut: str

class SheetsLogger:
    """Gestionnaire de logging Google Sheets"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str = ""):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des services
        self.client = None
        self.spreadsheet = None
        
        if gspread:
            self.initialize_sheets()
        else:
            self.logger.warning("⚠️ Google Sheets non configuré - module manquant")

    def initialize_sheets(self):
        """Initialise la connexion Google Sheets"""
        try:
            # Définition des scopes
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Authentification
            credentials = ServiceAccountCredentials.from_json_keyfile_name( # type: ignore
                self.credentials_path, scope # type: ignore
            )
            
            self.client = gspread.authorize(credentials) # type: ignore
            
            # Ouverture du spreadsheet
            if self.spreadsheet_id:
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                # Création d'un nouveau spreadsheet
                self.spreadsheet = self.client.create("Trading Bot Scalping - Logs")
                self.spreadsheet_id = self.spreadsheet.id
                self.logger.info(f"📊 Nouveau spreadsheet créé: {self.spreadsheet_id}")
            
            # Création des onglets si nécessaire
            self.setup_worksheets()
            
            self.logger.info("📊 Google Sheets initialisé avec succès")
            
        except FileNotFoundError:
            self.logger.error(f"❌ Fichier credentials non trouvé: {self.credentials_path}")
        except json.JSONDecodeError:
            self.logger.error("❌ Fichier credentials JSON invalide")
        except APIError as e: # type: ignore
            self.logger.error(f"❌ Erreur API Google Sheets: {e}")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Google Sheets: {e}")

    def setup_worksheets(self):
        """Configure les onglets du spreadsheet"""
        try:
            # Récupération des onglets existants
            existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()] # type: ignore
            
            # Création onglet Trades
            if "Trades" not in existing_sheets:
                trades_sheet = self.spreadsheet.add_worksheet(title="Trades", rows=1000, cols=20) # type: ignore
                self.setup_trades_headers(trades_sheet)
            
            # Création onglet Performance
            if "Performance" not in existing_sheets:
                perf_sheet = self.spreadsheet.add_worksheet(title="Performance", rows=500, cols=15) # type: ignore
                self.setup_performance_headers(perf_sheet)
            
            # Création onglet Dashboard
            if "Dashboard" not in existing_sheets:
                dash_sheet = self.spreadsheet.add_worksheet(title="Dashboard", rows=50, cols=10) # type: ignore
                self.setup_dashboard(dash_sheet)
            
            # Suppression de l'onglet par défaut si nécessaire
            if "Feuille 1" in existing_sheets:
                self.spreadsheet.del_worksheet(self.spreadsheet.worksheet("Feuille 1")) # type: ignore
                
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration onglets: {e}")

    def setup_trades_headers(self, sheet):
        """Configure les en-têtes de l'onglet Trades"""
        headers = [
            "Date", "Heure", "Paire", "Direction", "Taille", "Prix Entrée", 
            "Prix Sortie", "Stop Loss", "Take Profit", "P&L (EUR)", 
            "P&L (%)", "Durée", "Raison Sortie", "Capital Avant", "Capital Après"
        ]
        
        sheet.append_row(headers)
        
        # Formatage des en-têtes
        sheet.format("A1:O1", {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    def setup_performance_headers(self, sheet):
        """Configure les en-têtes de l'onglet Performance"""
        headers = [
            "Date", "Capital Début", "Capital Fin", "P&L (EUR)", "P&L (%)", 
            "Nb Trades", "Trades Gagnants", "Trades Perdants", "Win Rate (%)", 
            "Profit Factor", "Max Drawdown (%)", "Statut"
        ]
        
        sheet.append_row(headers)
        
        # Formatage des en-têtes
        sheet.format("A1:L1", {
            "backgroundColor": {"red": 0.9, "green": 0.6, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    def setup_dashboard(self, sheet):
        """Configure le dashboard"""
        # Métriques principales
        dashboard_data = [
            ["📊 DASHBOARD TRADING BOT", ""],
            ["", ""],
            ["Capital Initial", "=Performance!B2"],
            ["Capital Actuel", "=Performance!C2"],
            ["P&L Total", "=Performance!D2"],
            ["Performance (%)", "=Performance!E2"],
            ["", ""],
            ["Trades Aujourd'hui", "=Performance!F2"],
            ["Win Rate", "=Performance!I2"],
            ["Profit Factor", "=Performance!J2"],
            ["Max Drawdown", "=Performance!K2"],
            ["", ""],
            ["Statut", "=Performance!L2"],
            ["Dernière MAJ", "=NOW()"]
        ]
        
        for row in dashboard_data:
            sheet.append_row(row)
        
        # Formatage du titre
        sheet.format("A1:B1", {
            "backgroundColor": {"red": 0.1, "green": 0.7, "blue": 0.1},
            "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    async def log_trade(self, trade, action: str):
        """Log un trade dans Google Sheets"""
        if not self.client:
            self.logger.warning("⚠️ Google Sheets non initialisé - trade non loggé")
            return
        
        try:
            trades_sheet = self.spreadsheet.worksheet("Trades") # type: ignore
            
            if action == "OPEN":
                # Log d'ouverture
                row = [
                    trade.timestamp.strftime("%Y-%m-%d"),
                    trade.timestamp.strftime("%H:%M:%S"),
                    trade.pair,
                    trade.direction.value,
                    trade.size,
                    trade.entry_price,
                    "",  # Prix sortie vide
                    trade.stop_loss,
                    trade.take_profit,
                    "",  # P&L vide
                    "",  # P&L % vide
                    "",  # Durée vide
                    "",  # Raison sortie vide
                    "",  # Capital avant
                    ""   # Capital après
                ]
                trades_sheet.append_row(row) # type: ignore
            
            elif action == "CLOSE" or action == "CLOSE_VIRTUAL":
                # Mise à jour du trade existant
                # Recherche de la ligne du trade
                all_values = trades_sheet.get_all_values()
                
                for i, row in enumerate(all_values[1:], 2):  # Skip header
                    if (row[1] == trade.timestamp.strftime("%H:%M:%S") and 
                        row[2] == trade.pair):
                        
                        # Mise à jour de la ligne
                        exit_price = getattr(trade, 'exit_price', 0)
                        pnl = getattr(trade, 'pnl', 0)
                        exit_reason = getattr(trade, 'exit_reason', action)
                        duration = getattr(trade, 'duration', 'N/A')
                        
                        pnl_percent = 0
                        if trade.entry_price > 0 and exit_price > 0:
                            pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
                        
                        # Mise à jour par batch plutôt qu'individuellement
                        range_name = f"G{i}:M{i}"
                        values = [[
                            exit_price,
                            "", "", # Colonnes H et I vides
                            pnl,
                            pnl_percent,
                            str(duration),
                            exit_reason
                        ]]
                        
                        trades_sheet.update(range_name, values)
                        break
                else:
                    # Trade non trouvé, ajouter une nouvelle ligne
                    exit_price = getattr(trade, 'exit_price', 0)
                    pnl = getattr(trade, 'pnl', 0)
                    exit_reason = getattr(trade, 'exit_reason', action)
                    duration = getattr(trade, 'duration', 'N/A')
                    
                    pnl_percent = 0
                    if trade.entry_price > 0 and exit_price > 0:
                        pnl_percent = (exit_price - trade.entry_price) / trade.entry_price * 100
                    
                    row = [
                        trade.timestamp.strftime("%Y-%m-%d"),
                        trade.timestamp.strftime("%H:%M:%S"),
                        trade.pair,
                        trade.direction.value,
                        trade.size,
                        trade.entry_price,
                        exit_price,
                        trade.stop_loss,
                        trade.take_profit,
                        pnl,
                        pnl_percent,
                        str(duration),
                        exit_reason,
                        "",  # Capital avant
                        ""   # Capital après
                    ]
                    trades_sheet.append_row(row)
            
            self.logger.info(f"📊 Trade {action} loggé dans Google Sheets - {trade.pair}")
            
        except APIError as e: # type: ignore
            if "storage quota exceeded" in str(e).lower():
                self.logger.error("❌ Quota Google Drive dépassé - Vérifiez l'espace disponible")
            elif "permission" in str(e).lower():
                self.logger.error("❌ Erreur de permissions Google Sheets - Vérifiez le partage")
            else:
                self.logger.error(f"❌ Erreur API Google Sheets: {e}")
        except Exception as e:
            self.logger.error(f"❌ Erreur log trade {action}: {e}")
            import traceback
            self.logger.debug(f"Stacktrace: {traceback.format_exc()}")

    async def log_daily_performance(self, total_capital: float, daily_pnl: float, 
                                  trades_count: int, status: str):
        """Log la performance quotidienne"""
        if not self.client:
            return
        
        try:
            perf_sheet = self.spreadsheet.worksheet("Performance") # type: ignore
            
            # Calcul des métriques basé sur le capital total dynamique
            final_capital = total_capital  # Le capital total inclut déjà les P&L
            pnl_percent = daily_pnl / total_capital * 100
            
            # Récupération des données de trades pour calculs avancés
            trades_data = await self.get_daily_trades_data()
            
            winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in trades_data if t.get('pnl', 0) < 0])
            win_rate = winning_trades / max(trades_count, 1) * 100
            
            # Calcul profit factor
            total_wins = sum(t.get('pnl', 0) for t in trades_data if t.get('pnl', 0) > 0)
            total_losses = abs(sum(t.get('pnl', 0) for t in trades_data if t.get('pnl', 0) < 0))
            profit_factor = total_wins / max(total_losses, 1)
            
            # Calcul max drawdown (simplifié)
            max_drawdown = 0.0  # À implémenter selon besoins
            
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                total_capital,  # Capital total dynamique
                final_capital,
                daily_pnl,
                pnl_percent,
                trades_count,
                winning_trades,
                losing_trades,
                win_rate,
                profit_factor,
                max_drawdown,
                status
            ]
            
            perf_sheet.append_row(row)
            
            self.logger.info("📊 Performance quotidienne loggée dans Google Sheets")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur log performance: {e}")

    async def get_daily_trades_data(self) -> List[Dict]:
        """Récupère les données des trades du jour"""
        if not self.client:
            return []
        
        try:
            trades_sheet = self.spreadsheet.worksheet("Trades") # type: ignore
            all_values = trades_sheet.get_all_values()
            
            today = datetime.now().strftime("%Y-%m-%d")
            daily_trades = []
            
            for row in all_values[1:]:  # Skip header
                if row[0] == today and row[9]:  # Date aujourd'hui et P&L non vide
                    daily_trades.append({
                        'pair': row[2],
                        'pnl': float(row[9]) if row[9] else 0,
                        'duration': row[11],
                        'reason': row[12]
                    })
            
            return daily_trades
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération données trades: {e}")
            return []

    async def log_error(self, error: str, context: str = ""):
        """Log une erreur dans Google Sheets"""
        if not self.client:
            return
        
        try:
            # Création onglet erreurs si nécessaire
            try:
                errors_sheet = self.spreadsheet.worksheet("Erreurs") # type: ignore
            except:
                errors_sheet = self.spreadsheet.add_worksheet(title="Erreurs", rows=500, cols=5) # type: ignore
                errors_sheet.append_row(["Date", "Heure", "Erreur", "Contexte", "Statut"])
            
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%H:%M:%S"),
                error,
                context,
                "NOUVEAU"
            ]
            
            errors_sheet.append_row(row)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur log erreur: {e}")

    async def update_real_time_metrics(self, current_capital: float, daily_pnl: float, 
                                     open_positions: int):
        """Met à jour les métriques en temps réel"""
        if not self.client:
            return
        
        try:
            # Mise à jour du dashboard
            dashboard_sheet = self.spreadsheet.worksheet("Dashboard") # type: ignore
            
            # Mise à jour des valeurs
            dashboard_sheet.update("B4", current_capital)  # Capital actuel
            dashboard_sheet.update("B5", daily_pnl)       # P&L Total
            dashboard_sheet.update("B6", f"{daily_pnl/current_capital*100:.2f}%")  # Performance %
            dashboard_sheet.update("B14", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # Dernière MAJ
            
        except Exception as e:
            self.logger.error(f"❌ Erreur mise à jour temps réel: {e}")

    def get_spreadsheet_url(self) -> str:
        """Retourne l'URL du spreadsheet"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        return ""

    async def export_data(self, format_type: str = "csv") -> str: # type: ignore
        """Exporte les données"""
        # À implémenter selon besoins
        pass

    async def backup_data(self) -> bool: # type: ignore
        """Sauvegarde les données"""
        # À implémenter selon besoins
        pass

# Exemple d'utilisation
async def main():
    """Test du logger Google Sheets"""
    # Configuration
    CREDENTIALS_PATH = "credentials.json"
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"
    
    logger = SheetsLogger(CREDENTIALS_PATH, SPREADSHEET_ID)
    
    print(f"📊 Spreadsheet URL: {logger.get_spreadsheet_url()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

"""
Logger Google Sheets AMÉLIORÉ pour analyse fine des performances
Version optimisée avec suivi détaillé des frais et rentabilité par paire
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

from trading_hours import get_current_trading_session, get_trading_intensity


class EnhancedSheetsLogger:
    """Gestionnaire de logging Google Sheets avec analyse fine"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str = ""):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.logger = logging.getLogger(__name__)
        
        # Configuration frais
        self.fee_rate = 0.001  # 0.1% par transaction
        
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
                self.spreadsheet = self.client.create("Trading Bot v3.0 - Analytics")
                self.spreadsheet_id = self.spreadsheet.id
                self.logger.info(f"📊 Nouveau spreadsheet créé: {self.spreadsheet_id}")
            
            # Création des onglets améliorés
            self.setup_enhanced_worksheets()
            
            self.logger.info("📊 Google Sheets Enhanced initialisé avec succès")
            
        except FileNotFoundError:
            self.logger.error(f"❌ Fichier credentials non trouvé: {self.credentials_path}")
        except json.JSONDecodeError:
            self.logger.error("❌ Fichier credentials JSON invalide")
        except APIError as e:  # type: ignore
            self.logger.error(f"❌ Erreur API Google Sheets: {e}")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Google Sheets: {e}")

    def setup_enhanced_worksheets(self):
        """Configure les onglets améliorés du spreadsheet"""
        try:
            # Récupération des onglets existants
            existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()] # type: ignore
            
            # Création onglet Trades détaillé
            if "Trades_Detailed" not in existing_sheets:
                trades_sheet = self.spreadsheet.add_worksheet(title="Trades_Detailed", rows=2000, cols=25) # type: ignore
                self.setup_enhanced_trades_headers(trades_sheet)
            
            # Création onglet Performance par paire
            if "Performance_Pairs" not in existing_sheets:
                pairs_sheet = self.spreadsheet.add_worksheet(title="Performance_Pairs", rows=50, cols=15)  # type: ignore
                self.setup_pairs_performance_headers(pairs_sheet)
            
            # Création onglet Analyse horaire
            if "Hourly_Analysis" not in existing_sheets:
                hourly_sheet = self.spreadsheet.add_worksheet(title="Hourly_Analysis", rows=25, cols=12) # type: ignore
                self.setup_hourly_analysis_headers(hourly_sheet)
            
            # Création onglet Dashboard Analytics
            if "Analytics_Dashboard" not in existing_sheets:
                dash_sheet = self.spreadsheet.add_worksheet(title="Analytics_Dashboard", rows=30, cols=8) # type: ignore
                self.setup_analytics_dashboard(dash_sheet)
            
            # Suppression de l'onglet par défaut si nécessaire
            if "Feuille 1" in existing_sheets:
                self.spreadsheet.del_worksheet(self.spreadsheet.worksheet("Feuille 1")) # type: ignore
                
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration onglets: {e}")

    def setup_enhanced_trades_headers(self, sheet):
        """Configure les en-têtes détaillés de l'onglet Trades"""
        headers = [
            "Date", "Heure", "Paire", "Direction", "Taille (USDC)", 
            "Prix Entrée", "Prix Sortie", "Stop Loss", "Take Profit", 
            "P&L Brut (USDC)", "Frais Entrée (USDC)", "Frais Sortie (USDC)", 
            "Frais Total (USDC)", "P&L Net (USDC)", "P&L %", "ROI Net %", 
            "Durée", "Raison Sortie", "Capital Avant", "Capital Après", 
            "Session Trading", "Intensité Horaire", "Volatilité Paire", 
            "Volume 24h", "Spread %"
        ]
        
        sheet.append_row(headers)
        
        # Formatage des en-têtes
        sheet.format("A1:Y1", {
            "backgroundColor": {"red": 0.1, "green": 0.3, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })

    def setup_pairs_performance_headers(self, sheet):
        """Configure les en-têtes de performance par paire"""
        headers = [
            "Paire", "Nb Trades", "Volume Total (USDC)", "P&L Brut (USDC)", 
            "Frais Total (USDC)", "P&L Net (USDC)", "Win Rate %", 
            "Profit Factor", "ROI Net %", "Frais/Volume %", "Durée Moy (min)", 
            "Score Rentabilité", "Priorité", "Dernière MAJ"
        ]
        
        sheet.append_row(headers)
        
        # Ajout des formules pour chaque paire prioritaire
        priority_pairs = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC', 'XRPUSDC', 'DOGEUSDC', 
                         'ADAUSDC', 'MATICUSDC', 'LTCUSDC', 'LINKUSDC', 'DOTUSDC']
        
        for i, pair in enumerate(priority_pairs, 2):
            formula_row = [
                pair,
                f'=COUNTIF(Trades_Detailed!C:C,"{pair}")',  # Nb trades
                f'=SUMIF(Trades_Detailed!C:C,"{pair}",Trades_Detailed!E:E)',  # Volume
                f'=SUMIF(Trades_Detailed!C:C,"{pair}",Trades_Detailed!J:J)',  # P&L Brut
                f'=SUMIF(Trades_Detailed!C:C,"{pair}",Trades_Detailed!M:M)',  # Frais
                f'=SUMIF(Trades_Detailed!C:C,"{pair}",Trades_Detailed!N:N)',  # P&L Net
                f'=IFERROR(COUNTIFS(Trades_Detailed!C:C,"{pair}",Trades_Detailed!N:N,">0")/COUNTIF(Trades_Detailed!C:C,"{pair}"),0)',  # Win Rate
                f'=IFERROR(SUMIFS(Trades_Detailed!N:N,Trades_Detailed!C:C,"{pair}",Trades_Detailed!N:N,">0")/ABS(SUMIFS(Trades_Detailed!N:N,Trades_Detailed!C:C,"{pair}",Trades_Detailed!N:N,"<0")),0)',  # Profit Factor
                f'=IFERROR(F{i}/C{i},0)',  # ROI Net %
                f'=IFERROR(E{i}/C{i},0)',  # Frais/Volume %
                f'=IFERROR(AVERAGEIF(Trades_Detailed!C:C,"{pair}",Trades_Detailed!Q:Q),0)',  # Durée moyenne
                f'=IFERROR((F{i}/C{i})*(G{i}/100),0)',  # Score rentabilité
                f'=IF(L{i}>0.5,"HIGH",IF(L{i}>0.2,"MEDIUM","LOW"))',  # Priorité
                '=NOW()'  # Dernière MAJ
            ]
            sheet.append_row(formula_row)
        
        # Formatage
        sheet.format("A1:N1", {
            "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.1},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    def setup_hourly_analysis_headers(self, sheet):
        """Configure l'analyse horaire"""
        headers = [
            "Heure", "Session", "Nb Trades", "Volume (USDC)", "P&L Net (USDC)", 
            "Frais (USDC)", "Win Rate %", "ROI Horaire %", "Intensité", 
            "Score Session"
        ]
        
        sheet.append_row(headers)
        
        # Ajout des données pour chaque heure
        for hour in range(24):
            hour_str = f"{hour:02d}:00:00"
            next_hour_str = f"{hour+1:02d}:00:00" if hour < 23 else "23:59:59"
            
            # Détermination de la session
            if 9 <= hour < 12:
                session = "EU_MORNING"
                intensity = "100%"
            elif 15 <= hour < 18:
                session = "EU_US_OVERLAP"
                intensity = "100%"
            elif 18 <= hour < 21:
                session = "US_PRIME"  
                intensity = "100%"
            elif 12 <= hour < 14:
                session = "LUNCH_BREAK"
                intensity = "50%"
            else:
                session = "NORMAL"
                intensity = "70%"
            
            row = [
                f"{hour:02d}h",
                session,
                f'=COUNTIFS(Trades_Detailed!B:B,">={hour_str}",Trades_Detailed!B:B,"<{next_hour_str}")',
                f'=SUMIFS(Trades_Detailed!E:E,Trades_Detailed!B:B,">={hour_str}",Trades_Detailed!B:B,"<{next_hour_str}")',
                f'=SUMIFS(Trades_Detailed!N:N,Trades_Detailed!B:B,">={hour_str}",Trades_Detailed!B:B,"<{next_hour_str}")',
                f'=SUMIFS(Trades_Detailed!M:M,Trades_Detailed!B:B,">={hour_str}",Trades_Detailed!B:B,"<{next_hour_str}")',
                f'=IFERROR(COUNTIFS(Trades_Detailed!B:B,">={hour_str}",Trades_Detailed!B:B,"<{next_hour_str}",Trades_Detailed!N:N,">0")/C{hour+2},0)',
                f'=IFERROR(E{hour+2}/D{hour+2},0)',
                intensity,
                f'=IFERROR(E{hour+2}*G{hour+2}/100,0)'
            ]
            sheet.append_row(row)
        
        # Formatage
        sheet.format("A1:J1", {
            "backgroundColor": {"red": 0.2, "green": 0.7, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    def setup_analytics_dashboard(self, sheet):
        """Configure le dashboard d'analytics"""
        dashboard_data = [
            ["🔥 TRADING BOT v3.0 - ANALYTICS DASHBOARD", ""],
            ["", ""],
            ["💰 MÉTRIQUES FINANCIÈRES", ""],
            ["Capital Initial", "22819.00"],
            ["Capital Actuel", "=MAX(Trades_Detailed!T:T)"],
            ["P&L Total Net", "=SUM(Trades_Detailed!N:N)"],
            ["Frais Total", "=SUM(Trades_Detailed!M:M)"],
            ["ROI Global %", "=IFERROR((E5-D4)/D4*100,0)"],
            ["", ""],
            ["📊 MÉTRIQUES TRADING", ""],
            ["Total Trades", "=COUNTA(Trades_Detailed!C:C)-1"],
            ["Win Rate %", "=IFERROR(COUNTIF(Trades_Detailed!N:N,\">0\")/(D11)*100,0)"],
            ["Profit Factor", "=IFERROR(SUMIF(Trades_Detailed!N:N,\">0\",Trades_Detailed!N:N)/ABS(SUMIF(Trades_Detailed!N:N,\"<0\",Trades_Detailed!N:N)),0)"],
            ["Ratio Frais/Volume", "=IFERROR(D7/SUM(Trades_Detailed!E:E)*100,0)"],
            ["", ""],
            ["🏆 TOP PAIRES", ""],
            ["Meilleure paire", "=INDEX(Performance_Pairs!A:A,MATCH(MAX(Performance_Pairs!F:F),Performance_Pairs!F:F,0))"],
            ["P&L meilleure", "=MAX(Performance_Pairs!F:F)"],
            ["Pire paire", "=INDEX(Performance_Pairs!A:A,MATCH(MIN(Performance_Pairs!F:F),Performance_Pairs!F:F,0))"],
            ["P&L pire", "=MIN(Performance_Pairs!F:F)"],
            ["", ""],
            ["⏰ PERFORMANCE HORAIRE", ""],
            ["Meilleure heure", "=INDEX(Hourly_Analysis!A:A,MATCH(MAX(Hourly_Analysis!E:E),Hourly_Analysis!E:E,0))"],
            ["P&L meilleure heure", "=MAX(Hourly_Analysis!E:E)"],
            ["", ""],
            ["🎯 RECOMMANDATIONS", ""],
            ["Focus sur paires", "=TEXTJOIN(\", \",TRUE,IF(Performance_Pairs!M:M=\"HIGH\",Performance_Pairs!A:A,\"\"))"],
            ["Éviter paires", "=TEXTJOIN(\", \",TRUE,IF(Performance_Pairs!M:M=\"LOW\",Performance_Pairs!A:A,\"\"))"],
            ["Dernière MAJ", "=NOW()"]
        ]
        
        for row in dashboard_data:
            sheet.append_row(row)
        
        # Formatage du titre
        sheet.format("A1:B1", {
            "backgroundColor": {"red": 0.9, "green": 0.1, "blue": 0.1},
            "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        
        # Formatage des sections
        sheet.format("A3", {
            "backgroundColor": {"red": 0.1, "green": 0.8, "blue": 0.1},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    async def log_enhanced_trade(self, trade, action: str, capital_before: float = 0, 
                                capital_after: float = 0, pair_volatility: float = 0,
                                volume_24h: str = "", spread_percent: float = 0):
        """Log un trade avec toutes les métriques d'analyse"""
        if not self.client:
            self.logger.warning("⚠️ Google Sheets non initialisé - trade non loggé")
            return
        
        try:
            trades_sheet = self.spreadsheet.worksheet("Trades_Detailed") # type: ignore
            
            if action == "OPEN":
                # Calcul des frais d'entrée
                entry_fee = trade.size * self.fee_rate
                
                # Session et intensité actuelles
                from config import TradingConfig
                config = TradingConfig()
                session = get_current_trading_session()
                intensity = get_trading_intensity(config) * 100
                
                # Log d'ouverture complet
                row = [
                    trade.timestamp.strftime("%Y-%m-%d"),
                    trade.timestamp.strftime("%H:%M:%S"),
                    trade.pair,
                    trade.direction.value,
                    f"{trade.size:.2f}",
                    f"{trade.entry_price:.6f}",
                    "",  # Prix sortie vide
                    f"{trade.stop_loss:.6f}",
                    f"{trade.take_profit:.6f}",
                    "",  # P&L brut vide
                    f"{entry_fee:.4f}",  # Frais entrée
                    "",  # Frais sortie vide
                    "",  # Frais total vide
                    "",  # P&L net vide
                    "",  # P&L % vide
                    "",  # ROI net % vide
                    "",  # Durée vide
                    "OUVERT",  # Statut
                    f"{capital_before:.2f}",
                    f"{capital_after:.2f}",
                    session,
                    f"{intensity:.0f}%",
                    f"{pair_volatility:.2f}%" if pair_volatility else "",
                    volume_24h,
                    f"{spread_percent:.3f}%" if spread_percent else ""
                ]
                
                trades_sheet.append_row(row)
                self.logger.debug(f"📊 Trade OPEN détaillé loggé: {trade.pair}")
            
            elif action in ["CLOSE", "CLOSE_VIRTUAL"]:
                # Recherche et mise à jour du trade
                all_values = trades_sheet.get_all_values()
                
                for i, row in enumerate(all_values[1:], 2):  # Skip header
                    if (len(row) >= 3 and 
                        row[1] == trade.timestamp.strftime("%H:%M:%S") and 
                        row[2] == trade.pair and
                        row[17] == "OUVERT"):  # Statut ouvert
                        
                        # Calcul des métriques complètes
                        exit_price = getattr(trade, 'exit_price', 0)
                        pnl_gross = getattr(trade, 'pnl', 0)
                        exit_reason = getattr(trade, 'exit_reason', action)
                        duration = getattr(trade, 'duration', 'N/A')
                        
                        # Calcul des frais
                        entry_fee = float(row[10]) if row[10] else trade.size * self.fee_rate
                        exit_value = trade.size * (exit_price / trade.entry_price) if trade.entry_price > 0 else 0
                        exit_fee = exit_value * self.fee_rate
                        total_fees = entry_fee + exit_fee
                        
                        # P&L net et pourcentages
                        pnl_net = pnl_gross - total_fees
                        pnl_percent = (pnl_gross / trade.size) * 100 if trade.size > 0 else 0
                        roi_net_percent = (pnl_net / trade.size) * 100 if trade.size > 0 else 0
                        
                        # Durée en minutes
                        duration_minutes = duration.total_seconds() / 60 if hasattr(duration, 'total_seconds') else 0 # type: ignore
                        
                        # Mise à jour complète de la ligne
                        range_name = f"G{i}:Y{i}"
                        values = [[
                            f"{exit_price:.6f}",           # G: Prix sortie
                            f"{trade.stop_loss:.6f}",      # H: Stop Loss (mis à jour)
                            f"{trade.take_profit:.6f}",    # I: Take Profit (mis à jour)
                            f"{pnl_gross:.4f}",            # J: P&L brut
                            f"{entry_fee:.4f}",            # K: Frais entrée
                            f"{exit_fee:.4f}",             # L: Frais sortie
                            f"{total_fees:.4f}",           # M: Frais total
                            f"{pnl_net:.4f}",              # N: P&L net
                            f"{pnl_percent:.2f}",          # O: P&L %
                            f"{roi_net_percent:.2f}",      # P: ROI net %
                            f"{duration_minutes:.0f}",     # Q: Durée (min)
                            exit_reason,                    # R: Raison sortie
                            f"{capital_before:.2f}",       # S: Capital avant
                            f"{capital_after:.2f}",        # T: Capital après
                            row[20] if len(row) > 20 else "",  # U: Session (conservé)
                            row[21] if len(row) > 21 else "",  # V: Intensité (conservé)
                            f"{pair_volatility:.2f}%" if pair_volatility else (row[22] if len(row) > 22 else ""),  # W: Volatilité
                            volume_24h if volume_24h else (row[23] if len(row) > 23 else ""),  # X: Volume 24h
                            f"{spread_percent:.3f}%" if spread_percent else (row[24] if len(row) > 24 else "")   # Y: Spread
                        ]]
                        
                        trades_sheet.update(range_name, values)
                        self.logger.debug(f"📊 Trade CLOSE détaillé mis à jour: {trade.pair} (P&L Net: {pnl_net:.2f})")
                        break
                else:
                    self.logger.warning(f"⚠️ Trade ouvert non trouvé pour mise à jour: {trade.pair}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur logging trade enhanced {action}: {e}")
        
        # NOUVEAU: Force le recalcul automatique après chaque trade (avec gestion d'erreur)
        try:
            await self.force_calculations_after_trade()
        except APIError as e: # type: ignore
            self.logger.warning(f"⚠️ Erreur API Google Sheets (recalcul): {e}")
            # Ne pas interrompre le trading pour des erreurs Sheets
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur recalcul automatique: {e}")
            # Continuer le trading même si Sheets a des problèmes

    async def force_calculations_after_trade(self):
        """Force le recalcul des métriques après ajout d'un trade"""
        try:
            # Récupérer les données actuelles
            trades_sheet = self.spreadsheet.worksheet("Trades_Detailed") # type: ignore
            all_data = trades_sheet.get_all_values()
            
            if len(all_data) <= 1:  # Pas de trades
                return
            
            trades_data = all_data[1:]  # Skip header
            
            # 1. Mise à jour Performance_Summary
            summary_sheet = self.spreadsheet.worksheet("Performance_Summary") # type: ignore
            
            total_trades = len(trades_data)
            
            # Calcul P&L Net (colonne N = index 13)
            pnl_values = []
            for row in trades_data:
                if len(row) > 13 and row[13]:  # P&L Net non vide
                    try:
                        pnl_values.append(float(row[13]))
                    except:
                        pass
            
            total_pnl = sum(pnl_values)
            winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
            losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Mise à jour rapide des métriques principales avec gestion d'erreur
            try:
                summary_sheet.update('B4', [[total_trades]])
                summary_sheet.update('B5', [[winning_trades]])
                summary_sheet.update('B6', [[losing_trades]])
                summary_sheet.update('B7', [[f"{win_rate:.1f}"]])
                summary_sheet.update('B8', [[f"{total_pnl:.2f}"]])
                self.logger.debug("📊 Métriques Performance_Summary mises à jour")
            except APIError as e: # type: ignore
                self.logger.warning(f"⚠️ Erreur mise à jour métriques summary: {e}")
                # Fallback : mise à jour par batch
                try:
                    summary_values = [
                        [total_trades],
                        [winning_trades], 
                        [losing_trades],
                        [f"{win_rate:.1f}"],
                        [f"{total_pnl:.2f}"]
                    ]
                    summary_sheet.update('B4:B8', summary_values)
                    self.logger.debug("📊 Métriques summary mises à jour en batch")
                except Exception as fallback_error:
                    self.logger.error(f"❌ Erreur fallback mise à jour summary: {fallback_error}")
            
            # 2. Mise à jour Pairs_Analysis pour les paires actives
            pairs_sheet = self.spreadsheet.worksheet("Pairs_Analysis") # type: ignore
            
            # Identifier les paires qui ont des trades
            active_pairs = set()
            for row in trades_data:
                if len(row) > 2 and row[2]:
                    active_pairs.add(row[2])
            
            # Mettre à jour seulement les paires actives (plus rapide)
            pair_row_mapping = {
                'BTCUSDC': 2, 'ETHUSDC': 3, 'SOLUSDC': 4, 'XRPUSDC': 5, 'DOGEUSDC': 6,
                'ADAUSDC': 7, 'MATICUSDC': 8, 'LTCUSDC': 9, 'LINKUSDC': 10, 'DOTUSDC': 11
            }
            
            for pair in active_pairs:
                if pair in pair_row_mapping:
                    row_num = pair_row_mapping[pair]
                    
                    # Calculer pour cette paire
                    pair_trades = [row for row in trades_data if len(row) > 2 and row[2] == pair]
                    
                    if pair_trades:
                        nb_trades = len(pair_trades)
                        
                        # P&L Net pour cette paire
                        pair_pnl_values = []
                        for row in pair_trades:
                            if len(row) > 13 and row[13]:
                                try:
                                    pair_pnl_values.append(float(row[13]))
                                except:
                                    pass
                        
                        if pair_pnl_values:
                            total_pnl_pair = sum(pair_pnl_values)
                            winning_pair = len([pnl for pnl in pair_pnl_values if pnl > 0])
                            win_rate_pair = (winning_pair / nb_trades * 100) if nb_trades > 0 else 0
                            
                            # Recommandation
                            recommendation = "HIGH" if win_rate_pair > 60 else "MEDIUM" if win_rate_pair > 30 else "LOW"
                            
                            # Mise à jour rapide avec format liste correct
                            try:
                                pairs_sheet.update(f'B{row_num}', [[nb_trades]])
                                pairs_sheet.update(f'C{row_num}', [[f"{win_rate_pair:.1f}"]])
                                pairs_sheet.update(f'D{row_num}', [[f"{total_pnl_pair:.2f}"]])
                                pairs_sheet.update(f'I{row_num}', [[recommendation]])
                            except APIError as e: # type: ignore
                                self.logger.warning(f"⚠️ Erreur mise à jour paire {pair}: {e}")
                                # Fallback : mise à jour par batch
                                try:
                                    pair_values = [
                                        [nb_trades, f"{win_rate_pair:.1f}", f"{total_pnl_pair:.2f}", "", "", "", "", "", recommendation]
                                    ]
                                    pairs_sheet.update(f'B{row_num}:J{row_num}', pair_values)
                                except Exception:
                                    self.logger.warning(f"⚠️ Impossible de mettre à jour {pair}")
                                    pass
            
            self.logger.debug("📊 Recalcul automatique effectué")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur recalcul automatique: {e}")

    def get_pair_performance_summary(self):
        """Récupère le résumé de performance par paire"""
        try: 
            pairs_sheet = self.spreadsheet.worksheet("Performance_Pairs") # type: ignore
            data = pairs_sheet.get_all_values()
            
            summary = {}
            for row in data[1:]:  # Skip header
                if len(row) >= 12 and row[0]:  # Paire non vide
                    summary[row[0]] = {
                        'trades': row[1],
                        'volume': row[2], 
                        'pnl_net': row[5],
                        'win_rate': row[6],
                        'score': row[11],
                        'priority': row[12]
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération summary: {e}")
            return {}

    # ============================================================================
    # MÉTHODES DE COMPATIBILITÉ AVEC L'ANCIEN SYSTÈME
    # ============================================================================
    
    async def log_trade(self, trade, action: str, capital_before: float = 0, capital_after: float = 0):
        """Méthode de compatibilité - redirige vers log_enhanced_trade"""
        await self.log_enhanced_trade(
            trade=trade,
            action=action,
            capital_before=capital_before,
            capital_after=capital_after,
            pair_volatility=0.0,  # Valeurs par défaut
            volume_24h="",
            spread_percent=0.0
        )
    
    async def log_daily_performance(self, total_capital: float, daily_pnl: float, 
                                  trades_count: int, status: str):
        """Méthode de compatibilité - log simple pour rétrocompatibilité"""
        self.logger.info(f"📊 Performance quotidienne: Capital={total_capital:.2f}, P&L={daily_pnl:.2f}, Trades={trades_count}")
        # L'Enhanced Logger gère automatiquement les performances via les formules
        # Pas besoin de log supplémentaire car tout est calculé en temps réel
    
    def get_spreadsheet_url(self) -> str:
        """Retourne l'URL du spreadsheet"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        return ""

if __name__ == "__main__":
    print("📊 Enhanced Google Sheets Logger pour Trading Bot v3.0")
    print("✅ Prêt pour analyse fine des performances et frais par paire")

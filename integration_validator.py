#!/usr/bin/env python3
"""
Patch d'intégration du validateur de trades dans main.py
"""

VALIDATION_CODE = '''
# === TRADE VALIDATOR INTEGRATION ===
class TradeValidator:
    """Validateur pour détecter et bloquer les trades aberrants"""
    
    def __init__(self, max_loss_threshold=100, max_loss_percentage=0.02):
        self.max_loss_threshold = max_loss_threshold
        self.max_loss_percentage = max_loss_percentage
    
    def validate_trade_data(self, trade_data):
        """Valide les données d'un trade avant enregistrement"""
        errors = []
        warnings = []
        
        # Validation des champs obligatoires
        required_fields = ['pair', 'pnl_usdc', 'capital_before', 'capital_after', 'trade_count']
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        if errors:
            return False, errors, warnings
        
        # Validation des valeurs
        pnl = trade_data['pnl_usdc']
        capital_before = trade_data['capital_before']
        capital_after = trade_data['capital_after']
        
        # 1. Vérifier cohérence capital_before + pnl = capital_after
        expected_capital_after = capital_before + pnl
        diff = abs(capital_after - expected_capital_after)
        if diff > 0.01:  # Tolérance de 1 centime
            errors.append(f"Incohérence capital: {capital_before} + {pnl} ≠ {capital_after} (diff: {diff:.6f})")
        
        # 2. Vérifier seuils de perte
        if pnl < -self.max_loss_threshold:
            errors.append(f"Perte excessive: {pnl:.2f} USDC > seuil {self.max_loss_threshold} USDC")
        
        # 3. Vérifier pourcentage de perte
        if capital_before > 0:
            loss_percentage = abs(pnl) / capital_before
            if pnl < 0 and loss_percentage > self.max_loss_percentage:
                errors.append(f"Perte % excessive: {loss_percentage*100:.2f}% > seuil {self.max_loss_percentage*100:.2f}%")
        
        # 4. Vérifier valeurs positives
        if capital_before <= 0:
            errors.append(f"Capital_before invalide: {capital_before}")
        if capital_after <= 0:
            errors.append(f"Capital_after invalide: {capital_after}")
        
        # Warnings
        if abs(pnl) > 50:
            warnings.append(f"P&L élevé: {pnl:.2f} USDC")
        
        return len(errors) == 0, errors, warnings
    
    def safe_log_trade(self, db, trade_data):
        """Log un trade de manière sécurisée avec validation"""
        is_valid, errors, warnings = self.validate_trade_data(trade_data)
        
        if warnings:
            print(f"⚠️ TRADE WARNING - {trade_data.get('pair')}: {warnings}")
        
        if not is_valid:
            # Sauvegarder dans une collection séparée
            quarantine_data = {
                **trade_data,
                'validation_errors': errors,
                'validation_warnings': warnings,
                'quarantine_timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'QUARANTINED'
            }
            
            db.collection('quarantined_trades').add(quarantine_data)
            print(f"🚨 TRADE ABERRANT DÉTECTÉ - {trade_data.get('pair')}: {errors}")
            print(f"🔒 Trade mis en quarantaine pour investigation")
            
            # Envoyer alerte Telegram si disponible
            if hasattr(self, 'send_telegram_alert'):
                self.send_telegram_alert(f"🚨 TRADE ABERRANT: {trade_data.get('pair')} - {errors}")
            
            return False
        
        # Trade valide - enregistrer normalement
        try:
            db.collection('trades').add(trade_data)
            print(f"✅ Trade validé et enregistré: {trade_data.get('pair')} - P&L: {trade_data.get('pnl_usdc'):.2f} USDC")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement: {e}")
            return False

# Instance globale du validateur
trade_validator = TradeValidator(max_loss_threshold=100, max_loss_percentage=0.02)
'''

PROTECTED_LOG_FUNCTION = '''
def log_trade_to_firebase_protected(pair, total_trades, pnl_usdc, capital_before, capital_after, 
                                  trade_details=None, daily_pnl=None, positions_today=None):
    """Version protégée de log_trade_to_firebase avec validation"""
    try:
        # Préparer les données du trade
        trade_data = {
            'pair': pair,
            'trade_count': total_trades,
            'pnl_usdc': round(pnl_usdc, 4),
            'capital_before': round(capital_before, 2),
            'capital_after': round(capital_after, 2),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'daily_pnl': round(daily_pnl if daily_pnl is not None else pnl_usdc, 4),
            'positions_today': positions_today if positions_today is not None else total_trades
        }
        
        # Ajouter les détails de trade si fournis
        if trade_details:
            trade_data.update(trade_details)
        
        # Validation et enregistrement sécurisé
        db = firestore.client()
        success = trade_validator.safe_log_trade(db, trade_data)
        
        if success:
            print(f"📊 Trade {pair} enregistré: {total_trades} trades, P&L: {pnl_usdc:.2f} USDC")
        else:
            print(f"🚫 Trade {pair} REJETÉ par validation")
            
        return success
        
    except Exception as e:
        print(f"❌ Erreur lors du logging protégé: {e}")
        return False
'''

def create_integration_instructions():
    """Crée les instructions d'intégration"""
    print("🔧 INSTRUCTIONS D'INTÉGRATION DU VALIDATEUR")
    print("=" * 60)
    
    print("\n1. 📋 AJOUT DU CODE DE VALIDATION:")
    print("   - Ajouter la classe TradeValidator au début de main.py")
    print("   - Créer l'instance globale trade_validator")
    
    print("\n2. 🔄 REMPLACEMENT DES APPELS:")
    print("   - Remplacer log_trade_to_firebase() par log_trade_to_firebase_protected()")
    print("   - Ou modifier log_trade_to_firebase() pour utiliser le validateur")
    
    print("\n3. 📊 SURVEILLANCE:")
    print("   - Les trades aberrants seront mis en quarantaine")
    print("   - Collection 'quarantined_trades' créée automatiquement")
    print("   - Logs détaillés des validations")
    
    print("\n4. ⚙️ CONFIGURATION:")
    print("   - Seuil perte max: 100 USDC (modifiable)")
    print("   - Seuil perte %: 2% du capital (modifiable)")
    print("   - Validation cohérence capital_before + pnl = capital_after")
    
    print("\n5. 🚨 ALERTES:")
    print("   - Trades suspects: warnings dans les logs")
    print("   - Trades aberrants: rejetés et quarantinés")
    print("   - Possibilité d'ajout d'alertes Telegram")
    
    print("\n" + "=" * 60)
    print("✅ Prêt pour intégration")

if __name__ == "__main__":
    create_integration_instructions()
    
    print("\n📝 CODE À INTÉGRER DANS MAIN.PY:")
    print("=" * 60)
    print(VALIDATION_CODE)
    print("\n" + "=" * 60)
    print("📝 FONCTION PROTÉGÉE À UTILISER:")
    print("=" * 60)
    print(PROTECTED_LOG_FUNCTION)

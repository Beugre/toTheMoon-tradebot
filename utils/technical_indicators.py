"""
Analyseur d'indicateurs techniques
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import talib


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

@dataclass
class TechnicalSignal:
    """Signal technique"""
    indicator: str
    condition: str
    value: float
    strength: SignalStrength
    description: str

@dataclass
class MarketAnalysis:
    """Analyse complète du marché"""
    pair: str
    signals: List[TechnicalSignal]
    total_score: float
    recommendation: str
    trend: str
    momentum: str
    volatility: str

class TechnicalAnalyzer:
    """Analyseur technique avancé"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("📊 Analyseur technique initialisé")

    def analyze_pair(self, df: pd.DataFrame, pair: str) -> MarketAnalysis:
        """Analyse technique complète d'une paire"""
        
        signals = []
        
        # Analyse des moyennes mobiles
        ema_signals = self.analyze_ema(df)
        signals.extend(ema_signals)
        
        # Analyse MACD
        macd_signals = self.analyze_macd(df)
        signals.extend(macd_signals)
        
        # Analyse RSI
        rsi_signals = self.analyze_rsi(df)
        signals.extend(rsi_signals)
        
        # Analyse Bollinger Bands
        bb_signals = self.analyze_bollinger_bands(df)
        signals.extend(bb_signals)
        
        # Analyse du volume
        volume_signals = self.analyze_volume(df)
        signals.extend(volume_signals)
        
        # Analyse des chandeliers
        candle_signals = self.analyze_candlesticks(df)
        signals.extend(candle_signals)
        
        # Calcul du score total
        total_score = sum(signal.strength.value for signal in signals)
        
        # Détermination de la recommandation
        recommendation = self.get_recommendation(total_score, len(signals))
        
        # Analyse de tendance
        trend = self.analyze_trend(df)
        momentum = self.analyze_momentum(df)
        volatility = self.analyze_volatility(df)
        
        return MarketAnalysis(
            pair=pair,
            signals=signals,
            total_score=total_score,
            recommendation=recommendation,
            trend=trend,
            momentum=momentum,
            volatility=volatility
        )

    def analyze_ema(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse des moyennes mobiles exponentielles"""
        signals = []
        
        try:
            # Calcul EMA 9 et 21
            ema9 = talib.EMA(df['close'], timeperiod=9) # type: ignore
            ema21 = talib.EMA(df['close'], timeperiod=21) # type: ignore
            
            current_price = df['close'].iloc[-1]
            current_ema9 = ema9.iloc[-1]
            current_ema21 = ema21.iloc[-1]
            
            # Signal 1: EMA9 > EMA21 (tendance haussière)
            if current_ema9 > current_ema21:
                strength = SignalStrength.STRONG if current_ema9 > current_ema21 * 1.002 else SignalStrength.MODERATE
                signals.append(TechnicalSignal(
                    indicator="EMA",
                    condition="EMA9 > EMA21",
                    value=current_ema9 - current_ema21,
                    strength=strength,
                    description=f"EMA9 ({current_ema9:.4f}) > EMA21 ({current_ema21:.4f})"
                ))
            
            # Signal 2: Prix au-dessus des EMAs
            if current_price > current_ema9 and current_price > current_ema21:
                signals.append(TechnicalSignal(
                    indicator="EMA",
                    condition="Prix > EMAs",
                    value=current_price - max(current_ema9, current_ema21),
                    strength=SignalStrength.MODERATE,
                    description=f"Prix ({current_price:.4f}) au-dessus des EMAs"
                ))
            
            # Signal 3: Croisement récent
            if len(ema9) > 2 and len(ema21) > 2:
                prev_ema9 = ema9.iloc[-2]
                prev_ema21 = ema21.iloc[-2]
                
                if prev_ema9 <= prev_ema21 and current_ema9 > current_ema21:
                    signals.append(TechnicalSignal(
                        indicator="EMA",
                        condition="Croisement Golden Cross",
                        value=current_ema9 - current_ema21,
                        strength=SignalStrength.VERY_STRONG,
                        description="Croisement haussier EMA9/EMA21"
                    ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse EMA: {e}")
        
        return signals

    def analyze_macd(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse MACD"""
        signals = []
        
        try:
            # Calcul MACD
            macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9) # type: ignore
            
            if len(macd) > 1 and not np.isnan(macd.iloc[-1]):
                current_macd = macd.iloc[-1]
                current_signal = macdsignal.iloc[-1]
                current_hist = macdhist.iloc[-1]
                
                # Signal 1: MACD > Signal Line
                if current_macd > current_signal:
                    strength = SignalStrength.STRONG if current_hist > 0 else SignalStrength.MODERATE
                    signals.append(TechnicalSignal(
                        indicator="MACD",
                        condition="MACD > Signal",
                        value=current_macd - current_signal,
                        strength=strength,
                        description=f"MACD ({current_macd:.6f}) > Signal ({current_signal:.6f})"
                    ))
                
                # Signal 2: MACD au-dessus de 0
                if current_macd > 0:
                    signals.append(TechnicalSignal(
                        indicator="MACD",
                        condition="MACD > 0",
                        value=current_macd,
                        strength=SignalStrength.MODERATE,
                        description=f"MACD positif ({current_macd:.6f})"
                    ))
                
                # Signal 3: Histogramme croissant
                if len(macdhist) > 2:
                    prev_hist = macdhist.iloc[-2]
                    if current_hist > prev_hist:
                        signals.append(TechnicalSignal(
                            indicator="MACD",
                            condition="Histogramme croissant",
                            value=current_hist - prev_hist,
                            strength=SignalStrength.WEAK,
                            description="Momentum en amélioration"
                        ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse MACD: {e}")
        
        return signals

    def analyze_rsi(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse RSI"""
        signals = []
        
        try:
            # Calcul RSI
            rsi = talib.RSI(df['close'], timeperiod=14) # type: ignore
            
            if len(rsi) > 1 and not np.isnan(rsi.iloc[-1]):
                current_rsi = rsi.iloc[-1]
                
                # Signal 1: RSI en zone de rebond (pour long)
                if current_rsi < 40:
                    strength = SignalStrength.STRONG if current_rsi < 30 else SignalStrength.MODERATE
                    signals.append(TechnicalSignal(
                        indicator="RSI",
                        condition="RSI < 40",
                        value=40 - current_rsi,
                        strength=strength,
                        description=f"RSI en zone de rebond ({current_rsi:.1f})"
                    ))
                
                # Signal 2: RSI sortant de survente
                if len(rsi) > 2:
                    prev_rsi = rsi.iloc[-2]
                    if prev_rsi < 30 and current_rsi > 30:
                        signals.append(TechnicalSignal(
                            indicator="RSI",
                            condition="RSI sortant de survente",
                            value=current_rsi - 30,
                            strength=SignalStrength.STRONG,
                            description=f"RSI sortant de survente ({current_rsi:.1f})"
                        ))
                
                # Signal 3: RSI dans zone neutre favorable
                if 40 <= current_rsi <= 60:
                    signals.append(TechnicalSignal(
                        indicator="RSI",
                        condition="RSI neutre",
                        value=50 - abs(current_rsi - 50),
                        strength=SignalStrength.WEAK,
                        description=f"RSI en zone neutre ({current_rsi:.1f})"
                    ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse RSI: {e}")
        
        return signals

    def analyze_bollinger_bands(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse des Bollinger Bands"""
        signals = []
        
        try:
            # Calcul Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2) # type: ignore
            
            if len(bb_lower) > 0 and not np.isnan(bb_lower.iloc[-1]):
                current_price = df['close'].iloc[-1]
                current_upper = bb_upper.iloc[-1]
                current_middle = bb_middle.iloc[-1]
                current_lower = bb_lower.iloc[-1]
                
                # Signal 1: Prix proche ou touche bande inférieure
                distance_to_lower = abs(current_price - current_lower) / current_lower
                if distance_to_lower <= 0.005:  # 0.5% de marge
                    strength = SignalStrength.VERY_STRONG if distance_to_lower <= 0.002 else SignalStrength.STRONG
                    signals.append(TechnicalSignal(
                        indicator="Bollinger",
                        condition="Prix proche BB inférieure",
                        value=current_lower - current_price,
                        strength=strength,
                        description=f"Prix près de BB inf. ({current_price:.4f} vs {current_lower:.4f})"
                    ))
                
                # Signal 2: Bandes qui se resserrent (faible volatilité)
                if len(bb_upper) > 2:
                    prev_upper = bb_upper.iloc[-2]
                    prev_lower = bb_lower.iloc[-2]
                    
                    current_width = (current_upper - current_lower) / current_middle
                    prev_width = (prev_upper - prev_lower) / bb_middle.iloc[-2]
                    
                    if current_width < prev_width * 0.95:
                        signals.append(TechnicalSignal(
                            indicator="Bollinger",
                            condition="Bandes se resserrent",
                            value=prev_width - current_width,
                            strength=SignalStrength.WEAK,
                            description="Volatilité en baisse - potentiel breakout"
                        ))
                
                # Signal 3: Prix au-dessus de la moyenne mobile
                if current_price > current_middle:
                    signals.append(TechnicalSignal(
                        indicator="Bollinger",
                        condition="Prix > BB moyenne",
                        value=current_price - current_middle,
                        strength=SignalStrength.WEAK,
                        description=f"Prix au-dessus BB moyenne ({current_price:.4f} > {current_middle:.4f})"
                    ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse Bollinger: {e}")
        
        return signals

    def analyze_volume(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse du volume"""
        signals = []
        
        try:
            if 'volume' in df.columns and len(df) > 20:
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                
                # Signal 1: Volume au-dessus de la moyenne
                if current_volume > avg_volume * 1.5:
                    strength = SignalStrength.STRONG if current_volume > avg_volume * 2 else SignalStrength.MODERATE
                    signals.append(TechnicalSignal(
                        indicator="Volume",
                        condition="Volume élevé",
                        value=current_volume - avg_volume,
                        strength=strength,
                        description=f"Volume {current_volume/avg_volume:.1f}x supérieur à la moyenne"
                    ))
                
                # Signal 2: Volume croissant
                if len(df) > 3:
                    recent_volumes = df['volume'].iloc[-3:].values
                    if recent_volumes[-1] > recent_volumes[-2] > recent_volumes[-3]:
                        signals.append(TechnicalSignal(
                            indicator="Volume",
                            condition="Volume croissant",
                            value=recent_volumes[-1] - recent_volumes[-3],
                            strength=SignalStrength.MODERATE,
                            description="Volume en augmentation sur 3 périodes"
                        ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse volume: {e}")
        
        return signals

    def analyze_candlesticks(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Analyse des patterns de chandeliers"""
        signals = []
        
        try:
            # Patterns haussiers
            hammer = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close']) # type: ignore
            engulfing = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']) # type: ignore
            morning_star = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close']) # type: ignore
            
            # Vérification des patterns récents
            if len(hammer) > 0 and hammer.iloc[-1] > 0:
                signals.append(TechnicalSignal(
                    indicator="Candlestick",
                    condition="Hammer",
                    value=hammer.iloc[-1],
                    strength=SignalStrength.MODERATE,
                    description="Pattern Hammer détecté"
                ))
            
            if len(engulfing) > 0 and engulfing.iloc[-1] > 0:
                signals.append(TechnicalSignal(
                    indicator="Candlestick",
                    condition="Bullish Engulfing",
                    value=engulfing.iloc[-1],
                    strength=SignalStrength.STRONG,
                    description="Pattern Engulfing haussier"
                ))
            
            if len(morning_star) > 0 and morning_star.iloc[-1] > 0:
                signals.append(TechnicalSignal(
                    indicator="Candlestick",
                    condition="Morning Star",
                    value=morning_star.iloc[-1],
                    strength=SignalStrength.VERY_STRONG,
                    description="Pattern Morning Star"
                ))
            
        except Exception as e:
            self.logger.error(f"Erreur analyse chandelier: {e}")
        
        return signals

    def analyze_trend(self, df: pd.DataFrame) -> str:
        """Analyse de la tendance"""
        try:
            # Analyse basée sur les EMAs
            ema20 = talib.EMA(df['close'], timeperiod=20) # type: ignore
            ema50 = talib.EMA(df['close'], timeperiod=50) # type: ignore
            
            current_price = df['close'].iloc[-1]
            
            if len(ema20) > 0 and len(ema50) > 0:
                current_ema20 = ema20.iloc[-1]
                current_ema50 = ema50.iloc[-1]
                
                if current_price > current_ema20 > current_ema50:
                    return "HAUSSIER FORT"
                elif current_price > current_ema20 and current_ema20 > current_ema50:
                    return "HAUSSIER"
                elif current_price < current_ema20 < current_ema50:
                    return "BAISSIER FORT"
                elif current_price < current_ema20 and current_ema20 < current_ema50:
                    return "BAISSIER"
                else:
                    return "NEUTRE"
            
        except Exception as e:
            self.logger.error(f"Erreur analyse tendance: {e}")
        
        return "INDETERMINE"

    def analyze_momentum(self, df: pd.DataFrame) -> str:
        """Analyse du momentum"""
        try:
            # Calcul du momentum basé sur ROC
            roc = talib.ROC(df['close'], timeperiod=10) # type: ignore
            
            if len(roc) > 0 and not np.isnan(roc.iloc[-1]):
                current_roc = roc.iloc[-1]
                
                if current_roc > 2:
                    return "TRES FORT"
                elif current_roc > 1:
                    return "FORT"
                elif current_roc > 0:
                    return "POSITIF"
                elif current_roc > -1:
                    return "NEGATIF"
                else:
                    return "FAIBLE"
            
        except Exception as e:
            self.logger.error(f"Erreur analyse momentum: {e}")
        
        return "INDETERMINE"

    def analyze_volatility(self, df: pd.DataFrame) -> str:
        """Analyse de la volatilité"""
        try:
            # Calcul ATR pour la volatilité
            atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14) # type: ignore
            
            if len(atr) > 0 and not np.isnan(atr.iloc[-1]):
                current_atr = atr.iloc[-1]
                avg_atr = atr.rolling(window=20).mean().iloc[-1]
                
                ratio = current_atr / avg_atr
                
                if ratio > 1.5:
                    return "TRES ELEVEE"
                elif ratio > 1.2:
                    return "ELEVEE"
                elif ratio > 0.8:
                    return "NORMALE"
                else:
                    return "FAIBLE"
            
        except Exception as e:
            self.logger.error(f"Erreur analyse volatilité: {e}")
        
        return "INDETERMINE"

    def get_recommendation(self, total_score: float, signal_count: int) -> str:
        """Détermine la recommandation basée sur le score"""
        if signal_count == 0:
            return "AUCUN SIGNAL"
        
        avg_score = total_score / signal_count
        
        if avg_score >= 3.0 and signal_count >= 3:
            return "ACHAT FORT"
        elif avg_score >= 2.5 and signal_count >= 3:
            return "ACHAT"
        elif avg_score >= 2.0 and signal_count >= 2:
            return "ACHAT FAIBLE"
        elif avg_score >= 1.5:
            return "NEUTRE"
        else:
            return "EVITER"

    def is_valid_signal(self, analysis: MarketAnalysis, min_conditions: int = 3) -> bool:
        """Vérifie si le signal est valide pour le trading"""
        
        # Vérification nombre minimum de conditions
        if len(analysis.signals) < min_conditions:
            return False
        
        # Vérification score minimum
        if analysis.total_score < min_conditions * 2:
            return False
        
        # Vérification recommandation
        if analysis.recommendation in ["AUCUN SIGNAL", "EVITER"]:
            return False
        
        # Vérification présence d'au moins un signal fort
        has_strong_signal = any(
            signal.strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]
            for signal in analysis.signals
        )
        
        return has_strong_signal

    def get_signal_summary(self, analysis: MarketAnalysis) -> str:
        """Retourne un résumé des signaux"""
        summary = f"📊 Analyse {analysis.pair}:\\n"
        summary += f"🎯 Recommandation: {analysis.recommendation}\\n"
        summary += f"📈 Tendance: {analysis.trend}\\n"
        summary += f"⚡ Momentum: {analysis.momentum}\\n"
        summary += f"📊 Volatilité: {analysis.volatility}\\n"
        summary += f"🔢 Score: {analysis.total_score:.1f} ({len(analysis.signals)} signaux)\\n"
        
        summary += "\\nSignaux détectés:\\n"
        for signal in analysis.signals:
            strength_emoji = {
                SignalStrength.WEAK: "🟡",
                SignalStrength.MODERATE: "🟠",
                SignalStrength.STRONG: "🔴",
                SignalStrength.VERY_STRONG: "🟣"
            }
            summary += f"  {strength_emoji[signal.strength]} {signal.indicator}: {signal.description}\\n"
        
        return summary

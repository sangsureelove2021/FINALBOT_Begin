"""
TIER 2 - MARKET STATE CLASSIFIER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Classifies the current market into one of 10 states based on Tier 1 outputs.

States:
    1. TRENDING_UP
    2. TRENDING_DOWN
    3. IMPULSIVE
    4. CORRECTIVE
    5. CONSOLIDATING
    6. COMPRESSION
    7. BREAKING_OUT
    8. RANGING
    9. CHOPPY
    10. EXHAUSTION
"""

import pandas as pd
from typing import Dict, Any

from core.engines.base_engine import BaseEngine


class MarketStateClassifier(BaseEngine):
    """Tier 2: Market State Classifier"""
    
    ENGINE_NAME = "market_state_classifier"
    ENGINE_VERSION = "1.0.0"
    TIER = 2
    MIN_CANDLES = 100
    
    def __init__(self, config=None):
        super().__init__(config)
        # Will receive context-aware data through analyze
    
    def analyze(self, candles_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
        """
        Special analyze for classification.
        Can accept either candles_df + computed tier1 results, or context.
        """
        try:
            # Try to extract tier 1 data from kwargs (context-aware)
            tier1 = kwargs.get('tier1', {})
            
            # If not given, compute on the fly from candles
            if not tier1 and candles_df is not None:
                tier1 = self._compute_tier1_quick(candles_df)
            
            if not tier1:
                return self.get_neutral_state()
            
            # Classify
            state = self._classify(tier1)
            
            # Calculate quality
            quality = self._calculate_quality(state, tier1)
            
            return {
                'state': state,
                'quality_score': quality,
                'tradeable': self._is_tradeable(state, quality),
                'description': self._describe_state(state),
                'confidence': min(100, quality + 5),
            }
        except Exception as e:
            print(f"❌ MarketStateClassifier error: {e}")
            return self.get_neutral_state()
    
    def _compute_tier1_quick(self, df: pd.DataFrame) -> Dict:
        """Quick computation of needed tier 1 metrics"""
        try:
            ema20 = df['close'].ewm(span=20).mean().iloc[-1]
            ema50 = df['close'].ewm(span=50).mean().iloc[-1]
            close = df['close'].iloc[-1]
            
            direction = 'UP' if close > ema20 > ema50 else ('DOWN' if close < ema20 < ema50 else 'NONE')
            
            # ATR percentile rough
            high_low = df['high'] - df['low']
            atr = high_low.rolling(14).mean().iloc[-1]
            atr_avg = high_low.rolling(14).mean().tail(100).mean()
            atr_pct = (atr / atr_avg * 50) if atr_avg > 0 else 50
            atr_pct = min(100, max(0, atr_pct))
            
            return {
                'direction': direction,
                'atr_percentile': float(atr_pct),
                'trend_strength': 60 if direction != 'NONE' else 20,
            }
        except:
            return {}
    
    def _classify(self, tier1: Dict) -> str:
        """Apply classification logic"""
        direction = tier1.get('direction', 'NONE')
        atr_pct = tier1.get('atr_percentile', 50)
        trend_strength = tier1.get('trend_strength', 0) or tier1.get('strength', 0)
        trend_type = tier1.get('type', '')
        regime = tier1.get('regime', 'NORMAL')
        exhaustion = tier1.get('exhaustion_risk', 0)
        bos_detected = tier1.get('bos_detected', False)
        
        # Exhaustion check first (priority)
        if exhaustion > 70:
            return 'EXHAUSTION'
        
        # Choppy = no clear direction
        if direction == 'NONE' or trend_type == 'CHOPPY':
            return 'CHOPPY'
        
        # Breakout
        if bos_detected and atr_pct > 50:
            return 'BREAKING_OUT'
        
        # Compression
        if atr_pct < 25 and regime == 'LOW':
            return 'COMPRESSION'
        
        # Impulsive trend
        if trend_type == 'IMPULSIVE' and trend_strength > 70:
            return 'IMPULSIVE'
        
        # Corrective
        if trend_type == 'CORRECTIVE':
            return 'CORRECTIVE'
        
        # Strong trends
        if trend_strength > 60:
            return 'TRENDING_UP' if direction == 'UP' else 'TRENDING_DOWN'
        
        # Ranging
        if atr_pct < 50 and trend_strength < 50:
            return 'RANGING'
        
        # Consolidating
        if 30 < atr_pct < 60:
            return 'CONSOLIDATING'
        
        return 'RANGING'
    
    def _calculate_quality(self, state: str, tier1: Dict) -> int:
        """Quality score for the state (how tradeable)"""
        quality_map = {
            'IMPULSIVE': 90, 'TRENDING_UP': 85, 'TRENDING_DOWN': 85,
            'BREAKING_OUT': 80, 'COMPRESSION': 70, 'CORRECTIVE': 60,
            'CONSOLIDATING': 55, 'RANGING': 45,
            'CHOPPY': 20, 'EXHAUSTION': 25,
        }
        base = quality_map.get(state, 50)
        
        # Adjust based on trend strength
        trend_strength = tier1.get('trend_strength', 50)
        if trend_strength > 80:
            base = min(100, base + 5)
        elif trend_strength < 30:
            base = max(20, base - 10)
        
        return base
    
    def _is_tradeable(self, state: str, quality: int) -> bool:
        """Is this state tradeable?"""
        non_tradeable = ['CHOPPY', 'EXHAUSTION']
        if state in non_tradeable:
            return False
        return quality >= 60
    
    def _describe_state(self, state: str) -> str:
        descriptions = {
            'TRENDING_UP': 'Strong upward trend',
            'TRENDING_DOWN': 'Strong downward trend',
            'IMPULSIVE': 'Fast trending move',
            'CORRECTIVE': 'Pullback / correction phase',
            'CONSOLIDATING': 'Price consolidating',
            'COMPRESSION': 'Volatility compression',
            'BREAKING_OUT': 'Breakout in progress',
            'RANGING': 'Range-bound trading',
            'CHOPPY': 'Choppy / unclear direction',
            'EXHAUSTION': 'Trend exhaustion - reversal likely',
        }
        return descriptions.get(state, 'Unknown state')
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'state': 'CHOPPY', 'quality_score': 30,
            'tradeable': False, 'description': 'Insufficient data',
            'confidence': 0,
        }

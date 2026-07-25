"""
Confidence Scorer

Calculates final confidence from multiple sources.
"""

from typing import Dict, List
from data_evaluate.models.market_context import MarketContext


class ConfidenceScorer:
    """
    Calculates final confidence score from MarketContext.
    
    Considers:
    - Engine confidence levels
    - Score agreement (do all engines agree?)
    - Risk factor presence
    - Data quality
    """
    
    def __init__(self, threshold: int = 75):
        """
        Args:
            threshold: Minimum confidence for signal eligibility (default 75)
        """
        self.threshold = threshold
    
    def score(self, context: MarketContext) -> int:
        """
        Compute final confidence 0-100.
        """
        components = []
        
        # 1. Tier 1 confidence average
        tier1_conf = self._tier1_confidence(context)
        components.append(('tier1', tier1_conf, 0.30))
        
        # 2. Market state quality
        state_conf = self._market_state_quality(context)
        components.append(('state', state_conf, 0.25))
        
        # 3. Score agreement
        agreement = self._score_agreement(context)
        components.append(('agreement', agreement, 0.20))
        
        # 4. Risk factor penalty
        risk_score = self._risk_score(context)
        components.append(('risk', risk_score, 0.15))
        
        # 5. Data quality
        data_quality = self._data_quality(context)
        components.append(('data', data_quality, 0.10))
        
        # Weighted average
        total = sum(score * weight for _, score, weight in components)
        total_weight = sum(weight for _, _, weight in components)
        
        final = total / total_weight if total_weight > 0 else 0
        
        return int(max(0, min(100, final)))
    
    def _tier1_confidence(self, context: MarketContext) -> float:
        """Average confidence from Tier 1 engines"""
        confidences = []
        for layer in [context.trend, context.strength, 
                     context.volatility, context.structure, context.mtf]:
            if isinstance(layer, dict):
                conf = layer.get('confidence') or layer.get('confidence_from_mtf')
                if conf is not None:
                    confidences.append(float(conf))
        
        if not confidences:
            return 50.0
        return sum(confidences) / len(confidences)
    
    def _market_state_quality(self, context: MarketContext) -> float:
        """How tradeable is the current market state"""
        # market_state may be a plain string or a dict from the classifier
        ms = context.market_state
        if isinstance(ms, dict):
            state = ms.get('state', '')
        else:
            state = ms or ''
        quality_map = {
            'TRENDING_UP': 80, 'TRENDING_DOWN': 80,
            'BREAKING_OUT': 75, 'IMPULSIVE': 85,
            'COMPRESSION': 70, 'CORRECTIVE': 60,
            'CONSOLIDATING': 55, 'RANGING': 50,
            'CHOPPY': 30, 'EXHAUSTION': 25,
            
            # Correct actual market state classifier names
            'TRENDING_STRONG': 90, 'TRENDING_WEAK': 65,
            'BREAKOUT_EMERGING': 85, 'ACCUMULATION': 80,
            'SIDEWAY_RANGE': 75, 'DISTRIBUTION': 45,
            'CHOPPY_UNCERTAIN': 20, 'REVERSAL_FORMING': 60,
            'LIQUIDITY_VOID': 10, 'UNCLEAR': 15,
            'TRANSITIONAL': 50,
        }
        return quality_map.get(state, 50)
    
    def _score_agreement(self, context: MarketContext) -> float:
        """How well do different engines agree"""
        # Check MTF agreement
        mtf_score = context.mtf.get('alignment_score', 50)
        if isinstance(mtf_score, (int, float)):
            return float(mtf_score)
        return 50.0
    
    def _risk_score(self, context: MarketContext) -> float:
        """Score (lower is worse) for risk factors. Returns 100 if no risks, 0 if many risks"""
        score = 100.0
        
        # Trap detection penalty
        if context.traps.get('trap_detected'):
            score -= 30
        
        # Noise penalty
        noise_level = context.noise.get('noise_level', 0)
        if noise_level > 70:
            score -= 25
        
        # Anomaly penalty
        if context.anomaly.get('anomaly_detected'):
            score -= 20
        
        # Conflict penalty
        conflict_score = context.conflict.get('conflict_score', 0)
        if conflict_score > 60:
            score -= 15
        
        return max(0.0, score)
    
    def _data_quality(self, context: MarketContext) -> float:
        """Data quality assessment"""
        if context.has_errors():
            return 50.0
        if len(context.warnings) > 5:
            return 70.0
        return 100.0
    
    def is_signal_eligible(self, context: MarketContext) -> bool:
        """Check if confidence meets threshold for signal generation"""
        return self.score(context) >= self.threshold

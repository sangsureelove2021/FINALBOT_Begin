"""
TIER 7 - SIGNAL QUALITY SCORER


Scores the overall quality of a potential signal.
Combines edge, clarity, risk, and confirmation into a single quality grade.
"""

from typing import Dict, Any
from core.engines.base_engine import BaseEngine


class SignalQualityScorer(BaseEngine):
    """Tier 7: Signal Quality Scorer - reads MarketContext"""
    
    ENGINE_NAME = "signal_quality_scorer"
    ENGINE_VERSION = "1.0.0"
    TIER = 7
    
    def analyze(self, context=None, **kwargs) -> Dict[str, Any]:
        """Score signal quality from full context"""
        try:
            ctx = context or kwargs.get('context')
            if ctx is None:
                return self.get_neutral_state()
            
            # Component scores
            edge_score = self._score_edge(ctx)
            clarity_score = self._score_clarity(ctx)
            confirmation_score = self._score_confirmation(ctx)
            risk_penalty = self._score_risk_penalty(ctx)
            
            # Aggregate quality
            raw_quality = (
                edge_score * 0.30 +
                clarity_score * 0.30 +
                confirmation_score * 0.25 +
                (100 - risk_penalty) * 0.15
            )
            
            quality_score = int(min(100, max(0, raw_quality)))
            grade = self._assign_grade(quality_score)
            
            return {
                'quality_score': quality_score,
                'grade': grade,
                'edge_score': edge_score,
                'clarity_score': clarity_score,
                'confirmation_score': confirmation_score,
                'risk_penalty': risk_penalty,
                'is_premium': quality_score >= 85,
                'is_tradeable_quality': quality_score >= 70,
                'confidence': quality_score,
            }
        except Exception as e:
            print(f" SignalQualityScorer error: {e}")
            return self.get_neutral_state()
    
    def _score_edge(self, ctx) -> float:
        """Score the statistical edge (0-100)"""
        edge = ctx.move_probability.get('edge', 0)
        # Edge of 0 = 0 score, edge of 25+ = 100 score
        return min(100, edge * 4)
    
    def _score_clarity(self, ctx) -> float:
        """Score market clarity (0-100)"""
        clarity = ctx.synthesized_context.get('market_clarity', 50)
        return float(clarity)
    
    def _score_confirmation(self, ctx) -> float:
        """Score how many engines confirm the direction (0-100)"""
        direction = ctx.move_probability.get('direction', 'NEUTRAL')
        if direction == 'NEUTRAL':
            return 30.0
        
        confirmations = 0
        total_checks = 6
        
        # Trend confirms
        if ctx.trend.get('direction') == direction:
            confirmations += 1
        
        # MTF confirms
        if ctx.mtf.get('dominant_direction') == direction:
            confirmations += 1
        
        # Synthesizer confirms
        if ctx.synthesized_context.get('directional_bias') == direction:
            confirmations += 1
        
        # Conflict analyzer EMA confirms
        if ctx.conflict.get('ema_direction') == direction:
            confirmations += 1
        
        # Continuation supports
        cont_bias = ctx.continuation.get('bias', 'NEUTRAL')
        trend_dir = ctx.trend.get('direction', 'NONE')
        if cont_bias == 'CONTINUATION' and trend_dir == direction:
            confirmations += 1
        
        # Market pressure confirms
        buy_p = ctx.orderflow.get('buy_pressure', 50)
        if (direction == 'UP' and buy_p > 55) or (direction == 'DOWN' and buy_p < 45):
            confirmations += 1
        
        return (confirmations / total_checks) * 100
    
    def _score_risk_penalty(self, ctx) -> float:
        """Risk penalty 0-100 (higher = more risk)"""
        return float(ctx.synthesized_context.get('risk_level', 50))
    
    def _assign_grade(self, score: int) -> str:
        """Assign letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 78:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        return 'F'
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'quality_score': 0, 'grade': 'F',
            'edge_score': 0, 'clarity_score': 0,
            'confirmation_score': 0, 'risk_penalty': 100,
            'is_premium': False, 'is_tradeable_quality': False,
            'confidence': 0,
        }

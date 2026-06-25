"""
TIER 8 - EXPLAINABILITY ENGINE


Generates human-readable explanations of WHY a signal/decision was made.
Critical for trust and debugging.
"""

from typing import Dict, Any, List
from core.orchestration.base_engine import BaseEngine


class ExplainabilityEngine(BaseEngine):
    """Tier 8: Explainability Engine - reads MarketContext"""
    
    ENGINE_NAME = "explainability_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 8
    
    def analyze(self, context=None, **kwargs) -> Dict[str, Any]:
        """Generate explanation of the analysis"""
        try:
            ctx = context or kwargs.get('context')
            if ctx is None:
                return self.get_neutral_state()
            
            supporting = self._gather_supporting_factors(ctx)
            opposing = self._gather_opposing_factors(ctx)
            key_drivers = self._identify_key_drivers(ctx)
            summary = self._compose_summary(ctx, supporting, opposing)
            
            return {
                'summary': summary,
                'supporting_factors': supporting,
                'opposing_factors': opposing,
                'key_drivers': key_drivers,
                'factor_balance': len(supporting) - len(opposing),
                'explanation_available': True,
                'confidence': 100,
            }
        except Exception as e:
            import logging
            import traceback
            logging.exception(f" ExplainabilityEngine error: {e}")
            traceback.print_exc()
            return self.get_neutral_state()
    
    def _gather_supporting_factors(self, ctx) -> List[str]:
        """Factors supporting a trade"""
        factors = []
        
        trend_dir = ctx.trend.get('direction', 'NONE')
        if trend_dir != 'NONE':
            conf = ctx.trend.get('confidence', 0)
            factors.append(f"Trend is {trend_dir} (confidence {conf})")
        
        mtf_align = ctx.mtf.get('alignment_score', 0)
        if mtf_align >= 70:
            factors.append(f"Strong MTF alignment ({mtf_align})")
        
        clarity = ctx.synthesized_context.get('market_clarity', 0)
        if clarity >= 65:
            factors.append(f"Clear market picture ({clarity})")
        
        edge = ctx.move_probability.get('edge', 0)
        if edge >= 10:
            factors.append(f"Statistical edge present ({edge})")
        
        efficiency = ctx.efficiency.get('overall_efficiency', 0)
        if efficiency >= 65:
            factors.append(f"Efficient price movement ({efficiency})")
        
        quality = ctx.signal_quality.get('quality_score', 0)
        if quality >= 70:
            grade = ctx.signal_quality.get('grade', '?')
            factors.append(f"Good signal quality (grade {grade})")
        
        confirmation = ctx.signal_quality.get('confirmation_score', 0)
        if confirmation >= 70:
            factors.append(f"Multiple engines confirm direction ({confirmation:.0f})")
        
        return factors
    
    def _gather_opposing_factors(self, ctx) -> List[str]:
        """Factors against a trade"""
        factors = []
        
        if ctx.traps.get('trap_detected'):
            trap_type = ctx.traps.get('trap_type', 'unknown')
            factors.append(f"Trap detected ({trap_type})")
        
        if ctx.anomaly.get('anomaly_detected'):
            factors.append(f"Statistical anomaly detected")
        
        noise = ctx.noise.get('noise_level', 0)
        if noise > 60:
            factors.append(f"High market noise ({noise})")
        
        conflict = ctx.conflict.get('conflict_score', 0)
        if conflict > 50:
            factors.append(f"Conflicting signals ({conflict})")
        
        if ctx.transition.get('in_transition'):
            t_type = ctx.transition.get('transition_type', 'unknown')
            factors.append(f"Market in transition ({t_type})")
        
        exhaustion = ctx.strength.get('exhaustion_risk', 0)
        if exhaustion > 65:
            factors.append(f"Momentum exhaustion risk ({exhaustion})")
        
        if ctx.mtf.get('htf_ltf_conflict'):
            factors.append("Higher/Lower timeframe conflict")
        
        if ctx.trend.get('type') == 'CHOPPY':
            factors.append("Choppy market - no clear direction")
        
        return factors
    
    def _identify_key_drivers(self, ctx) -> List[str]:
        """Top 3 most influential factors"""
        drivers = []
        
        # The dominant factor is usually the synthesized read
        market_read = ctx.synthesized_context.get('market_read', '')
        if market_read:
            drivers.append(market_read)
        
        # Probability direction
        prob_dir = ctx.move_probability.get('direction', 'NEUTRAL')
        up_prob = ctx.move_probability.get('up_probability', 50)
        if prob_dir != 'NEUTRAL':
            drivers.append(f"Probability favors {prob_dir} ({up_prob}% up)")
        
        # Confidence tier
        conf_tier = ctx.confidence_framework.get('confidence_tier', 'UNKNOWN')
        final_conf = ctx.confidence_framework.get('final_confidence', 0)
        drivers.append(f"Confidence: {conf_tier} ({final_conf})")
        
        return drivers[:3]
    
    def _compose_summary(self, ctx, supporting, opposing) -> str:
        """One-paragraph plain summary"""
        if isinstance(ctx.market_state, dict):
            state = ctx.market_state.get('state', 'UNKNOWN')
        else:
            state = str(ctx.market_state) if ctx.market_state else 'UNKNOWN'
        direction = ctx.move_probability.get('direction', 'NEUTRAL')
        confidence = ctx.confidence_framework.get('final_confidence', 0)
        
        sup_count = len(supporting)
        opp_count = len(opposing)
        
        verdict = "favorable" if sup_count > opp_count else (
                  "unfavorable" if opp_count > sup_count else "mixed")
        
        return (
            f"Market is {state} with {direction} bias. "
            f"Final confidence {confidence}. "
            f"{sup_count} supporting vs {opp_count} opposing factors - "
            f"conditions are {verdict}."
        )
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'summary': 'No explanation available - insufficient data',
            'supporting_factors': [], 'opposing_factors': [],
            'key_drivers': [], 'factor_balance': 0,
            'explanation_available': False, 'confidence': 0,
        }

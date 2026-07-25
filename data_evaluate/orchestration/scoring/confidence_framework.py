"""
TIER 7 - CONFIDENCE FRAMEWORK


Final confidence calibration. Produces the definitive confidence number
that the strategy and execution gate will use.

This is the LAST WORD on "how confident are we" before strategy decision.
"""

from typing import Dict, Any
from data_evaluate.orchestration.base_engine import BaseEngine


class ConfidenceFramework(BaseEngine):
    """Tier 7: Confidence Framework - reads MarketContext"""
    
    ENGINE_NAME = "confidence_framework"
    ENGINE_VERSION = "1.0.0"
    TIER = 7
    
    def analyze(self, context=None, **kwargs) -> Dict[str, Any]:
        """Calibrate final confidence"""
        try:
            ctx = context or kwargs.get('context')
            if ctx is None:
                return self.get_neutral_state()
            
            # Base confidence from quality
            base = ctx.signal_quality.get('quality_score', 0)
            
            # Probability estimate confidence
            prob_conf = ctx.move_probability.get('estimate_confidence', 0)
            
            # Combine base + probability confidence
            combined = (base * 0.6) + (prob_conf * 0.4)
            
            # Apply calibration adjustments
            calibrated = self._apply_calibration(ctx, combined)
            
            # Apply hard caps based on risk factors
            final = self._apply_caps(ctx, calibrated)
            
            # Reliability of this confidence
            reliability = self._assess_reliability(ctx)
            
            return {
                'final_confidence': int(final),
                'base_confidence': int(base),
                'calibrated_confidence': int(calibrated),
                'reliability': reliability,
                'confidence_tier': self._tier(final),
                'is_actionable': final >= 75 and reliability >= 60,
                'caps_applied': self._list_caps(ctx),
                'confidence': int(final),
            }
        except Exception as e:
            import logging
            logging.exception(f"ConfidenceFramework error: {e}")
            raise
    
    def _apply_calibration(self, ctx, raw: float) -> float:
        """Apply calibration adjustments"""
        calibrated = raw
        
        # Boost if everything aligns strongly
        confirmation = ctx.signal_quality.get('confirmation_score', 0)
        if confirmation >= 85:
            calibrated += 5
        
        # Reduce if in transition
        if ctx.transition.get('in_transition'):
            calibrated -= 8
        
        # Reduce if low persistence (move may not hold)
        persistence = ctx.persistence.get('persistence_score', 50)
        if persistence < 40:
            calibrated -= 6
        
        # Boost if high efficiency
        efficiency = ctx.efficiency.get('overall_efficiency', 50)
        if efficiency >= 70:
            calibrated += 4
        
        return max(0, min(100, calibrated))
    
    def _apply_caps(self, ctx, confidence: float) -> float:
        """Apply hard caps - confidence cannot exceed these in risky conditions"""
        capped = confidence
        
        # Cap at 70 if trap detected
        if ctx.traps.get('trap_detected'):
            capped = min(capped, 70)
        
        # Cap at 65 if anomaly detected
        if ctx.anomaly.get('anomaly_detected'):
            capped = min(capped, 65)
        
        # Cap at 60 if high conflict
        if ctx.conflict.get('conflict_score', 0) > 70:
            capped = min(capped, 60)
        
        # Cap at 55 if very noisy
        if ctx.noise.get('noise_level', 0) > 75:
            capped = min(capped, 55)
        
        # Cap at 50 if choppy market
        if ctx.trend.get('type') == 'CHOPPY':
            capped = min(capped, 50)
        
        # Cap at 70 if MTF conflict
        if ctx.mtf.get('htf_ltf_conflict'):
            capped = min(capped, 70)
        
        return capped
    
    def _list_caps(self, ctx) -> list:
        """List which caps were triggered"""
        caps = []
        if ctx.traps.get('trap_detected'):
            caps.append('trap_cap_70')
        if ctx.anomaly.get('anomaly_detected'):
            caps.append('anomaly_cap_65')
        if ctx.conflict.get('conflict_score', 0) > 70:
            caps.append('conflict_cap_60')
        if ctx.noise.get('noise_level', 0) > 75:
            caps.append('noise_cap_55')
        if ctx.trend.get('type') == 'CHOPPY':
            caps.append('choppy_cap_50')
        if ctx.mtf.get('htf_ltf_conflict'):
            caps.append('mtf_cap_70')
        return caps
    
    def _assess_reliability(self, ctx) -> int:
        """How reliable is this confidence number (0-100)"""
        reliability = 70
        
        # Errors reduce reliability
        if ctx.has_errors():
            reliability -= 25
        
        # Many warnings reduce reliability
        if len(ctx.warnings) > 5:
            reliability -= 15
        
        # Transition reduces reliability
        if ctx.transition.get('in_transition'):
            reliability -= 15
        
        # Good regime quality increases reliability
        regime_q = ctx.regime_quality.get('overall_quality', 50)
        if regime_q > 70:
            reliability += 15
        
        # Engines all executed
        if len(ctx.engines_executed) >= 20:
            reliability += 10
        
        return int(min(100, max(0, reliability)))
    
    def _tier(self, confidence: float) -> str:
        """Confidence tier label"""
        if confidence >= 90:
            return 'VERY_HIGH'
        elif confidence >= 75:
            return 'HIGH'
        elif confidence >= 60:
            return 'MODERATE'
        elif confidence >= 45:
            return 'LOW'
        return 'VERY_LOW'
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'final_confidence': 0, 'base_confidence': 0,
            'calibrated_confidence': 0, 'reliability': 0,
            'confidence_tier': 'VERY_LOW', 'is_actionable': False,
            'caps_applied': [], 'confidence': 0,
        }

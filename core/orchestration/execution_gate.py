"""
Execution Gate (signal_veto)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Final authority that decides whether to execute or block a signal.

This is the LAST DEFENSE against bad trades.
Philosophy: "The Art of Saying NO"
"""

from typing import Dict, Any
from core.models.market_context import MarketContext


class ExecutionGate:
    """
    Final gate that approves or blocks signals.
    
    Rules:
    - If confidence < threshold → BLOCK
    - If trap detected → BLOCK
    - If anomaly detected → BLOCK
    - If multiple conflicts → BLOCK
    - If extreme volatility → BLOCK
    - If exhaustion + low confidence → BLOCK
    """
    
    def __init__(self, 
                 min_confidence: int = 75,
                 max_block_score: int = 60,
                 block_on_trap: bool = True,
                 block_on_anomaly: bool = True):
        self.min_confidence = min_confidence
        self.max_block_score = max_block_score
        self.block_on_trap = block_on_trap
        self.block_on_anomaly = block_on_anomaly
    
    def evaluate(self, context: MarketContext, 
                recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate signal and decide approve or block.
        
        Returns:
            {
                'approved': bool,
                'reason': str,
                'blocked_by': str,
                'risk_score': int
            }
        """
        # Get scores
        confidence = context.get_score('confidence')
        block_score = context.get_score('block')
        
        # === HARD BLOCKS ===
        
        # 1. Confidence too low
        if confidence < self.min_confidence:
            return self._block(
                f"Confidence {confidence:.0f} < threshold {self.min_confidence}",
                'low_confidence'
            )
        
        # 2. Block score too high
        if block_score > self.max_block_score:
            return self._block(
                f"Block score {block_score:.0f} > max {self.max_block_score}",
                'high_block_score'
            )
        
        # 3. Trap detected
        if self.block_on_trap and context.traps.get('trap_detected'):
            trap_type = context.traps.get('trap_type', 'unknown')
            return self._block(
                f"Trap detected: {trap_type}",
                'trap_detected'
            )
        
        # 4. Anomaly detected
        if self.block_on_anomaly and context.anomaly.get('anomaly_detected'):
            return self._block("Statistical anomaly detected", 'anomaly')
        
        # 5. Extreme volatility
        regime = context.volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            return self._block("Extreme volatility regime", 'extreme_volatility')
        
        # 6. MTF conflict + low alignment
        mtf_conflict = context.mtf.get('htf_ltf_conflict', False)
        mtf_alignment = context.mtf.get('alignment_score', 50)
        if mtf_conflict and mtf_alignment < 40:
            return self._block(
                "Higher TF vs Lower TF conflict with poor alignment",
                'mtf_conflict'
            )
        
        # 7. Choppy market
        trend_type = context.trend.get('type', '')
        if trend_type == 'CHOPPY':
            return self._block("Choppy market - no clear direction", 'choppy_market')
        
        # 8. High exhaustion + low confidence combo
        exhaustion = context.strength.get('exhaustion_risk', 0)
        if exhaustion > 70 and confidence < 85:
            return self._block(
                f"High exhaustion ({exhaustion:.0f}) with moderate confidence",
                'exhaustion_risk'
            )
        
        # === APPROVED ===
        return {
            'approved': True,
            'reason': f"All checks passed (conf={confidence:.0f}, block={block_score:.0f})",
            'blocked_by': None,
            'risk_score': int(block_score),
        }
    
    def _block(self, reason: str, code: str) -> Dict[str, Any]:
        return {
            'approved': False,
            'reason': reason,
            'blocked_by': code,
            'risk_score': 100,
        }

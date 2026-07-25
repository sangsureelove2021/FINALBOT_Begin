"""
Block Scorer

Scores reasons to BLOCK entry (Art of Saying NO).
Higher score = more reasons to block.
"""

from data_evaluate.models.market_context import MarketContext


class BlockScorer:
    """Compute 0-100 block score (higher = more reasons to NOT trade)"""
    
    def score(self, context: MarketContext) -> int:
        """Compute block score 0-100"""
        score = 0.0
        
        # Trap detected
        if context.traps.get('trap_detected'):
            score += 35
        
        # High noise
        noise = context.noise.get('noise_level', 0)
        if noise > 75:
            score += 25
        elif noise > 60:
            score += 15
        
        # Anomaly
        if context.anomaly.get('anomaly_detected'):
            score += 20
        
        # Conflict detected
        conflict = context.conflict.get('conflict_score', 0)
        if conflict > 70:
            score += 20
        elif conflict > 50:
            score += 10
        
        # Exhaustion risk
        exhaustion = context.strength.get('exhaustion_risk', 0)
        if exhaustion > 75:
            score += 18
        elif exhaustion > 60:
            score += 10
        
        # Reversal risk in trending market
        reversal = context.trend.get('reversal_risk', 0)
        if reversal > 70:
            score += 15
        
        # Choppy / corrective market
        trend_type = context.trend.get('type', '')
        if trend_type == 'CHOPPY':
            state_str = context.market_state.get('state', 'UNKNOWN') if isinstance(context.market_state, dict) else context.market_state
            if state_str not in ("ACCUMULATION", "BREAKOUT_EMERGING"):
                score += 25
        elif trend_type == 'CORRECTIVE':
            score += 12
        
        # MTF conflict
        if context.mtf.get('htf_ltf_conflict'):
            score += 18
        
        # Low data quality
        if context.has_errors():
            score += 30
        
        return int(max(0, min(100, score)))
    
    def get_block_reasons(self, context: MarketContext) -> list:
        """Return list of human-readable block reasons"""
        reasons = []
        
        if context.traps.get('trap_detected'):
            reasons.append("Trap detected")
        
        if context.noise.get('noise_level', 0) > 75:
            reasons.append("High market noise")
        
        if context.anomaly.get('anomaly_detected'):
            reasons.append("Statistical anomaly detected")
        
        if context.conflict.get('conflict_score', 0) > 70:
            reasons.append("Engine signals conflicting")
        
        if context.strength.get('exhaustion_risk', 0) > 75:
            reasons.append("Momentum exhaustion risk")
        
        if context.trend.get('reversal_risk', 0) > 70:
            reasons.append("High reversal risk")
        
        if context.trend.get('type') == 'CHOPPY':
            reasons.append("Choppy market - no clear direction")
        
        if context.mtf.get('htf_ltf_conflict'):
            reasons.append("Higher TF / Lower TF conflict")
        
        if context.has_errors():
            reasons.append(f"Data errors: {len(context.errors)}")
        
        return reasons

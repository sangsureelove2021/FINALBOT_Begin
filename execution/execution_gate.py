"""
Execution Gate (signal_veto)

Final authority that decides whether to execute or block a signal.

This is the LAST DEFENSE against bad trades.
"""

from typing import Dict, Any
from data_evaluate.models.market_context import MarketContext


class ExecutionGate:
    """
    Final gate that approves or blocks signals.

    Rules:
    - If confidence < threshold → BLOCK
    - If entry score < 70 → BLOCK
    - If block score >= 40 → BLOCK
    - If trap detected → BLOCK
    - If anomaly detected → BLOCK
    - If multiple conflicts → BLOCK
    - If extreme volatility → BLOCK
    - If exhaustion + low confidence → BLOCK
    """

    def __init__(self, 
                 min_confidence: int = 0,  # TEMP DISABLED FOR TESTING (was 75)
                 max_block_score: int = 40,
                 block_on_trap: bool = True,
                 block_on_anomaly: bool = True):
        self.min_confidence = min_confidence
        self.max_block_score = max_block_score
        self.block_on_trap = block_on_trap
        self.block_on_anomaly = block_on_anomaly

    def evaluate(self, context: MarketContext, 
                recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate signal against entry quality and risk rules.
        """
        confidence = context.get_score('confidence')
        block_score = context.get_score('block')
        entry_score = context.get_score('entry')

        # 1. Confidence check - TEMP DISABLED FOR TESTING
        # Bypassing minimum confidence threshold for backtest
        # if confidence < self.min_confidence:
        #     return self._block(f"Low confidence ({confidence:.0f} < {self.min_confidence})", "low_confidence")

        # DS Blueprint V2: Binary Options Overhaul Filters
        state_dict = context.market_state
        state = state_dict.get('state', 'UNKNOWN').upper() if isinstance(state_dict, dict) else (state_dict.upper() if isinstance(state_dict, str) else 'UNKNOWN')

        # 1. Indicator State Guard (Block toxic conditions)
        # [DISABLED per Boss request] Allow all states
        # if state in ['VOLATILITY_EXPANDING', 'LIQUIDITY_VOID', 'EXTREME']:
        #     return self._block(f"Trading blocked in toxic state: {state}", f"toxic_state_{state.lower()}")

        # 1.5 Market Structure Leader (Direction Alignment & Hard Blocks)
        ms_regime = context.market_structure.get('regime', 'UNKNOWN')
        signal_direction = recommendation.get('direction', '').upper()

        if ms_regime == 'CHOPPY':
            return self._block("Market Structure is CHOPPY (No clear direction)", "choppy_structure")
        elif ms_regime == 'BULLISH' and signal_direction == 'PUT':
            return self._block("Signal PUT conflicts with BULLISH Market Structure", "structure_mismatch")
        elif ms_regime == 'BEARISH' and signal_direction == 'CALL':
            return self._block("Signal CALL conflicts with BEARISH Market Structure", "structure_mismatch")

        # 2. MTF Alignment (M15 Guard) - REMOVED for M5 Reversal Strategies
        # 5-minute reversals often happen against the M15 color, so this guard is counterproductive.

        # 3. Dynamic Entry score check (M5 binary — strategy already filters; gate is secondary)
        min_entry_required = 68 if state == 'MEAN_REVERSION_ZONE' else 65
        # [DISABLED per Boss request] Make entry_score informational only
        # if 0 < entry_score < min_entry_required:
        #     return self._block(f"Low entry score ({entry_score:.0f} < {min_entry_required} for {state})", "low_entry")

        # 4. Block score check
        # [DISABLED per Boss request] Make block_score informational only
        # if block_score >= self.max_block_score:
        #     return self._block(f"High block score ({block_score:.0f} >= {self.max_block_score})", "high_block")

        # 5. Trap check
        if self.block_on_trap and context.traps.get('trap_detected'):
            trap_type = context.traps.get('trap_type', '?')
            return self._block(f"Trap detected ({trap_type})", "trap")

        # 6. Anomaly check
        if self.block_on_anomaly and context.anomaly.get('anomaly_detected'):
            return self._block("Market anomaly detected", "anomaly")

        # 7. Extreme Volatility check
        regime = context.volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            return self._block("Extreme market volatility", "extreme_vol")

        # 8. Exhaustion + Low Confidence check
        exhaustion = context.strength.get('exhaustion_risk', 0)
        if exhaustion > 70 and confidence < 85:
            return self._block(f"Exhaustion risk ({exhaustion:.0f}) with moderate confidence ({confidence:.0f})", "exhaustion")

        return {
            'approved': True,
            'reason': f"Approved: confidence={confidence:.0f}, block={block_score:.0f}",
            'blocked_by': None,
            'risk_score': int(block_score)
        }

    def _block(self, reason: str, code: str) -> Dict[str, Any]:
        return {
            'approved': False,
            'reason': reason,
            'blocked_by': code,
            'risk_score': 100
        }

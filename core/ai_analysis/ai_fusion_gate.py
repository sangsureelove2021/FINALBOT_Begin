from typing import List, Dict, Any
from .ai_engine import AIInsight


class AIFusionGate:
    """
    Fuses traditional strategy signals with AI insights.
    Produces final decision with confidence score.
    """

    def __init__(self, ai_weight: float = 0.4, strategy_weight: float = 0.6, veto_enabled: bool = True):
        """
        Args:
            ai_weight: weight given to AI confidence (0-1)
            strategy_weight: weight given to traditional strategies (0-1)
            veto_enabled: if True, NO_TRADE from AI cuts confidence by 50%
        """
        self.ai_weight = ai_weight
        self.strategy_weight = strategy_weight
        self.veto_enabled = veto_enabled

    def fuse_signals(self, traditional_signals: List[Dict[str, Any]], ai_insight: AIInsight) -> Dict[str, Any]:
        """
        Combine traditional strategy signals with AI analysis.

        Args:
            traditional_signals: list of signal dicts with keys: 'signal' (CALL/PUT), 'confidence', 'strategy', etc.
            ai_insight: AIInsight object from AIAnalysisEngine

        Returns:
            dict with keys: action, entry_score, block_score, confidence, ai_reason, ai_raw
        """
        avg_entry_score = self._calc_avg_entry_score(traditional_signals)
        avg_strategy_conf = self._calc_avg_confidence(traditional_signals)

        # Fuse confidence
        confidence = (avg_strategy_conf * self.strategy_weight) + (ai_insight.confidence * self.ai_weight)

        # Veto: if AI says NO_TRADE and veto enabled, reduce confidence by 50%
        if self.veto_enabled and ai_insight.action == "NO_TRADE":
            confidence *= 0.5

        final_action = self._decide_action(ai_insight, traditional_signals, confidence)

        return {
            "action": final_action,
            "entry_score": avg_entry_score,
            "block_score": self._calc_block_score(traditional_signals),
            "confidence": confidence,
            "ai_reason": ai_insight.reason,
            "ai_raw": ai_insight.raw_response[:200]
        }

    def _decide_action(self, ai: AIInsight, trad_signals: List[Dict], confidence: float) -> str:
        """Determine final action based on AI and traditional signals."""
        # If AI says NO_TRADE and post-veto confidence < 50, respect AI
        if ai.action == "NO_TRADE" and confidence < 50:
            return "NO_TRADE"

        # Otherwise, majority vote of traditional signals
        calls = sum(1 for s in trad_signals if s.get('signal') == 'CALL')
        puts = sum(1 for s in trad_signals if s.get('signal') == 'PUT')

        if calls > puts:
            return "CALL"
        elif puts > calls:
            return "PUT"
        else:
            # Tie: respect AI if available and not NO_TRADE
            if ai.action in ("CALL", "PUT"):
                return ai.action
            return "NO_TRADE"

    def _calc_avg_entry_score(self, trad_signals: List[Dict]) -> float:
        """Calculate average entry score from traditional signals."""
        if not trad_signals:
            return 0.0
        total = 0.0
        count = 0
        for s in trad_signals:
            # Some signals may have entry_score field, otherwise use confidence as proxy
            score = s.get('entry_score', s.get('confidence', 0))
            if isinstance(score, (int, float)):
                total += score
                count += 1
        return total / count if count > 0 else 0.0

    def _calc_avg_confidence(self, trad_signals: List[Dict]) -> float:
        """Calculate average confidence from traditional signals."""
        if not trad_signals:
            return 0.0
        total = 0.0
        count = 0
        for s in trad_signals:
            conf = s.get('confidence', 0)
            if isinstance(conf, (int, float)):
                total += conf
                count += 1
        return total / count if count > 0 else 0.0

    def _calc_block_score(self, trad_signals: List[Dict]) -> float:
        """Calculate block score (risk blocking factor). Lower is better."""
        if not trad_signals:
            return 0.0
        # Block score is average of 'block_score' if present, else low by default
        total = 0.0
        count = 0
        for s in trad_signals:
            block = s.get('block_score', 10)  # default low block
            if isinstance(block, (int, float)):
                total += block
                count += 1
        return total / count if count > 0 else 0.0

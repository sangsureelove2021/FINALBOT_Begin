"""
Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main pipeline that orchestrates the full analysis flow.

Flow:
    Candles → ContextBuilder → Scoring → Strategy → ExecutionGate → Signal
"""

from typing import Dict, List
from datetime import datetime
import uuid
import pandas as pd

from core.models.market_context import MarketContext
from core.models.signal import Signal, SignalAction, SignalQuality
from core.orchestration.context_builder import ContextBuilder
from core.scoring.confidence_scorer import ConfidenceScorer
from core.scoring.entry_scorer import EntryScorer
from core.scoring.block_scorer import BlockScorer


class Pipeline:
    """
    Main pipeline orchestrator.
    
    Stages:
        1. Build context (all engines run)
        2. Compute scores
        3. Run strategies
        4. Execution gate (signal_veto)
        5. Return final signal
    """
    
    def __init__(self, 
                 context_builder: ContextBuilder,
                 strategies: List = None,
                 execution_gate = None,
                 confidence_scorer: ConfidenceScorer = None,
                 entry_scorer: EntryScorer = None,
                 block_scorer: BlockScorer = None):
        
        self.context_builder = context_builder
        self.strategies = strategies or []
        self.execution_gate = execution_gate
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.entry_scorer = entry_scorer or EntryScorer()
        self.block_scorer = block_scorer or BlockScorer()
    
    def execute(self, symbol: str, candles: Dict[str, pd.DataFrame],
               timeframe: str = 'M5') -> Signal:
        """
        Execute full pipeline.
        
        Returns:
            Signal (CALL, PUT, NO_SIGNAL, or BLOCKED)
        """
        # === STAGE 1: Build context ===
        context = self.context_builder.build(symbol, candles, timeframe)
        
        if context.has_errors() and len(context.errors) > 5:
            return self._create_blocked_signal(
                symbol, timeframe, context, "Too many errors in context build"
            )
        
        # === STAGE 2: Compute scores ===
        context.set_score('confidence', self.confidence_scorer.score(context))
        context.set_score('entry', self.entry_scorer.score(context))
        context.set_score('block', self.block_scorer.score(context))
        context.aggregated_score = context.get_score('confidence')
        
        # === STAGE 3: Run strategies ===
        recommendation = self._evaluate_strategies(context)
        context.strategy_recommendation = recommendation
        
        if recommendation.get('action') == 'NO_SIGNAL':
            return self._create_no_signal(symbol, timeframe, context, recommendation)
        
        # === STAGE 4: Execution Gate (signal veto) ===
        if self.execution_gate:
            gate_decision = self.execution_gate.evaluate(context, recommendation)
            context.execution_decision = gate_decision
            
            if not gate_decision.get('approved'):
                return self._create_blocked_signal(
                    symbol, timeframe, context,
                    gate_decision.get('reason', 'Blocked by execution gate')
                )
        
        # === STAGE 5: Final signal ===
        return self._create_signal(symbol, timeframe, context, recommendation)
    
    def _evaluate_strategies(self, context: MarketContext) -> Dict:
        """Run all eligible strategies and pick best"""
        if not self.strategies:
            return {'action': 'NO_SIGNAL', 'confidence': 0,
                    'reason': 'No strategies registered'}
        
        best = None
        best_score = -1
        
        for strategy in self.strategies:
            if not strategy.is_eligible(context):
                continue
            
            try:
                result = strategy.evaluate(context)
                
                # Combined score: entry quality minus block penalty
                entry = result.get('entry_score', 50)
                block = result.get('block_score', 0)
                combined = entry - (block * 0.5)
                
                if combined > best_score:
                    best_score = combined
                    best = result
                    best['strategy_name'] = strategy.strategy_name
            except Exception as e:
                context.add_warning(f"Strategy {strategy.strategy_name} error: {e}")
        
        if best is None:
            return {'action': 'NO_SIGNAL', 'confidence': 0,
                    'reason': 'No eligible strategies'}
        
        return best
    
    def _create_signal(self, symbol: str, timeframe: str,
                      context: MarketContext, recommendation: Dict) -> Signal:
        """Create actionable signal"""
        action_str = recommendation.get('action', 'NO_SIGNAL')
        action = SignalAction[action_str] if action_str in SignalAction.__members__ \
                 else SignalAction.NO_SIGNAL
        
        confidence = recommendation.get('confidence', 50)
        quality = self._compute_quality(confidence)
        
        return Signal(
            signal_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            symbol=symbol,
            timeframe=timeframe,
            action=action,
            confidence=confidence,
            quality=quality,
            strategy_name=recommendation.get('strategy_name', 'unknown'),
            reason=recommendation.get('reason', ''),
            score_snapshot={
                'confidence': context.get_score('confidence'),
                'entry': context.get_score('entry'),
                'block': context.get_score('block'),
                'aggregated': context.aggregated_score,
            },
        )
    
    def _create_no_signal(self, symbol: str, timeframe: str,
                         context: MarketContext, recommendation: Dict) -> Signal:
        """Create NO_SIGNAL signal"""
        return Signal(
            signal_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            symbol=symbol,
            timeframe=timeframe,
            action=SignalAction.NO_SIGNAL,
            confidence=recommendation.get('confidence', 0),
            quality=SignalQuality.LOW,
            strategy_name=recommendation.get('strategy_name', 'none'),
            reason=recommendation.get('reason', 'No clear opportunity'),
        )
    
    def _create_blocked_signal(self, symbol: str, timeframe: str,
                              context: MarketContext, reason: str) -> Signal:
        """Create BLOCKED signal"""
        return Signal(
            signal_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            symbol=symbol,
            timeframe=timeframe,
            action=SignalAction.BLOCKED,
            confidence=0,
            quality=SignalQuality.LOW,
            strategy_name='none',
            reason=reason,
            blocked_by='execution_gate',
            veto_reason=reason,
        )
    
    def _compute_quality(self, confidence: int) -> SignalQuality:
        """Map confidence to quality tier"""
        if confidence >= 90:
            return SignalQuality.PREMIUM
        elif confidence >= 75:
            return SignalQuality.HIGH
        elif confidence >= 60:
            return SignalQuality.MEDIUM
        else:
            return SignalQuality.LOW

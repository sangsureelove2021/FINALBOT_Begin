"""
Context Builder

Assembles MarketContext by running engines in tier order.
This is the central wiring of the Intelligence OS.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import pandas as pd

from core.models.market_context import MarketContext
from core.engines.engine_registry import EngineRegistry
from core.interfaces.context_interface import IContextBuilder


class ContextBuilder(IContextBuilder):
    """
    Builds MarketContext from candle data by running registered engines.
    
    Execution flow:
        1. Validate input
        2. Run Tier 1 engines (trend, strength, volatility, structure, mtf)
        3. Run Tier 2 engines (market state classification)
        4. Run Tier 3 engines (price action)
        5. Run Tier 4 engines (detection)
        6. Run Tier 5 engines (behavior)
        7. Run Tier 6 engines (synthesis)
        8. Run Tier 7 engines (quality)
    """
    
    def __init__(self, registry: EngineRegistry):
        self.registry = registry
    
    def build(self, symbol: str, candles: Dict[str, pd.DataFrame],
              timeframe: str = 'M5') -> MarketContext:
        """
        Build complete MarketContext.
        
        Args:
            symbol: Trading pair (e.g. 'EURUSD')
            candles: Dict of {timeframe: DataFrame}
            timeframe: Primary timeframe for analysis
        
        Returns:
            Populated MarketContext
        """
        # Initialize context
        primary_df = candles.get(timeframe)
        
        if primary_df is None or primary_df.empty:
            return self._empty_context(symbol, timeframe)
        
        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            timeframe=timeframe,
            candles=candles,
            current_price=float(primary_df['close'].iloc[-1]),
            candle_index=len(primary_df) - 1,
        )
        
        # Run all tiers in order
        for tier_num in sorted(self.registry.list_tiers()):
            self._run_tier(tier_num, context, candles, primary_df)
        
        return context
    
    def _run_tier(self, tier_num: int, context: MarketContext,
                 candles: Dict[str, pd.DataFrame],
                 primary_df: pd.DataFrame) -> None:
        """Run all engines for a single tier"""
        engines = self.registry.get_by_tier(tier_num)
        
        for engine in engines:
            try:
                # Tier 6-8 synthesis engines read the MarketContext directly
                # Tier 1 MTF needs the candles dict (multi-timeframe)
                # Tier 1-5 analytical engines need the primary dataframe
                if tier_num >= 6:
                    result = engine.analyze(context=context)
                elif 'mtf' in engine.engine_name.lower():
                    result = engine.analyze(candles_dict=candles)
                elif tier_num == 2 and engine.engine_name == 'market_state_classifier':
                    # M5 binary strategies: classify on M5 candles (fallback M15 → primary)
                    m5_df = candles.get('M5')
                    m15_df = candles.get('M15')
                    if m5_df is not None and len(m5_df) >= 100:
                        result = engine.analyze(m5_df)
                    elif m15_df is not None and not m15_df.empty:
                        result = engine.analyze(m15_df)
                    else:
                        # Fallback to primary if M15 is missing
                        tier1 = {
                            'direction': context.trend.get('direction', 'NONE') if context.trend else 'NONE',
                            'atr_percentile': context.volatility.get('atr_percentile', 50.0) if context.volatility else 50.0,
                            'trend_strength': context.trend.get('strength', 0) if context.trend else 0,
                            'strength': context.strength.get('strength_score', 0) if context.strength else 0,
                            'type': context.trend.get('type', '') if context.trend else '',
                            'regime': context.volatility.get('regime', 'NORMAL') if context.volatility else 'NORMAL',
                            'exhaustion_risk': context.strength.get('exhaustion_risk', 0) if context.strength else 0,
                            'bos_detected': context.structure.get('bos_detected', False) if context.structure else False,
                        }
                        result = engine.analyze(primary_df, tier1=tier1)
                else:
                    result = engine.analyze(primary_df)
                
                # Map result to context based on engine name
                self._apply_engine_result(context, engine.engine_name, result)
                context.mark_engine_executed(engine.engine_name)
                
            except Exception as e:
                context.add_error(f"{engine.engine_name} failed: {str(e)}")
    
    def _apply_engine_result(self, context: MarketContext,
                             engine_name: str, result: Dict[str, Any]) -> None:
        """
        Apply engine result to appropriate context field.
        Maps engine_name -> context attribute.
        """
        # Mapping table: engine name to context attribute
        mapping = {
            'trend_engine': 'trend',
            'strength_engine': 'strength',
            'volatility_engine': 'volatility',
            'structure_engine': 'structure',
            'market_structure_engine': 'market_structure',
            'mtf_engine': 'mtf',
            'market_state_classifier': 'market_state',
            'regime_quality_scorer': 'regime_quality',
            'candle_pattern_analyzer': 'candle_patterns',
            'price_action_handler': 'price_action',
            'trap_detector': 'traps',
            'noise_detector': 'noise',
            'liquidity_engine': 'liquidity',
            'divergence_analyzer': 'divergence',
            'transition_analyzer': 'transition',
            'conflict_analyzer': 'conflict',
            'efficiency_analyzer': 'efficiency',
            'persistence_analyzer': 'persistence',
            'continuation_analyzer': 'continuation',
            'market_pressure_analyzer': 'orderflow',
            'anomaly_detector': 'anomaly',
            'context_synthesizer': 'synthesized_context',
            'probability_estimator': 'move_probability',
            'signal_quality_scorer': 'signal_quality',
            'confidence_framework': 'confidence_framework',
            'explainability_engine': 'explainability',
            'behavior_analyzer': 'orderflow',  # Map to closest field
        }
        
        attr = mapping.get(engine_name)
        if attr and hasattr(context, attr):
            if engine_name == 'market_state_classifier':
                # Revert to dict to avoid crashes in ContextSynthesizer & ExplainabilityEngine
                setattr(context, attr, result)
            else:
                setattr(context, attr, result)
    
    def _empty_context(self, symbol: str, timeframe: str) -> MarketContext:
        """Return empty context when no data available"""
        ctx = MarketContext(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            timeframe=timeframe,
            current_price=0.0,
        )
        ctx.add_error("No candle data available")
        return ctx

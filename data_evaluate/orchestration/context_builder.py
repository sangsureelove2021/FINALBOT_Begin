"""
Context Builder

Assembles MarketContext by running engines in tier order.
This is the central wiring of the Intelligence OS.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import pandas as pd

from data_evaluate.models.market_context import MarketContext
from data_evaluate.orchestration.engine_registry import EngineRegistry
from data_evaluate.interfaces.context_interface import IContextBuilder


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
        primary_df = candles[timeframe]
        
        if primary_df is None or primary_df.empty:
            from data_evaluate.exceptions import InvalidInputError
            raise InvalidInputError("Missing primary_df for context builder")
        
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
                    # Strict payload construction for Market State Classifier
                    # No fallbacks. Fail fast if required data is missing.
                    if 'M5' not in candles or candles['M5'] is None or candles['M5'].empty:
                        from data_evaluate.exceptions import InvalidInputError
                        raise InvalidInputError(f"[{engine.engine_name}] FAIL-FAST: M5 candle data is missing")
                        
                    if not context.trend or not context.strength or not context.volatility or not context.structure or not context.mtf:
                        from data_evaluate.exceptions import InvalidInputError
                        raise InvalidInputError(f"[{engine.engine_name}] FAIL-FAST: Missing Tier 1 context data")

                    m5_df = candles['M5']
                    latest_m5 = m5_df.iloc[-1].to_dict()
                    
                    # Assuming price_action might be part of the m5 features or we strictly require it
                    pa_data = {}
                    if 'move_quality' in latest_m5:
                        pa_data['move_quality'] = latest_m5['move_quality']
                        if 'wick_dominance' not in latest_m5:
                            from data_evaluate.exceptions import InvalidInputError
                            raise InvalidInputError(f"[{engine.engine_name}] FAIL-FAST: 'wick_dominance' missing")
                        pa_data['wick_dominance'] = latest_m5['wick_dominance']
                        if 'sr_interaction' not in latest_m5:
                            from data_evaluate.exceptions import InvalidInputError
                            raise InvalidInputError(f"[{engine.engine_name}] FAIL-FAST: 'sr_interaction' missing")
                        pa_data['sr_interaction'] = latest_m5['sr_interaction']
                    elif context.price_action:
                        pa_data = context.price_action
                    else:
                        # Fail-Fast if no price_action data is available
                        from data_evaluate.exceptions import InvalidInputError
                        raise InvalidInputError(f"[{engine.engine_name}] FAIL-FAST: price_action data is missing")
                        
                    payload = {
                        'm5': latest_m5,
                        'price_action': pa_data,
                        'ohlcv': latest_m5
                    }
                    
                    kwargs = {
                        'trend_data': context.trend,
                        'strength_data': context.strength,
                        'volatility_data': context.volatility,
                        'structure_data': context.structure,
                        'mtf_data': context.mtf,
                        'symbol': context.symbol
                    }
                    
                    result = engine.analyze(payload, **kwargs)
                else:
                    result = engine.analyze(primary_df)
                
                # Map result to context based on engine name
                self._apply_engine_result(context, engine.engine_name, result)
                context.mark_engine_executed(engine.engine_name)
                
            except Exception as e:
                raise
    
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
        
        attr = mapping[engine_name]
        if attr and hasattr(context, attr):
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

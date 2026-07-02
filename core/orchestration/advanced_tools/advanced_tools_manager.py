import logging
import pandas as pd
from typing import Dict, Any

from core.orchestration.advanced_tools.behavior_analyzer import BehaviorAnalyzer
from core.orchestration.advanced_tools.candle_pattern_analyzer import CandlePatternAnalyzer
from core.orchestration.advanced_tools.conflict_analyzer import ConflictAnalyzer
from core.orchestration.advanced_tools.continuation_analyzer import ContinuationAnalyzer
from core.orchestration.advanced_tools.divergence_analyzer import DivergenceAnalyzer
from core.orchestration.advanced_tools.efficiency_analyzer import EfficiencyAnalyzer
from core.orchestration.advanced_tools.persistence_analyzer import PersistenceAnalyzer
from core.orchestration.advanced_tools.price_action_handler import PriceActionHandler
from core.orchestration.advanced_tools.transition_analyzer import TransitionAnalyzer
from core.orchestration.trap_detector import TrapDetector

logger = logging.getLogger("AdvancedToolsManager")

class AdvancedToolsManager:
    def __init__(self):
        self.behavior = BehaviorAnalyzer()
        self.candle_pattern = CandlePatternAnalyzer()
        self.conflict = ConflictAnalyzer()
        self.continuation = ContinuationAnalyzer()
        self.divergence = DivergenceAnalyzer()
        self.efficiency = EfficiencyAnalyzer()
        self.persistence = PersistenceAnalyzer()
        self.transition = TransitionAnalyzer()
        
        # This was previously in indicator_store
        self.price_action = PriceActionHandler()
        self.trap_detector = TrapDetector()

    def analyze_all(self, symbol: str, basic_payload: Dict[str, Any], df_m5: Any) -> Dict[str, Any]:
        """
        Runs all advanced analyzers using the M5 DataFrame and basic payload.
        Returns a dictionary of all advanced metrics.
        """
        results = {}
        
        if not isinstance(df_m5, pd.DataFrame) or df_m5.empty:
            raise ValueError(f"advanced_tools.analyze_all: df_m5 is empty or invalid for symbol {symbol}")
        
        # Run specialized analyzers
        candle_data = self.candle_pattern.analyze(df_m5)
        trap_data = self.trap_detector.analyze(df_m5)
        pa_data = self.price_action.analyze(df_m5)
        
        # Format Price Action for Group B
        patterns = candle_data['patterns_detected']
        
        # Use simple heuristic for body strength and wick dominance
        body_size = pa_data['recent_body_size']
        wick_ratio = pa_data['wick_to_body_ratio']
        
        m5_basic = basic_payload['m5']
        meta_basic = basic_payload['meta']
        close_price = meta_basic['close']
        
        # Override support/resistance with fractal logic from PA if available
        fractal_support = pa_data['fractal_support']
        fractal_resistance = pa_data['fractal_resistance']
        
        support = fractal_support if fractal_support > 0 else m5_basic['support']
        resistance = fractal_resistance if fractal_resistance > 0 else m5_basic['resistance']
        atr = m5_basic['atr14']
        
        # Inject back into m5 to prevent data loss in the 69-field contract
        m5_basic['support'] = support
        m5_basic['resistance'] = resistance
        m5_basic['volume_trend'] = pa_data['volume_momentum']
        
        pivot = m5_basic['pivot']
        rejection_zone = "NONE"
        sr_interaction = "NONE"
        if close_price and isinstance(close_price, (int, float)) and close_price > 0:
            threshold = atr * 0.5 if (atr and isinstance(atr, (int, float)) and atr > 0) else close_price * 0.001
            
            # rejection_zone
            if pivot and isinstance(pivot, (int, float)) and pivot > 0 and abs(close_price - pivot) <= threshold:
                rejection_zone = "AT_PIVOT"
            elif support and isinstance(support, (int, float)) and support > 0 and abs(close_price - support) <= threshold:
                rejection_zone = "AT_SUPPORT"
            elif resistance and isinstance(resistance, (int, float)) and resistance > 0 and abs(close_price - resistance) <= threshold:
                rejection_zone = "AT_RESISTANCE"

            # sr_interaction
            if pivot and isinstance(pivot, (int, float)) and pivot > 0 and abs(close_price - pivot) <= threshold:
                sr_interaction = "TESTING_PIVOT"
            elif resistance and isinstance(resistance, (int, float)) and resistance > 0 and abs(close_price - resistance) <= threshold:
                sr_interaction = "TESTING_RESISTANCE"
            elif support and isinstance(support, (int, float)) and support > 0 and abs(close_price - support) <= threshold:
                sr_interaction = "TESTING_SUPPORT"
        
        # trap_alert mapping
        trap_detected = trap_data['trap_detected']
        trap_type = trap_data['trap_type']
        trap_alert = "NONE"
        if trap_detected:
            if trap_type == 'bear':
                trap_alert = "BEAR_TRAP"
            elif trap_type == 'bull':
                trap_alert = "BULL_TRAP"
            else:
                trap_alert = "TRUE"

        results['price_action'] = {
            'pattern': patterns[0] if patterns else 'NONE',
            'last_candle_bias': candle_data['last_candle_color'],
            'last_candle': candle_data['last_candle_color'],
            'body_strength': 'STRONG' if body_size > 0.1 else 'WEAK',
            'rejection_zone': rejection_zone,
            'wick_dominance': 'HIGH_WICK' if wick_ratio > 1.0 else 'LOW_WICK',
            'momentum_bias': pa_data['directional_bias'],
            'move_quality': 'CLEAN' if pa_data['move_type'] == 'CLEAN_TRENDING' else ('CHAOTIC' if pa_data['move_type'] == 'CHAOTIC' else ('NOISY' if pa_data['move_type'] == 'NOISY' else 'NORMAL')),
            'trap_alert': trap_alert,
            'sr_interaction': sr_interaction,
            'volume_momentum': pa_data['volume_momentum']
        }
            
        # Run all specialized analyzers
        results['behavior'] = self.behavior.analyze(df_m5)
        results['candle_pattern'] = candle_data
        results['trap_detector'] = trap_data
        results['conflict'] = self.conflict.analyze(df_m5)
        results['continuation'] = self.continuation.analyze(df_m5)
        results['divergence'] = self.divergence.analyze(df_m5)
        results['efficiency'] = self.efficiency.analyze(df_m5)
        results['persistence'] = self.persistence.analyze(df_m5)
        results['transition'] = self.transition.analyze(df_m5)

        return results

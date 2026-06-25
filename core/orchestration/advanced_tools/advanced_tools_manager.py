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
            return results
        
        # Run specialized analyzers
        candle_data = self.candle_pattern.analyze(df_m5)
        trap_data = self.trap_detector.analyze(df_m5)
        pa_data = self.price_action.analyze(df_m5)
        
        # Format Price Action for Group B
        patterns = candle_data.get('patterns_detected', [])
        
        # Use simple heuristic for body strength and wick dominance
        body_size = pa_data.get('recent_body_size', 0)
        wick_ratio = pa_data.get('wick_to_body_ratio', 0)
        
        m5_basic = basic_payload.get('m5', {})
        meta_basic = basic_payload.get('meta', {})
        close_price = meta_basic.get('close', 0)
        support = m5_basic.get('support', 0)
        resistance = m5_basic.get('resistance', 0)
        atr = m5_basic.get('atr14', 0)
        
        sr_interaction = "NONE"
        if close_price and isinstance(close_price, (int, float)) and close_price > 0:
            threshold = atr * 0.5 if (atr and isinstance(atr, (int, float)) and atr > 0) else close_price * 0.001
            if resistance and isinstance(resistance, (int, float)) and resistance > 0 and abs(close_price - resistance) <= threshold:
                sr_interaction = "TESTING_RESISTANCE"
            elif support and isinstance(support, (int, float)) and support > 0 and abs(close_price - support) <= threshold:
                sr_interaction = "TESTING_SUPPORT"
        
        results['price_action'] = {
            'pattern': patterns[0] if patterns else 'NONE',
            'last_candle_bias': candle_data.get('last_candle_color', 'NEUTRAL'),
            'body_strength': 'STRONG' if body_size > 0.1 else 'WEAK',
            'wick_dominance': 'HIGH' if wick_ratio > 1.0 else 'LOW',
            'momentum_bias': pa_data.get('directional_bias', 'NEUTRAL'),
            'move_quality': 'CLEAN' if pa_data.get('move_type') == 'CLEAN_TRENDING' else ('CHOPPY' if pa_data.get('move_type') in ['NOISY', 'CHAOTIC'] else 'NORMAL'),
            'trap_alert': trap_data.get('trap_detected', False),
            'sr_interaction': sr_interaction
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

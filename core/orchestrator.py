import logging
import pandas as pd
from typing import Dict, Any, Optional

from core.indicator_store import store
from core.engines.market_state_classifier import MarketStateClassifier
from core.logging.trade_logger import TradeLogger

logger = logging.getLogger("Orchestrator")

class Orchestrator:
    """
    ผู้จัดการส่วนกลาง (Central Orchestrator)
    ทำหน้าที่ดึงข้อมูลจาก IndicatorStore ส่งให้ Engines วิเคราะห์
    ส่งผลลัพธ์ให้ MarketStateClassifier และรวบรวมข้อมูลส่งให้ TradeLogger
    """
    
    def __init__(self, trade_logger: TradeLogger):
        self.trade_logger = trade_logger
        
        # Initialize Market State Classifier
        self.classifier = None
        try:
            self.classifier = MarketStateClassifier()
            logger.info("MarketStateClassifier initialized successfully in Orchestrator")
        except Exception as e:
            logger.error(f"Failed to initialize MarketStateClassifier: {e}")
            
        # TODO: Initialize the 5 engines here in the future
        
    def process_cycle(self, symbol: str, candles_dict: Dict[str, pd.DataFrame], ai_context: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        """
        รันกระบวนการวิเคราะห์ 1 รอบสำหรับคู่เงิน
        """
        primary_df = candles_dict.get('M5')
        if primary_df is None or primary_df.empty:
            logger.warning(f"No M5 data for {symbol} in Orchestrator")
            return None
            
        # 1. Get pre-calculated payload from IndicatorStore
        payload = store.get_payload(symbol)
        indicators_primary = payload.get('m5', {})
        
        # 2. Prepare Tier 1 Data for Classifier
        # (Temporary mock-up until the 5 engines are connected)
        ema20_val = indicators_primary.get('ema20', 0.0)
        ema50_val = indicators_primary.get('ema50', 0.0)
        direction = 'UP' if ema20_val > ema50_val else 'DOWN'
        
        atr_percentile = 50.0
        rsi_val = indicators_primary.get('rsi14', 50.0)
        strength = abs(rsi_val - 50.0) * 2  # ยิ่งใกล้ 50 ยิ่งต่ำ
        
        bb_width_val = indicators_primary.get('bb_width', 0.0)
        regime = 'ranging' if bb_width_val < 0.01 else 'trending'
        
        tier1 = {
            'direction': direction,
            'atr_percentile': atr_percentile,
            'trend_strength': strength,
            'strength': strength,
            'type': 'trend' if regime == 'trending' else 'range',
            'regime': regime.upper(),
            'exhaustion_risk': 0.0,
            'bos_detected': False
        }
        
        # 3. Market State Classification
        market_state = {
            'state': 'UNKNOWN',
            'trend_direction': 'NEUTRAL',
            'trend_type': 'neutral',
            'trend_strength': strength,
            'patterns': [],
            'atr_percentile': atr_percentile,
            'volatility_label': 'normal',
            'compression_quality': 0.0,
            'regime': regime
        }
        
        if self.classifier is not None:
            try:
                result = self.classifier.analyze(primary_df, tier1=tier1)
                
                if isinstance(result, dict):
                    metrics = result.get('metrics', {})
                    market_state['state'] = result.get('state', 'UNKNOWN')
                    market_state['trend_direction'] = metrics.get('trend_direction', 'NONE')
                    market_state['compression_quality'] = 100.0 if metrics.get('compression_detected', False) else 0.0
                    market_state['regime'] = 'ranging' if market_state['trend_direction'] == 'NONE' else 'trending'
            except Exception as e:
                logger.error(f"MarketStateClassifier error: {e}")
                
        # 4. Create final log data via TradeLogger
        log_data = self.trade_logger.build_log_data(
            symbol=symbol,
            candles_dict=candles_dict,
            market_state=market_state,
            primary_timeframe='M5',
            ai_context=ai_context
        )
        
        return log_data

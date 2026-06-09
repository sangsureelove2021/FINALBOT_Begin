import numpy as np
import pandas as pd
from typing import Dict, Any

from core.engines.base_engine import BaseEngine

class MarketStateClassifier(BaseEngine):
    """Tier 2: Market State Classifier
    M5 Binary Options Overhaul.
    Detects market condition suitable for 5-minute expirations.
    """
    
    ENGINE_NAME = "market_state_classifier"
    ENGINE_VERSION = "3.0.0"
    TIER = 2
    MIN_CANDLES = 100
    
    def __init__(self, config=None):
        super().__init__(config)
    
    def analyze(self, candles_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
        try:
            if candles_df is None or len(candles_df) < self.MIN_CANDLES:
                return self.get_neutral_state()
                
            state = self._classify(candles_df)
            quality = self._calculate_quality(state)
            
            return {
                'state': state,
                'quality_score': quality,
                'tradeable': self._is_tradeable(state, quality),
                'description': self._describe_state(state),
                'confidence': min(100, quality + 5),
            }
        except Exception as e:
            print(f"[ERR] MarketStateClassifier error: {e}")
            return self.get_neutral_state()
            
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        try:
            high, low, close = df['high'], df['low'], df['close']
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            atr = tr.ewm(alpha=1/period, adjust=False).mean()
            
            up_move = high.diff()
            down_move = -low.diff()
            pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            pos_dm_smooth = pd.Series(pos_dm).ewm(alpha=1/period, adjust=False).mean()
            neg_dm_smooth = pd.Series(neg_dm).ewm(alpha=1/period, adjust=False).mean()
            
            pos_di = 100 * (pos_dm_smooth / (atr + 1e-9))
            neg_di = 100 * (neg_dm_smooth / (atr + 1e-9))
            
            dx = 100 * (abs(pos_di - neg_di) / (pos_di + neg_di + 1e-9))
            adx = dx.ewm(alpha=1/period, adjust=False).mean()
            
            return float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 20.0
        except:
            return 20.0

    def _classify(self, df: pd.DataFrame) -> str:
        """Classify into binary-friendly states."""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Bollinger Bands
        bb_window = 20
        bb_std = 2.0
        rolling_mean = close.rolling(window=bb_window).mean()
        rolling_std = close.rolling(window=bb_window).std(ddof=0)
        upper_band = rolling_mean + (bb_std * rolling_std)
        lower_band = rolling_mean - (bb_std * rolling_std)
        
        # Bandwidth
        bandwidth = (upper_band - lower_band) / rolling_mean
        current_bw = bandwidth.iloc[-1]
        avg_bw = bandwidth.iloc[-20:].mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        adx = self._calculate_adx(df)
        
        # ATR relative
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        current_atr = atr.iloc[-1]
        avg_atr = atr.iloc[-100:].mean()
        atr_pct = (current_atr / (avg_atr + 1e-9)) * 100
        
        # 1. LIQUIDITY VOID
        if atr_pct < 20 or current_bw < 0.0005:
            # Very tight, unplayable
            return 'LIQUIDITY_VOID'
            
        # 2. VOLATILITY EXPANDING (Dangerous to fade)
        if current_bw > avg_bw * 1.5 and adx > 25:
            return 'VOLATILITY_EXPANDING'
            
        # 3. EXHAUSTION ZONE (Price outside BB and RSI stretched)
        is_upper_pierce = close.iloc[-1] > upper_band.iloc[-1] or high.iloc[-1] > upper_band.iloc[-1]
        is_lower_pierce = close.iloc[-1] < lower_band.iloc[-1] or low.iloc[-1] < lower_band.iloc[-1]
        
        if (is_upper_pierce and current_rsi >= 65) or (is_lower_pierce and current_rsi <= 35):
            return 'EXHAUSTION_ZONE'
            
        # 4. MEAN REVERSION ZONE (ranging / low-momentum — primary M5 binary edge)
        if adx < 32 and current_bw <= avg_bw * 1.4:
            return 'MEAN_REVERSION_ZONE'

        # 5. Moderate momentum still tradable for M5 reversals
        if adx < 38 and current_bw <= avg_bw * 1.6:
            return 'MEAN_REVERSION_ZONE'
            
        # 6. DEFAULT — only block truly chaotic conditions
        if adx > 42 or current_bw > avg_bw * 2.0:
            return 'CHOPPY_UNCERTAIN'

        return 'MEAN_REVERSION_ZONE'

    def _calculate_quality(self, state: str) -> int:
        quality_map = {
            'EXHAUSTION_ZONE': 95,
            'MEAN_REVERSION_ZONE': 85,
            'VOLATILITY_EXPANDING': 30,
            'CHOPPY_UNCERTAIN': 20,
            'LIQUIDITY_VOID': 10,
        }
        return quality_map.get(state, 50)
    
    def _is_tradeable(self, state: str, quality: int) -> bool:
        non_tradeable = ['CHOPPY_UNCERTAIN', 'LIQUIDITY_VOID', 'VOLATILITY_EXPANDING']
        if state in non_tradeable:
            return False
        return quality >= 40
    
    def _describe_state(self, state: str) -> str:
        descriptions = {
            'EXHAUSTION_ZONE': 'Price over-extended from mean, ripe for 5m reversal',
            'MEAN_REVERSION_ZONE': 'Low momentum ranging market, perfect for BB bounces',
            'VOLATILITY_EXPANDING': 'High momentum breakout, dangerous to fade',
            'LIQUIDITY_VOID': 'Low volume dead zone / sparse trading (Safety lock)',
            'CHOPPY_UNCERTAIN': 'Choppy chaotic market - high noise fallback',
        }
        return descriptions.get(state, 'Unknown state')
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'state': 'CHOPPY_UNCERTAIN', 'quality_score': 20,
            'tradeable': False, 'description': 'Insufficient data',
            'confidence': 0,
        }

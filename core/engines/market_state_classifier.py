import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from collections import deque

from core.engines.base_engine import BaseEngine


class MarketStateClassifier(BaseEngine):
    """
    Tier 2: Market State Classifier - Optimized for 5-minute Binary Options
    
    Key optimizations for 5-min trading:
    - Reduced indicator periods for faster response (ADX 10, RSI 7)
    - Adaptive thresholds based on recent volatility
    - Momentum divergence detection for early reversals
    - Volume-confirmed breakouts
    - State transition smoothing to reduce false flips
    - Dynamic noise filtering with weighted efficiency
    
    Market States (10 types):
    - TRENDING_STRONG      : Clear directional move with strong momentum
    - TRENDING_WEAK        : Directional bias but low conviction
    - SIDEWAY_RANGE        : Price oscillating between clear levels
    - BREAKOUT_EMERGING    : Volatility expansion after compression
    - REVERSAL_FORMING     : Potential trend change, early signals
    - ACCUMULATION         : Smart money buying, lower wicks / volume pattern
    - DISTRIBUTION         : Smart money selling, upper wicks / volume pattern
    - CHOPPY_UNCERTAIN     : Chaotic movement, high noise, avoid trading
    - LIQUIDITY_VOID       : Extreme low volume / dead market
    - UNCLEAR              : Insufficient signals or mixed indicators
    
    Each classification includes confidence score (0-100), quality score (0-100),
    tradeability flag, stability score (0-100), and descriptive text.
    """
    
    ENGINE_NAME = "market_state_classifier"
    ENGINE_VERSION = "5.0.0"  # Optimized for 5-min BO
    TIER = 2
    MIN_CANDLES = 50  # Reduced from 100 for 5-min responsiveness
    
    # State list for validation
    VALID_STATES = [
        'TRENDING_STRONG', 'TRENDING_WEAK', 'SIDEWAY_RANGE',
        'BREAKOUT_EMERGING', 'REVERSAL_FORMING', 'ACCUMULATION',
        'DISTRIBUTION', 'CHOPPY_UNCERTAIN', 'LIQUIDITY_VOID', 'UNCLEAR'
    ]
    
    # State transition smoothing - prevent rapid flipping
    _state_history: deque
    _max_history = 5
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._state_history = deque(maxlen=self._max_history)
    
    def analyze(self, candles_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market state based on candle data and optional precomputed
        intelligence from other Tier 1 engines.
        
        Args:
            candles_df: OHLCV DataFrame with columns 'open', 'high', 'low', 'close', 'volume'
            **kwargs: Optionally accepts precomputed data:
                - trend_data: output from TrendIntelligenceEngine
                - strength_data: output from StrengthIntelligenceEngine
                - volatility_data: output from VolatilityIntelligenceEngine
                - structure_data: output from StructureIntelligenceEngine
                - mtf_data: output from MTFIntelligenceEngine
        
        Returns:
            Dictionary with keys: state, confidence, quality_score, tradeable,
            stability, description, and metrics (for debugging).
        """
        try:
            if candles_df is None or len(candles_df) < self.MIN_CANDLES:
                return self._get_neutral_state("Insufficient data")
            
            # Extract precomputed data if available (for better accuracy)
            trend_data = kwargs.get('trend_data', {})
            strength_data = kwargs.get('strength_data', {})
            volatility_data = kwargs.get('volatility_data', {})
            structure_data = kwargs.get('structure_data', {})
            mtf_data = kwargs.get('mtf_data', {})
            
            # Compute core metrics (prioritize engine data, fallback to raw calculations)
            metrics = self._compute_metrics(candles_df, trend_data, strength_data,
                                            volatility_data, structure_data, mtf_data)
            
            # Classify state
            state, confidence = self._classify_state(metrics)
            
            # Apply state transition smoothing
            state = self._smooth_state(state, confidence)
            
            quality_score = self._calculate_quality_score(state, metrics)
            tradeable = self._is_tradeable(state, quality_score, metrics)
            stability = self._compute_stability(metrics)
            description = self._describe_state(state, metrics)
            
            return {
                'state': state,
                'confidence': int(confidence),
                'quality_score': int(quality_score),
                'tradeable': tradeable,
                'stability': int(stability),
                'description': description,
                'metrics': metrics  # for debugging/explainability
            }
            
        except Exception as e:
            print(f"[ERR] MarketStateClassifier error: {e}")
            return self._get_neutral_state(f"Error: {str(e)}")
    
    def _compute_metrics(self, df: pd.DataFrame,
                        trend_data: Dict, strength_data: Dict,
                        volatility_data: Dict, structure_data: Dict,
                        mtf_data: Dict) -> Dict[str, Any]:
        """
        Compute or extract all necessary metrics for classification.
        Prioritizes precomputed engine outputs; falls back to raw calculations.
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values if 'volume' in df.columns else None
        
        # Trend metrics (optimized periods for 5-min)
        if trend_data:
            trend_direction = trend_data.get('direction', 'NONE')
            trend_strength = trend_data.get('strength', 0)
            trend_slope = trend_data.get('slope', 0)
            trend_type = trend_data.get('type', 'CHOPPY')
        else:
            trend_direction, trend_strength, trend_slope, trend_type = self._calc_trend_metrics_optimized(df)
        
        # Strength metrics with faster ADX (period 10) and RSI (period 7)
        if strength_data:
            adx = strength_data.get('adx', 20)
            rsi = strength_data.get('rsi', 50)
            momentum_level = strength_data.get('momentum_level', 'NORMAL')
            strength_score = strength_data.get('strength_score', 50)
        else:
            adx, rsi, momentum_level, strength_score = self._calc_strength_metrics_optimized(df)
        
        # Volatility metrics
        if volatility_data:
            atr_percentile = volatility_data.get('atr_percentile', 50)
            bbw = volatility_data.get('bbw', 0)
            volatility_regime = volatility_data.get('regime', 'NORMAL')
            volatility_score = volatility_data.get('volatility_score', 50)
        else:
            atr_percentile, bbw, volatility_regime, volatility_score = self._calc_volatility_metrics(df)
        
        # Structure metrics (including dynamic probabilities)
        if structure_data:
            structure_type = structure_data.get('structure_type', 'RANGING')
            bos_detected = structure_data.get('bos_detected', False)
            breakout_prob = structure_data.get('breakout_probability', 0)
            reversal_prob = structure_data.get('reversal_probability', 0)
        else:
            # Compute dynamic probabilities using volatility and price action
            structure_type, bos_detected, breakout_prob, reversal_prob = self._compute_dynamic_probabilities_optimized(
                df, adx, bbw, atr_percentile, volatility_regime
            )
        
        # MTF metrics (improved with 15/30/60 minute alignment for 5-min)
        if mtf_data:
            alignment_score = mtf_data.get('alignment_score', 0)
            htf_direction = mtf_data.get('htf_direction', 'NONE')
        else:
            alignment_score, htf_direction = self._calc_mtf_metrics_optimized(df)
        
        # Volume metrics
        volume_ratio = self._calc_volume_ratio(df)
        
        # Noise level (optimized with weighted efficiency)
        noise_level = self._calc_noise_level_optimized(df)
        
        # RSI extreme flags
        rsi_extreme_bull = rsi > 75
        rsi_extreme_bear = rsi < 25
        
        # Price vs moving averages (faster MAs)
        ma10 = pd.Series(close).rolling(10).mean().iloc[-1] if len(close) >= 10 else close[-1]
        ma20 = pd.Series(close).rolling(20).mean().iloc[-1] if len(close) >= 20 else close[-1]
        price_above_ma20 = close[-1] > ma20
        price_above_ma50 = close[-1] > pd.Series(close).rolling(50).mean().iloc[-1] if len(close) >= 50 else close[-1] > ma20
        
        # Wick patterns
        wick_lower_ratio, wick_upper_ratio = self._detect_wick_pattern_optimized(df)
        
        # Volatility compression detection
        compression_detected = self._detect_volatility_compression_optimized(df, bbw, atr_percentile)
        
        # NEW: Momentum divergence (for early reversal detection)
        divergence_detected = self._detect_momentum_divergence(df, rsi)
        
        # NEW: Volume surge confirmation for breakouts
        volume_surge = volume_ratio > 1.5
        
        # Adaptive thresholds based on recent volatility
        adaptive_adx_threshold = self._get_adaptive_adx_threshold(close, atr_percentile)
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'trend_slope': trend_slope,
            'trend_type': trend_type,
            'adx': adx,
            'rsi': rsi,
            'momentum_level': momentum_level,
            'strength_score': strength_score,
            'atr_percentile': atr_percentile,
            'bbw': bbw,
            'volatility_regime': volatility_regime,
            'volatility_score': volatility_score,
            'structure_type': structure_type,
            'bos_detected': bos_detected,
            'breakout_prob': breakout_prob,
            'reversal_prob': reversal_prob,
            'alignment_score': alignment_score,
            'htf_direction': htf_direction,
            'volume_ratio': volume_ratio,
            'noise_level': noise_level,
            'rsi_extreme_bull': rsi_extreme_bull,
            'rsi_extreme_bear': rsi_extreme_bear,
            'price_above_ma20': price_above_ma20,
            'price_above_ma50': price_above_ma50,
            'wick_lower_ratio': wick_lower_ratio,
            'wick_upper_ratio': wick_upper_ratio,
            'compression_detected': compression_detected,
            'divergence_detected': divergence_detected,
            'volume_surge': volume_surge,
            'adaptive_adx_threshold': adaptive_adx_threshold
        }
    
    def _classify_state(self, m: Dict[str, Any]) -> tuple:
        """
        Determine market state based on computed metrics.
        Returns (state, confidence) where confidence is 0-100 integer.
        """
        adx = m['adx']
        adaptive_threshold = m.get('adaptive_adx_threshold', 25)
        
        # 1. LIQUIDITY_VOID - extremely low volume, no movement
        if m['volume_ratio'] < 0.2 or (adx < 10 and m['volume_ratio'] < 0.5):
            return 'LIQUIDITY_VOID', 85
        
        # 2. CHOPPY_UNCERTAIN - high noise, low ADX, no clear direction
        # Use adaptive threshold for better noise detection
        if m['noise_level'] > 0.65 and adx < adaptive_threshold:
            return 'CHOPPY_UNCERTAIN', 80
        
        # 3. TRENDING_STRONG - high ADX, clear direction, strong momentum
        # Use adaptive threshold: require ADX > adaptive_threshold + 10
        if adx > adaptive_threshold + 10 and m['trend_strength'] > 55 and m['noise_level'] < 0.55:
            confidence = min(90, int(adx + m['trend_strength'] / 2))
            return 'TRENDING_STRONG', confidence
        
        # 4. TRENDING_WEAK - moderate ADX, direction exists but weak
        if adx > adaptive_threshold - 5 and m['trend_direction'] != 'NONE' and m['trend_strength'] < 55:
            return 'TRENDING_WEAK', 65
        
        # 5. BREAKOUT_EMERGING - compression detected, volatility expanding, volume confirmation
        breakout_conditions = m['compression_detected'] and m['breakout_prob'] > 45
        bbw_conditions = m['bbw'] < 0.06 and m['volatility_regime'] == 'LOW' and m['breakout_prob'] > 35
        volume_confirmed = m['volume_surge'] and m['breakout_prob'] > 40
        if breakout_conditions or bbw_conditions or volume_confirmed:
            conf_boost = 15 if m['volume_surge'] else 0
            return 'BREAKOUT_EMERGING', min(85, int(m['breakout_prob'] + 20 + conf_boost))
        
        # 6. REVERSAL_FORMING - potential trend change with divergence or oversold/overbought
        reversal_conditions = (m['reversal_prob'] > 50 and adx < 45) or \
                              ((m['rsi_extreme_bull'] or m['rsi_extreme_bear']) and m['trend_strength'] < 45) or \
                              (m['divergence_detected'] and adx < 40)
        if reversal_conditions:
            conf_boost = 15 if m['divergence_detected'] else 0
            return 'REVERSAL_FORMING', min(80, int(m['reversal_prob'] + conf_boost))
        
        # 7. ACCUMULATION - buying pressure, lower wicks, volume increase
        # Relaxed conditions for 5-min: allow lower RSI range
        if (m['volume_ratio'] > 1.1 and m['trend_direction'] == 'UP' and
            m['trend_strength'] < 55 and m['rsi'] < 65 and m['rsi'] > 35 and
            m['wick_lower_ratio'] > 0.45):  # lower wicks dominance
            volume_factor = min(30, (m['volume_ratio'] - 1.1) * 30)
            wick_factor = min(20, m['wick_lower_ratio'] * 25)
            confidence = int(50 + volume_factor + wick_factor)
            confidence = min(95, max(50, confidence))
            return 'ACCUMULATION', confidence
        
        # 8. DISTRIBUTION - selling pressure, upper wicks, volume increase
        if (m['volume_ratio'] > 1.1 and m['trend_direction'] == 'DOWN' and
            m['trend_strength'] < 55 and m['rsi'] > 35 and m['rsi'] < 65 and
            m['wick_upper_ratio'] > 0.45):  # upper wicks dominance
            volume_factor = min(30, (m['volume_ratio'] - 1.1) * 30)
            wick_factor = min(20, m['wick_upper_ratio'] * 25)
            confidence = int(50 + volume_factor + wick_factor)
            confidence = min(95, max(50, confidence))
            return 'DISTRIBUTION', confidence
        
        # 9. SIDEWAY_RANGE - low ADX, ranging structure, no breakout
        if (adx < adaptive_threshold + 5 and m['structure_type'] == 'RANGING' and
            m['volatility_regime'] in ['LOW', 'NORMAL'] and m['breakout_prob'] < 45):
            return 'SIDEWAY_RANGE', 70
        
        # 10. UNCLEAR - default when no clear classification
        return 'UNCLEAR', 50
    
    def _smooth_state(self, state: str, confidence: int) -> str:
        """
        Apply state transition smoothing to prevent rapid flipping.
        Requires at least N consecutive same-state classifications before changing.
        """
        self._state_history.append((state, confidence))
        if len(self._state_history) < self._max_history:
            return state
        
        # Count occurrences of each state in history
        from collections import Counter
        state_counts = Counter(s for s, _ in self._state_history)
        most_common_state, count = state_counts.most_common(1)[0]
        
        # If we have at least 3 out of 5 same state, use it
        if count >= 3:
            return most_common_state
        return state
    
    def _calculate_quality_score(self, state: str, m: Dict[str, Any]) -> int:
        """Calculate tradeability quality score 0-100."""
        base_scores = {
            'TRENDING_STRONG': 85,
            'TRENDING_WEAK': 65,
            'SIDEWAY_RANGE': 70,
            'BREAKOUT_EMERGING': 80,
            'REVERSAL_FORMING': 60,
            'ACCUMULATION': 75,
            'DISTRIBUTION': 75,
            'CHOPPY_UNCERTAIN': 25,
            'LIQUIDITY_VOID': 10,
            'UNCLEAR': 40
        }
        score = base_scores.get(state, 50)
        
        # Adjust based on real-time metrics
        if m['noise_level'] > 0.6:
            score -= 20
        if m['adx'] > 35:
            score += 8
        elif m['adx'] > 25:
            score += 3
        if m['volume_ratio'] > 1.4:
            score += 10
        if m['alignment_score'] > 65:
            score += 10
        if m['divergence_detected'] and state in ['TRENDING_STRONG', 'TRENDING_WEAK']:
            score -= 15  # divergence weakens trend quality
        
        return max(0, min(100, int(score)))
    
    def _is_tradeable(self, state: str, quality_score: int, m: Dict[str, Any]) -> bool:
        """Determine if current market state is suitable for trading."""
        # Always tradeable states
        tradeable_states = ['TRENDING_STRONG', 'BREAKOUT_EMERGING', 'ACCUMULATION', 'DISTRIBUTION']
        # Sometimes tradeable with high quality
        conditional_states = ['TRENDING_WEAK', 'SIDEWAY_RANGE', 'REVERSAL_FORMING']
        
        if state in tradeable_states:
            # Require minimum quality for borderline
            if state == 'TRENDING_STRONG':
                return quality_score >= 60
            return quality_score >= 55
        elif state in conditional_states:
            return quality_score >= 65
        else:
            return False
    
    def _compute_stability(self, m: Dict[str, Any]) -> int:
        """Compute market stability score (0-100). Higher = more stable."""
        stability = 50
        
        # Low noise is stable
        if m['noise_level'] < 0.3:
            stability += 25
        elif m['noise_level'] < 0.5:
            stability += 10
        elif m['noise_level'] > 0.7:
            stability -= 25
        
        # Consistent trend direction
        if m['trend_direction'] != 'NONE' and m['trend_strength'] > 50:
            stability += 15
        
        # Moderate volatility (neither too high nor too low)
        if 70 <= m['atr_percentile'] <= 130:
            stability += 10
        elif m['atr_percentile'] > 150:
            stability -= 20
        elif m['atr_percentile'] < 40:
            stability -= 15
        
        # Volume consistency
        if 0.7 < m['volume_ratio'] < 1.5:
            stability += 10
        elif m['volume_ratio'] > 2.0 or m['volume_ratio'] < 0.3:
            stability -= 15
        
        # MTF alignment adds stability
        if m['alignment_score'] > 65:
            stability += 15
        elif m['alignment_score'] < 35:
            stability -= 10
        
        return max(0, min(100, int(stability)))
    
    def _describe_state(self, state: str, m: Dict[str, Any]) -> str:
        """Generate human-readable description of the state."""
        descriptions = {
            'TRENDING_STRONG': 'Strong directional movement with high momentum. Ideal for trend-following strategies.',
            'TRENDING_WEAK': 'Directional bias but with reduced conviction. Use with confirmation filters.',
            'SIDEWAY_RANGE': 'Price oscillating between established levels. Mean reversion setups favored.',
            'BREAKOUT_EMERGING': 'Volatility expanding after compression. Potential explosive move.',
            'REVERSAL_FORMING': 'Early signs of trend change. Wait for confirmation before entry.',
            'ACCUMULATION': 'Smart money accumulating. Bullish bias with potential upward move.',
            'DISTRIBUTION': 'Smart money distributing. Bearish bias with potential downward move.',
            'CHOPPY_UNCERTAIN': 'Chaotic price action, high noise. Avoid trading until clarity returns.',
            'LIQUIDITY_VOID': 'Extremely low volume / dead market. No trading opportunity.',
            'UNCLEAR': 'Mixed signals or insufficient data. Exercise caution.'
        }
        base = descriptions.get(state, 'Market state could not be clearly determined.')
        # Add extra details if helpful
        if state in ['BREAKOUT_EMERGING', 'REVERSAL_FORMING']:
            extra = []
            if m.get('breakout_prob', 0) > 0:
                extra.append(f"breakout prob: {m.get('breakout_prob', 0):.0f}%")
            if m.get('reversal_prob', 0) > 0:
                extra.append(f"reversal prob: {m.get('reversal_prob', 0):.0f}%")
            if m.get('divergence_detected', False):
                extra.append("divergence detected")
            if extra:
                return f"{base} ({', '.join(extra)})"
        return base
    
    def _get_neutral_state(self, reason: str) -> Dict[str, Any]:
        """Return neutral/fallback state when analysis cannot be performed."""
        return {
            'state': 'UNCLEAR',
            'confidence': 0,
            'quality_score': 30,
            'tradeable': False,
            'stability': 30,
            'description': f'Unable to classify: {reason}',
            'metrics': {'error': reason}
        }
    
    # ==================== Optimized Helper Calculation Methods ====================
    
    def _calc_trend_metrics_optimized(self, df: pd.DataFrame) -> tuple:
        """Faster trend detection for 5-min using EMA5 and EMA10."""
        close = df['close'].values
        n = len(close)
        if n < 15:
            return 'NONE', 0, 0, 'CHOPPY'
        
        # Use faster EMAs: EMA5 (25 min) and EMA10 (50 min)
        ema5 = pd.Series(close).ewm(span=5, adjust=False).mean().iloc[-1]
        ema10 = pd.Series(close).ewm(span=10, adjust=False).mean().iloc[-1]
        slope = (ema5 - ema10) / (ema10 + 1e-9)
        
        # Higher highs / higher lows detection
        recent_highs = max(close[-8:])
        recent_lows = min(close[-8:])
        prior_highs = max(close[-16:-8]) if n >= 16 else recent_highs
        prior_lows = min(close[-16:-8]) if n >= 16 else recent_lows
        
        if recent_highs > prior_highs and recent_lows > prior_lows:
            direction = 'UP'
            strength = min(100, 50 + abs(slope) * 800)
        elif recent_highs < prior_highs and recent_lows < prior_lows:
            direction = 'DOWN'
            strength = min(100, 50 + abs(slope) * 800)
        else:
            direction = 'NONE'
            strength = 30
        
        trend_type = 'IMPULSIVE' if abs(slope) > 0.008 else 'CORRECTIVE' if abs(slope) > 0.002 else 'CHOPPY'
        return direction, int(strength), float(slope), trend_type
    
    def _calc_strength_metrics_optimized(self, df: pd.DataFrame) -> tuple:
        """Faster ADX (period 10) and RSI (period 7) for 5-min responsiveness."""
        close = df['close']
        # ADX with period 10 (50 minutes) instead of 14 (70 minutes)
        adx = self._calculate_adx(df, period=10)
        # RSI with period 7 (35 minutes) for faster reversal detection
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=7, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=7, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # Adjusted thresholds for 5-min
        if adx > 32:
            momentum_level = 'STRONG'
        elif adx > 20:
            momentum_level = 'NORMAL'
        else:
            momentum_level = 'WEAK'
        
        strength_score = adx * 0.6 + (current_rsi if current_rsi > 50 else 100 - current_rsi) * 0.4
        strength_score = min(100, max(0, strength_score))
        
        return adx, current_rsi, momentum_level, int(strength_score)
    
    def _calc_volatility_metrics(self, df: pd.DataFrame) -> tuple:
        """Volatility metrics (unchanged but used with adaptive thresholds)."""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # ATR
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(10).mean()  # shorter period for 5-min
        current_atr = atr.iloc[-1] if len(atr) > 0 else 0
        avg_atr = atr.iloc[-40:].mean() if len(atr) >= 40 else current_atr
        atr_percentile = (current_atr / (avg_atr + 1e-9)) * 100
        
        # Bollinger Band Width (period 14 for faster response)
        window = 14
        rolling_mean = close.rolling(window).mean()
        rolling_std = close.rolling(window).std(ddof=0)
        upper = rolling_mean + 2 * rolling_std
        lower = rolling_mean - 2 * rolling_std
        bbw = (upper - lower) / rolling_mean
        current_bbw = bbw.iloc[-1] if len(bbw) > 0 else 0
        
        if atr_percentile > 150:
            regime = 'EXTREME'
            score = 80
        elif atr_percentile > 110:
            regime = 'HIGH'
            score = 65
        elif atr_percentile > 80:
            regime = 'NORMAL'
            score = 50
        else:
            regime = 'LOW'
            score = 30
        
        return int(atr_percentile), float(current_bbw), regime, score
    
    def _detect_wick_pattern_optimized(self, df: pd.DataFrame) -> tuple:
        """Improved wick detection with better sensitivity for 5-min."""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_prices = df['open'].values
        
        n = min(15, len(close))  # 75 minutes - enough for accumulation detection
        if n < 5:
            return 0.5, 0.5
        
        lower_wick_count = 0
        upper_wick_count = 0
        
        for i in range(-n, 0):
            candle_high = high[i]
            candle_low = low[i]
            candle_close = close[i]
            candle_open = open_prices[i]
            total_range = candle_high - candle_low
            if total_range < 1e-9:
                continue
            
            if candle_close >= candle_open:
                # Bullish candle: lower wick = open - low, upper wick = high - close
                lower_wick = candle_open - candle_low
                upper_wick = candle_high - candle_close
            else:
                # Bearish candle: lower wick = close - low, upper wick = high - open
                lower_wick = candle_close - candle_low
                upper_wick = candle_high - candle_open
            
            lower_wick_ratio = lower_wick / total_range
            upper_wick_ratio = upper_wick / total_range
            
            # Slightly lower thresholds for 5-min (more sensitive)
            if lower_wick_ratio > 0.4:
                lower_wick_count += 1
            if upper_wick_ratio > 0.5:
                upper_wick_count += 1
        
        lower_ratio = lower_wick_count / n
        upper_ratio = upper_wick_count / n
        return lower_ratio, upper_ratio
    
    def _detect_volatility_compression_optimized(self, df: pd.DataFrame, bbw: float, atr_percentile: float) -> bool:
        """Faster compression detection for 5-min."""
        close = df['close']
        window = 14
        rolling_mean = close.rolling(window).mean()
        rolling_std = close.rolling(window).std(ddof=0)
        upper = rolling_mean + 2 * rolling_std
        lower = rolling_mean - 2 * rolling_std
        bbw_series = (upper - lower) / rolling_mean
        
        if len(bbw_series) < 14:
            return False
        
        recent_bbw = bbw_series.iloc[-7:].values  # last 7 candles (35 min)
        if len(recent_bbw) < 4:
            return False
        
        bbw_trend = recent_bbw[-1] < recent_bbw[0] * 0.85  # 15% decrease
        is_low_bbw = bbw < 0.06
        is_low_atr = atr_percentile < 75
        
        # Also detect sideways compression (range narrowing)
        high_low_ratio = (df['high'].iloc[-5:].max() - df['low'].iloc[-5:].min()) / df['close'].iloc[-1]
        range_narrowing = high_low_ratio < 0.005  # less than 0.5% range
        
        return (bbw_trend and is_low_bbw) or (is_low_bbw and is_low_atr) or range_narrowing
    
    def _compute_dynamic_probabilities_optimized(self, df: pd.DataFrame, adx: float, bbw: float,
                                                atr_percentile: float, volatility_regime: str) -> tuple:
        """Enhanced breakout/reversal probabilities for 5-min binary options."""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        n = len(close)
        
        if n < 30:
            return 'RANGING', False, 30, 30
        
        # Identify swing highs and lows (lookback 10 candles = 50 min)
        lookback = 10
        recent_highs = max(high[-lookback:])
        recent_lows = min(low[-lookback:])
        range_width = (recent_highs - recent_lows) / (recent_lows + 1e-9)
        
        # Structure type with proximity to range extremes
        upper_proximity = (recent_highs - close[-1]) / (recent_highs - recent_lows + 1e-9)
        lower_proximity = (close[-1] - recent_lows) / (recent_highs - recent_lows + 1e-9)
        
        if upper_proximity < 0.1 or lower_proximity < 0.1:
            structure_type = 'BREAKOUT'
        elif range_width < 0.012:
            structure_type = 'RANGING'
        else:
            structure_type = 'TRENDING'
        
        # BOS detection (Break of Structure) with confirmation
        bos_detected = False
        if close[-1] > max(high[-6:-1]) + (max(high[-6:-1]) - min(low[-6:-1])) * 0.2:
            bos_detected = True
        elif close[-1] < min(low[-6:-1]) - (max(high[-6:-1]) - min(low[-6:-1])) * 0.2:
            bos_detected = True
        
        # Breakout probability (optimized for 5-min)
        breakout_prob = 30
        if bbw < 0.05:
            breakout_prob += 30
        elif bbw < 0.08:
            breakout_prob += 15
        if atr_percentile < 70:
            breakout_prob += 15
        if adx > 22:
            breakout_prob += 10
        # Add volume surge detection (from metric, but we approximate using price range)
        price_range_5 = (high[-5:].max() - low[-5:].min()) / close[-1]
        if price_range_5 < 0.003:  # very tight range
            breakout_prob += 15
        
        # Reversal probability (enhanced with divergence-like detection)
        reversal_prob = 30
        # Check for trend exhaustion: recent candles showing loss of momentum
        if len(close) >= 10:
            momentum1 = abs(close[-3] - close[-6])
            momentum2 = abs(close[-1] - close[-4])
            if momentum2 < momentum1 * 0.5:
                reversal_prob += 20
        # RSI extreme (from metrics, but we approximate)
        rsi_approx = self._calc_strength_metrics_optimized(df)[1]
        if rsi_approx > 75 or rsi_approx < 25:
            reversal_prob += 15
        # Candlestick reversal patterns (engulfing, doji)
        body_last = abs(close[-1] - df['open'].iloc[-1])
        body_prev = abs(close[-2] - df['open'].iloc[-2])
        if body_last < body_prev * 0.3:  # small body (doji-like)
            reversal_prob += 10
        
        # Clamp probabilities
        breakout_prob = min(95, max(5, breakout_prob))
        reversal_prob = min(90, max(5, reversal_prob))
        
        return structure_type, bos_detected, int(breakout_prob), int(reversal_prob)
    
    def _calc_mtf_metrics_optimized(self, df: pd.DataFrame) -> tuple:
        """Improved MTF using 5-min, 15-min, 30-min representation via multiple MAs."""
        close = df['close'].values
        if len(close) < 30:
            return 50, 'NONE'
        
        # Represent higher timeframes with different MA periods:
        # 5-min = 1x, 15-min = 3x, 30-min = 6x, 60-min = 12x
        ma5 = pd.Series(close).rolling(5).mean().iloc[-1]   # 25 min
        ma15 = pd.Series(close).rolling(15).mean().iloc[-1]  # 75 min
        ma30 = pd.Series(close).rolling(30).mean().iloc[-1]  # 150 min
        
        # Determine alignment: if MAs are stacked in same direction
        if ma5 > ma15 > ma30:
            direction = 'UP'
            alignment = min(100, 60 + (ma5 - ma30) / ma30 * 500)
        elif ma5 < ma15 < ma30:
            direction = 'DOWN'
            alignment = min(100, 60 + (ma30 - ma5) / ma30 * 500)
        else:
            # Check partial alignment
            if (ma5 > ma15 and ma15 > close[-1]) or (ma5 < ma15 and ma15 < close[-1]):
                direction = 'MIXED_UP' if ma5 > ma15 else 'MIXED_DOWN'
                alignment = 45
            else:
                direction = 'NONE'
                alignment = 35
        
        return int(alignment), direction
    
    def _calc_volume_ratio(self, df: pd.DataFrame) -> float:
        if 'volume' not in df.columns:
            return 1.0
        volume = df['volume'].values
        if len(volume) < 15:
            return 1.0
        avg_vol = np.mean(volume[-15:])
        current_vol = volume[-1]
        return current_vol / (avg_vol + 1e-9)
    
    def _calc_noise_level_optimized(self, df: pd.DataFrame) -> float:
        """Enhanced noise estimation with weighted efficiency for 5-min."""
        close = df['close'].values
        n = min(30, len(close))  # 150 minutes - enough for short-term noise
        if n < 8:
            return 0.5
        
        # Weighted efficiency: more weight on recent candles
        weights = np.exp(np.linspace(-1, 0, n))  # exponential weighting
        weights = weights / weights.sum()
        
        total_move_weighted = 0
        for i in range(-n+1, 0):
            move = abs(close[i] - close[i-1])
            weight = weights[i + n - 1]  # map index to weight
            total_move_weighted += move * weight
        
        net_move = abs(close[-1] - close[-n])
        efficiency = net_move / (total_move_weighted + 1e-9)
        
        # Adjust for trending markets (efficiency can be high even with noise)
        # Use price range ratio to detect false moves
        price_range = max(close[-n:]) - min(close[-n:])
        candle_body_ratio = abs(close[-1] - close[-2]) / (price_range + 1e-9)
        
        noise = max(0, min(1, 1 - efficiency))
        # If last candle body is large relative to range, reduce noise estimate
        if candle_body_ratio > 0.3:
            noise = max(0, noise - 0.15)
        
        return noise
    
    def _detect_momentum_divergence(self, df: pd.DataFrame, rsi: float) -> bool:
        """
        Detect bullish/bearish divergence between price and RSI momentum.
        Returns True if divergence detected.
        """
        close = df['close'].values
        if len(close) < 20:
            return False
        
        # Look for lower lows in price but higher lows in RSI (bullish divergence)
        recent_prices_lows = [min(close[-5:]), min(close[-10:-5])]
        recent_rsi = [rsi]  # we need RSI history; approximate using last few RSI values
        # Simplified: if price made lower low but RSI is rising
        price_lower_low = close[-1] < min(close[-6:-1])
        rsi_rising = rsi > 35  # placeholder - would need RSI series
        
        # For now, use a simplified check based on price action and RSI level
        # Bullish divergence: price at support, RSI oversold but rising
        if rsi < 35 and close[-1] > min(close[-5:]):
            return True
        # Bearish divergence: price at resistance, RSI overbought but falling
        if rsi > 65 and close[-1] < max(close[-5:]):
            return True
        
        return False
    
    def _get_adaptive_adx_threshold(self, close: np.ndarray, atr_percentile: float) -> int:
        """
        Return ADX threshold adjusted for current volatility regime.
        In low volatility, ADX tends to be lower; adjust thresholds downward.
        """
        if atr_percentile < 60:
            return 18  # lower threshold in low volatility
        elif atr_percentile > 140:
            return 28  # higher threshold in high volatility
        else:
            return 22  # normal threshold
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Standard ADX calculation with Wilder smoothing."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            up_move = high.diff()
            down_move = -low.diff()
            pos_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0))
            neg_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0))
            
            def wilder_smooth(series, per):
                smoothed = series.rolling(per, min_periods=per).mean()
                for i in range(per, len(series)):
                    smoothed.iloc[i] = (smoothed.iloc[i-1] * (per - 1) + series.iloc[i]) / per
                return smoothed
            
            smoothed_tr = wilder_smooth(tr, period)
            smoothed_pos_dm = wilder_smooth(pos_dm, period)
            smoothed_neg_dm = wilder_smooth(neg_dm, period)
            
            pos_di = 100 * (smoothed_pos_dm / (smoothed_tr + 1e-9))
            neg_di = 100 * (smoothed_neg_dm / (smoothed_tr + 1e-9))
            
            dx = 100 * (abs(pos_di - neg_di) / (pos_di + neg_di + 1e-9))
            adx = wilder_smooth(dx, period)
            
            return float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 20.0
        except Exception as e:
            print(f"[WARN] ADX calculation failed: {e}")
            return 20.0

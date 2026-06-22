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
                - symbol: trading pair symbol (e.g., 'EURUSD-OTC')
        
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
            symbol = kwargs.get('symbol', '')
            is_otc = (symbol.upper().endswith('_OTC') or symbol.upper().endswith('-OTC')) if isinstance(symbol, str) else False
            
            # Compute core metrics (prioritize engine data, fallback to raw calculations)
            metrics = self._compute_metrics(candles_df, trend_data, strength_data,
                                            volatility_data, structure_data, mtf_data,
                                            is_otc=is_otc)
            
            # Classify state
            state, confidence = self._classify_state(metrics, is_otc=is_otc)
            
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
                        mtf_data: Dict, is_otc: bool = False) -> Dict[str, Any]:
        """
        Compute or extract all necessary metrics for classification.
        Prioritizes precomputed engine outputs; falls back to raw calculations.
        
        For OTC pairs (is_otc=True), volume_ratio is forced to 1.0 to avoid
        LIQUIDITY_VOID misclassification since volume data is not reliable in OTC markets.
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
        # For OTC: force volume_ratio to 1.0 to avoid LIQUIDITY_VOID misclassification
        if is_otc:
            volume_ratio = 1.0
        else:
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
            'adaptive_adx_threshold': adaptive_adx_threshold,
            'is_otc': is_otc
        }
    
    def _classify_state(self, m: Dict[str, Any], is_otc: bool = False) -> tuple:
        """
        Determine market state using a weighted scoring system.
        Returns (state, confidence) where confidence is 0-100 integer.
        
        For OTC pairs (is_otc=True), LIQUIDITY_VOID score is forced to 0
        because volume data is not reliable in OTC markets.
        """
        # Compute raw scores for all states
        raw_scores = self._compute_raw_scores(m)
        
        # Apply global modifiers (boosts/penalties)
        adjusted_scores = self._apply_global_modifiers(raw_scores, m, is_otc)
        
        # For OTC, explicitly zero out LIQUIDITY_VOID
        if is_otc:
            adjusted_scores['LIQUIDITY_VOID'] = 0
        
        # Select best state
        best_state = max(adjusted_scores, key=adjusted_scores.get)
        best_score = adjusted_scores[best_state]
        
        # Calculate confidence based on score margin over second best
        sorted_scores = sorted(adjusted_scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            margin = sorted_scores[0] - sorted_scores[1]
            # Confidence: base 50% + margin contribution, capped at 100
            confidence = min(100, int(50 + (margin / 100) * 50))
        else:
            confidence = 50
        
        # Prevent rapid switching: if best_state is LIQUIDITY_VOID but previous wasn't,
        # require a significant margin (>=15 points) to switch
        if best_state == 'LIQUIDITY_VOID' and self._state_history:
            prev_state, _ = self._state_history[-1]
            if prev_state != 'LIQUIDITY_VOID' and len(sorted_scores) >= 2:
                if margin < 15:
                    # Fall back to second best (unless it's also LIQUIDITY_VOID)
                    second_best = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)[1][0]
                    if second_best != 'LIQUIDITY_VOID':
                        best_state = second_best
                        best_score = adjusted_scores[best_state]
                        confidence = min(100, int(50 + ((best_score - sorted_scores[1]) / 100) * 50))
        
        return best_state, max(0, min(100, confidence))
    
    def _compute_raw_scores(self, m: Dict[str, Any]) -> Dict[str, float]:
        """Compute raw score for each state based on the weighted scoring system."""
        scores = {}
        
        # Extract metrics
        adx = m.get('adx', 0)
        trend_strength = m.get('trend_strength', 0)
        direction = m.get('trend_direction', 'NONE')
        atr_percentile = m.get('atr_percentile', 50)
        bbw = m.get('bbw', 0.08)
        volatility_regime = m.get('volatility_regime', 'NORMAL')
        structure_type = m.get('structure_type', 'RANGING')
        bos_detected = m.get('bos_detected', False)
        breakout_prob = m.get('breakout_prob', 30)
        reversal_prob = m.get('reversal_prob', 30)
        volume_ratio = m.get('volume_ratio', 1.0)
        is_otc = m.get('is_otc', False)
        noise_level = m.get('noise_level', 0.5)
        alignment_score = m.get('alignment_score', 50)
        htf_ltf_conflict = m.get('htf_ltf_conflict', False)
        exhaustion_risk = m.get('exhaustion_risk', 30)
        divergence_detected = m.get('divergence_detected', False)
        rsi = m.get('rsi', 50)
        wick_lower_ratio = m.get('wick_lower_ratio', 0.3)
        wick_upper_ratio = m.get('wick_upper_ratio', 0.3)
        
        # ----- TRENDING_STRONG -----
        score = (adx / 100) * 35
        score += (trend_strength / 100) * 30
        score += (alignment_score / 100) * 20
        score += (1 - noise_level) * 15
        # Boosts
        if direction != 'NONE':
            score += 10
        if structure_type in ['TRENDING', 'BREAKOUT']:
            score += 10
        if bos_detected:
            score += 5
        if alignment_score >= 70:
            score += 10
        # Penalties
        if noise_level > 0.6:
            score -= 20
        if exhaustion_risk > 70:
            score -= 20
        if htf_ltf_conflict:
            score -= 15
        scores['TRENDING_STRONG'] = max(0, score)
        
        # ----- BREAKOUT_EMERGING -----
        score = max(0, (0.06 - bbw) / 0.06) * 30
        score += (100 - atr_percentile) / 100 * 20
        score += (breakout_prob / 100) * 25
        score += (1 if bos_detected else 0) * 15
        # Volume factor
        if not is_otc:
            score += min(1.0, volume_ratio / 1.5) * 10
        else:
            score += 10  # full volume credit for OTC
        # Boosts
        if bbw < 0.04:
            score += 15
        if atr_percentile < 30:
            score += 10
        if not is_otc and volume_ratio > 1.5:
            score += 10
        # Penalties
        if noise_level > 0.5:
            score -= 15
        if htf_ltf_conflict:
            score -= 20
        scores['BREAKOUT_EMERGING'] = max(0, score)
        
        # ----- SIDEWAY_RANGE -----
        score = (100 - adx) / 100 * 35
        score += (1 if structure_type == 'RANGING' else 0) * 25
        score += (1 - noise_level) * 20
        score += (1 if volatility_regime in ['LOW', 'NORMAL'] else 0) * 20
        # Boosts
        if adx < 18:
            score += 15
        if noise_level < 0.3:
            score += 10
        # Penalties
        if bos_detected:
            score -= 20
        if breakout_prob > 50:
            score -= 15
        scores['SIDEWAY_RANGE'] = max(0, score)
        
        # ----- ACCUMULATION -----
        score = min(1.0, wick_lower_ratio * 2) * 35
        # Volume factor
        if not is_otc:
            score += min(1.0, volume_ratio / 1.2) * 25
        else:
            score += 25
        score += ((100 - trend_strength) / 100) * 20
        score += (1 if structure_type in ['RANGING', 'CORRECTIVE'] else 0) * 20
        # Boosts
        if not is_otc and volume_ratio > 1.2:
            score += 15
        if wick_lower_ratio > 0.5:
            score += 10
        # Penalties
        if bos_detected:
            score -= 15
        if divergence_detected:
            score -= 10
        scores['ACCUMULATION'] = max(0, score)
        
        # ----- DISTRIBUTION -----
        score = min(1.0, wick_upper_ratio * 2) * 35
        if not is_otc:
            score += min(1.0, volume_ratio / 1.2) * 25
        else:
            score += 25
        score += ((100 - trend_strength) / 100) * 20
        score += (1 if structure_type in ['RANGING', 'CORRECTIVE'] else 0) * 20
        # Boosts
        if not is_otc and volume_ratio > 1.2:
            score += 15
        if wick_upper_ratio > 0.5:
            score += 10
        # Penalties
        if bos_detected:
            score -= 15
        if divergence_detected:
            score -= 10
        scores['DISTRIBUTION'] = max(0, score)
        
        # ----- TRENDING_WEAK -----
        score = (adx / 100) * 30
        score += (trend_strength / 100) * 25
        score += (1 - noise_level) * 25
        score += (alignment_score / 100) * 20
        # Boosts
        if direction != 'NONE':
            score += 10
        if structure_type in ['TRENDING', 'CORRECTIVE']:
            score += 5
        # Penalties
        if exhaustion_risk > 70:
            score -= 25
        if htf_ltf_conflict:
            score -= 10
        if noise_level > 0.5:
            score -= 15
        scores['TRENDING_WEAK'] = max(0, score)
        
        # ----- REVERSAL_FORMING -----
        score = (reversal_prob / 100) * 35
        score += (100 - adx) / 100 * 25
        score += (1 if divergence_detected else 0) * 20
        score += (1 - noise_level) * 20
        # Boosts
        if rsi < 30 or rsi > 70:
            score += 15
        if structure_type == 'CORRECTIVE':
            score += 10
        # Penalties
        if noise_level > 0.5:
            score -= 15
        if htf_ltf_conflict:
            score -= 10
        scores['REVERSAL_FORMING'] = max(0, score)
        
        # ----- CHOPPY_UNCERTAIN -----
        score = noise_level * 100 * 0.6
        score += (100 - adx) / 100 * 20
        score += (1 if structure_type == 'CHOPPY' else 0) * 20
        # Penalties (lower score for choppy)
        if trend_strength > 40:
            score -= 20
        if alignment_score > 50:
            score -= 15
        scores['CHOPPY_UNCERTAIN'] = max(0, score)
        
        # ----- LIQUIDITY_VOID -----
        # Use inverse of volume and ADX as indicators of void
        if not is_otc:
            score = (1 - min(1.0, volume_ratio / 0.5)) * 50
            score += (1 - min(1.0, adx / 20)) * 50
        else:
            score = 0  # will be zeroed in _classify_state
        scores['LIQUIDITY_VOID'] = max(0, score)
        
        # ----- UNCLEAR -----
        # Default moderate score when nothing else fits
        score = 25
        # Increase if most scores are low
        other_scores = [scores[k] for k in scores if k != 'UNCLEAR']
        if all(s < 30 for s in other_scores):
            score = 50
        if htf_ltf_conflict or noise_level > 0.6:
            score += 20
        scores['UNCLEAR'] = max(0, min(100, score))
        
        return scores
    
    def _apply_global_modifiers(self, scores: Dict[str, float], m: Dict[str, Any], is_otc: bool) -> Dict[str, float]:
        """Apply global boosts and penalties to all state scores."""
        adjusted = dict(scores)
        
        noise_level = m.get('noise_level', 0.5)
        htf_ltf_conflict = m.get('htf_ltf_conflict', False)
        exhaustion_risk = m.get('exhaustion_risk', 30)
        anomaly_detected = m.get('anomaly_detected', False)
        volatility_regime = m.get('volatility_regime', 'NORMAL')
        volume_ratio = m.get('volume_ratio', 1.0)
        is_otc = m.get('is_otc', False)
        
        # Global modifiers
        modifiers = []
        
        # Low noise boost
        if noise_level < 0.25:
            modifiers.append(('TRENDING_STRONG', 10))
            modifiers.append(('SIDEWAY_RANGE', 10))
        
        # Volume surge boost
        if not is_otc and volume_ratio > 1.5:
            modifiers.append(('BREAKOUT_EMERGING', 15))
            modifiers.append(('ACCUMULATION', 15))
            modifiers.append(('DISTRIBUTION', 15))
        
        # HTF-LTF conflict penalty
        if htf_ltf_conflict:
            for state in adjusted:
                if state != 'UNCLEAR':
                    adjusted[state] -= 15
        
        # High noise penalty
        if noise_level > 0.6:
            adjusted['TRENDING_STRONG'] -= 20
            adjusted['BREAKOUT_EMERGING'] -= 20
        
        # Exhaustion penalty
        if exhaustion_risk > 70:
            adjusted['TRENDING_STRONG'] -= 25
            adjusted['TRENDING_WEAK'] -= 25
        
        # Anomaly penalty
        if anomaly_detected:
            for state in adjusted:
                adjusted[state] -= 30
        
        # Extreme volatility penalty
        if volatility_regime == 'EXTREME':
            for state in adjusted:
                if state != 'UNCLEAR':
                    adjusted[state] -= 20
        
        # Apply modifiers
        for state, boost in modifiers:
            if state in adjusted:
                adjusted[state] += boost
        
        # Clamp to 0-100
        for state in adjusted:
            adjusted[state] = max(0, min(100, adjusted[state]))
        
        return adjusted
    
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
        counter = Counter(s for s, _ in self._state_history)
        most_common_state, count = counter.most_common(1)[0]
        
        # If the most common state appears at least 3 times, use it
        if count >= 3:
            return most_common_state
        return state
    
    def _calculate_quality_score(self, state: str, m: Dict[str, Any]) -> float:
        """Calculate quality score (0-100) based on state and metrics."""
        # Base quality by state
        state_quality = {
            'TRENDING_STRONG': 90,
            'BREAKOUT_EMERGING': 85,
            'ACCUMULATION': 80,
            'SIDEWAY_RANGE': 75,
            'TRENDING_WEAK': 65,
            'REVERSAL_FORMING': 60,
            'DISTRIBUTION': 45,
            'CHOPPY_UNCERTAIN': 20,
            'LIQUIDITY_VOID': 10,
            'UNCLEAR': 15
        }
        quality = state_quality.get(state, 50)
        
        # Adjust based on noise level
        noise_penalty = int(m.get('noise_level', 0) * 30)
        quality = max(0, quality - noise_penalty)
        
        # Adjust based on volume
        volume_ratio = m.get('volume_ratio', 1.0)
        if volume_ratio < 0.5:
            quality = max(0, quality - 20)
        
        return min(100, quality)
    
    def _is_tradeable(self, state: str, quality: float, m: Dict[str, Any]) -> bool:
        """Determine if market is tradeable based on state and quality."""
        tradeable_states = [
            'TRENDING_STRONG', 'BREAKOUT_EMERGING', 'ACCUMULATION',
            'SIDEWAY_RANGE', 'TRENDING_WEAK', 'REVERSAL_FORMING', 'DISTRIBUTION'
        ]
        if state not in tradeable_states:
            return False
        # อ่านจาก config ที่ส่งเข้ามา หรือใช้ค่า default
        cfg = self.config or {}
        min_quality = cfg.get("min_quality_score", 40)
        max_noise  = cfg.get("max_noise_level", 0.6)
        if quality < min_quality:
            return False
        if m.get('noise_level', 0) > max_noise:
            return False
        return True
    
    def _compute_stability(self, m: Dict[str, Any]) -> float:
        """Compute market stability score (0-100)."""
        noise = m.get('noise_level', 0)
        volatility = m.get('volatility_score', 50) / 100
        adx = m.get('adx', 0) / 50
        
        stability = 100 * (1 - noise) * (1 - volatility * 0.3) * (0.5 + 0.5 * min(1, adx))
        return min(100, max(0, stability))
    
    def _describe_state(self, state: str, m: Dict[str, Any]) -> str:
        """Generate human-readable description of the market state."""
        descriptions = {
            'TRENDING_STRONG': 'Strong directional trend with high momentum. Favorable for trend-following strategies.',
            'TRENDING_WEAK': 'Weak directional bias. Caution advised, consider range-bound strategies.',
            'SIDEWAY_RANGE': 'Price ranging between clear levels. Suitable for mean-reversion strategies.',
            'BREAKOUT_EMERGING': 'Volatility expansion after compression. Potential breakout opportunity.',
            'REVERSAL_FORMING': 'Early signals of potential trend change. Watch for confirmation.',
            'ACCUMULATION': 'Smart money accumulation. Bullish bias, look for breakout.',
            'DISTRIBUTION': 'Smart money distribution. Bearish bias, look for breakdown.',
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
        
        # Momentum level
        if current_rsi > 65:
            momentum = 'STRONG'
            strength_score = 70 + (current_rsi - 65) / 35 * 30
        elif current_rsi < 35:
            momentum = 'WEAK'
            strength_score = 70 - (35 - current_rsi) / 35 * 30
        else:
            momentum = 'NORMAL'
            strength_score = 50 + (current_rsi - 50) / 15 * 20
        
        return int(adx), int(current_rsi), momentum, int(strength_score)
    
    def _calc_volatility_metrics(self, df: pd.DataFrame) -> tuple:
        """Calculate volatility metrics: ATR percentile, BBW, regime, score."""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        n = len(close)
        
        if n < 20:
            return 50, 0.05, 'NORMAL', 50
        
        # ATR (period 10 for 5-min responsiveness)
        tr = np.zeros(n)
        for i in range(1, n):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        atr = pd.Series(tr).rolling(10).mean().iloc[-1]
        
        # ATR percentile based on recent 50 periods
        atr_history = pd.Series(tr).rolling(10).mean().iloc[-50:] if n >= 50 else pd.Series(tr).rolling(10).mean()
        atr_percentile = 50
        if len(atr_history) > 0:
            current_atr = atr_history.iloc[-1] if len(atr_history) > 0 else atr
            atr_percentile = min(100, max(0, (current_atr / (atr_history.mean() + 1e-9)) * 50))
        
        # Bollinger Band Width (BBW)
        ma20 = pd.Series(close).rolling(20).mean()
        std20 = pd.Series(close).rolling(20).std()
        bbw = (2 * std20.iloc[-1]) / (ma20.iloc[-1] + 1e-9) if len(ma20) > 0 else 0.05
        
        # Volatility regime
        if atr_percentile < 30:
            regime = 'LOW'
            score = 30
        elif atr_percentile < 60:
            regime = 'NORMAL'
            score = 50
        elif atr_percentile < 85:
            regime = 'HIGH'
            score = 70
        else:
            regime = 'EXTREME'
            score = 85
        
        return int(atr_percentile), float(bbw), regime, score
    
    def _calc_mtf_metrics_optimized(self, df: pd.DataFrame) -> tuple:
        """
        Simplified MTF alignment using M5 vs M15/M30/H1 approximation.
        Since we only have M5 data, we use a heuristic based on rolling windows.
        """
        close = df['close'].values
        n = len(close)
        if n < 30:
            return 50, 'NONE'
        
        # Approximate higher timeframe directions using different window sizes
        # M15 = 3 candles, M30 = 6 candles, H1 = 12 candles
        m15_slope = (close[-1] - close[-3]) / (close[-3] + 1e-9) if n >= 3 else 0
        m30_slope = (close[-1] - close[-6]) / (close[-6] + 1e-9) if n >= 6 else 0
        h1_slope = (close[-1] - close[-12]) / (close[-12] + 1e-9) if n >= 12 else 0
        
        # Determine directions
        m15_dir = 'UP' if m15_slope > 0.001 else 'DOWN' if m15_slope < -0.001 else 'NONE'
        m30_dir = 'UP' if m30_slope > 0.001 else 'DOWN' if m30_slope < -0.001 else 'NONE'
        h1_dir = 'UP' if h1_slope > 0.001 else 'DOWN' if h1_slope < -0.001 else 'NONE'
        
        # Count alignment
        up_count = sum([1 for d in [m15_dir, m30_dir, h1_dir] if d == 'UP'])
        down_count = sum([1 for d in [m15_dir, m30_dir, h1_dir] if d == 'DOWN'])
        
        if up_count >= 2:
            htf_direction = 'UP'
            alignment = 60 + up_count * 15
        elif down_count >= 2:
            htf_direction = 'DOWN'
            alignment = 60 + down_count * 15
        elif up_count == 0 and down_count == 0:
            htf_direction = 'NONE'
            alignment = 50
        else:
            htf_direction = 'MIXED'
            alignment = 40
        
        return int(min(100, alignment)), htf_direction
    
    def _calc_volume_ratio(self, df: pd.DataFrame) -> float:
        """Calculate volume ratio (current volume / average volume)."""
        if 'volume' not in df.columns:
            return 1.0
        volume = df['volume'].values
        if len(volume) < 10:
            return 1.0
        avg_volume = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
        if avg_volume == 0:
            return 1.0
        return volume[-1] / avg_volume
    
    def _calc_noise_level_optimized(self, df: pd.DataFrame) -> float:
        """Calculate noise level using weighted efficiency (0-1)."""
        close = df['close'].values
        n = len(close)
        if n < 20:
            return 0.5
        
        # Calculate efficiency: net move / total movement
        total_move = sum(abs(close[i] - close[i-1]) for i in range(1, n))
        net_move = abs(close[-1] - close[0])
        efficiency = net_move / (total_move + 1e-9)
        
        # Adjust for trending markets (efficiency can be high even with noise)
        price_range = max(close[-n:]) - min(close[-n:])
        candle_body_ratio = abs(close[-1] - close[-2]) / (price_range + 1e-9) if n >= 2 else 0
        
        noise = max(0, min(1, 1 - efficiency))
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
        
        # Simplified: price at support with RSI oversold but rising = bullish divergence
        if rsi < 35 and close[-1] > min(close[-5:]):
            return True
        # Price at resistance, RSI overbought but falling = bearish divergence
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
    
    def _compute_dynamic_probabilities_optimized(self, df: pd.DataFrame, adx: float,
                                                 bbw: float, atr_percentile: float,
                                                 volatility_regime: str) -> tuple:
        """
        Compute breakout and reversal probabilities using price action and volatility.
        Returns (structure_type, bos_detected, breakout_prob, reversal_prob).
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        n = len(close)
        
        if n < 30:
            return 'RANGING', False, 30, 30
        
        # Identify recent swing highs and lows
        swing_highs = []
        swing_lows = []
        for i in range(5, n-5):
            if high[i] > max(high[i-5:i]) and high[i] > max(high[i+1:i+6]):
                swing_highs.append(high[i])
            if low[i] < min(low[i-5:i]) and low[i] < min(low[i+1:i+6]):
                swing_lows.append(low[i])
        
        # Determine structure type based on trend and range
        if len(swing_highs) > 0 and len(swing_lows) > 0:
            recent_range = max(close[-20:]) - min(close[-20:])
            avg_range = np.mean([high[i] - low[i] for i in range(max(0, n-30), n)])
            if recent_range > avg_range * 2:
                structure_type = 'BREAKOUT'
            elif recent_range < avg_range * 0.8:
                structure_type = 'RANGING'
            else:
                structure_type = 'TRENDING' if adx > 25 else 'RANGING'
        else:
            structure_type = 'RANGING'
        
        # BOS detection: price breaking recent swing levels
        bos_detected = False
        if len(swing_highs) > 0 and close[-1] > max(swing_highs[-3:]) * 1.002:
            bos_detected = True
        elif len(swing_lows) > 0 and close[-1] < min(swing_lows[-3:]) * 0.998:
            bos_detected = True
        
        # Breakout probability
        if bbw < 0.05 and volatility_regime == 'LOW':
            breakout_prob = 60 + (0.05 - bbw) * 200
        elif adx > 30 and volatility_regime in ['LOW', 'NORMAL']:
            breakout_prob = 50 + (adx - 30) / 2
        else:
            breakout_prob = 30 + (atr_percentile / 200) * 20
        
        # Reversal probability
        if adx > 50 and atr_percentile > 80:
            reversal_prob = 40 + (adx - 50) / 2
        elif atr_percentile > 120:
            reversal_prob = 50
        else:
            reversal_prob = 30
        
        return structure_type, bos_detected, int(min(100, breakout_prob)), int(min(100, reversal_prob))
    
    def _detect_wick_pattern_optimized(self, df: pd.DataFrame) -> tuple:
        """
        Detect wick patterns: ratio of lower wick to body, upper wick to body.
        Returns (lower_wick_ratio, upper_wick_ratio) as fractions of candle range.
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        n = len(close)
        
        if n < 5:
            return 0.3, 0.3
        
        lower_wicks = []
        upper_wicks = []
        
        for i in range(max(0, n-10), n):
            body_low = min(close[i], close[i-1] if i > 0 else close[i])
            body_high = max(close[i], close[i-1] if i > 0 else close[i])
            candle_range = high[i] - low[i] + 1e-9
            
            lower_wick = (min(close[i], body_low) - low[i]) / candle_range
            upper_wick = (high[i] - max(close[i], body_high)) / candle_range
            
            lower_wicks.append(lower_wick)
            upper_wicks.append(upper_wick)
        
        return np.mean(lower_wicks), np.mean(upper_wicks)
    
    def _detect_volatility_compression_optimized(self, df: pd.DataFrame, bbw: float, atr_percentile: float) -> bool:
        """Detect volatility compression (tightening ranges)."""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        n = len(close)
        
        if n < 20:
            return False
        
        # Check BBW compression
        if bbw < 0.06 and bbw > 0.01:
            return True
        
        # Check ATR compression
        if atr_percentile < 40:
            return True
        
        # Check recent range contraction
        recent_range = max(close[-10:]) - min(close[-10:])
        prior_range = max(close[-20:-10]) - min(close[-20:-10]) if n >= 20 else recent_range
        if prior_range > 0 and recent_range / prior_range < 0.7:
            return True
        
        return False

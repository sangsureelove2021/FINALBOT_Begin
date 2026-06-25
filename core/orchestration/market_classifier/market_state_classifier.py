import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from collections import deque

from core.orchestration.base_engine import BaseEngine


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
    
    def analyze(self, payload: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market state based on SSOT payload and precomputed Tier 1 data.
        
        Args:
            payload: SSOT dictionary containing 'm5', 'price_action', 'ohlcv'
            **kwargs:
                - trend_data
                - strength_data
                - volatility_data
                - structure_data
                - mtf_data
                - symbol
        """
        try:
            if not payload or 'm5' not in payload:
                return self._get_neutral_state("Insufficient payload data")
            
            trend_data = kwargs.get('trend_data', {})
            strength_data = kwargs.get('strength_data', {})
            volatility_data = kwargs.get('volatility_data', {})
            structure_data = kwargs.get('structure_data', {})
            mtf_data = kwargs.get('mtf_data', {})
            symbol = kwargs.get('symbol', '')
            is_otc = (symbol.upper().endswith('_OTC') or symbol.upper().endswith('-OTC')) if isinstance(symbol, str) else False
            
            metrics = self._compute_metrics(payload, trend_data, strength_data,
                                            volatility_data, structure_data, mtf_data,
                                            is_otc=is_otc)
            
            state, confidence = self._classify_state(metrics, is_otc=is_otc)
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
                'metrics': metrics
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._get_neutral_state(f"Error: {str(e)}")
    
    def _compute_metrics(self, payload: Dict[str, Any],
                        trend_data: Dict, strength_data: Dict,
                        volatility_data: Dict, structure_data: Dict,
                        mtf_data: Dict, is_otc: bool = False) -> Dict[str, Any]:
        
        m5 = payload.get('m5', {})
        pa = payload.get('price_action', {})
        meta = payload.get('ohlcv', {})
        
        close = meta.get('close', 0.0)
        
        # Engine Data
        trend_direction = trend_data.get('direction', 'NONE')
        trend_strength = trend_data.get('strength', 0)
        trend_slope = trend_data.get('slope', 0)
        trend_type = trend_data.get('type', 'CHOPPY')
        
        adx = strength_data.get('adx', 20)
        rsi = strength_data.get('rsi', 50)
        momentum_level = strength_data.get('momentum_level', 'NORMAL')
        strength_score = strength_data.get('strength_score', 50)
        
        atr_percentile = volatility_data.get('atr_percentile', 50)
        bbw = volatility_data.get('bbw', 0.05)
        volatility_regime = volatility_data.get('regime', 'NORMAL')
        volatility_score = volatility_data.get('volatility_score', 50)
        
        structure_type = structure_data.get('structure_type', 'RANGING')
        bos_detected = structure_data.get('bos_detected', False)
        breakout_prob = structure_data.get('breakout_probability', 30)
        reversal_prob = structure_data.get('reversal_probability', 30)
        
        alignment_score = mtf_data.get('alignment_score', 50)
        htf_direction = mtf_data.get('htf_direction', 'NONE')
        
        # Payload Data
        volume_ratio = 1.0 if is_otc else m5.get('volume_ratio', 1.0)
        volume_surge = volume_ratio > 1.5
        
        # Noise level from move_quality
        move_quality = pa.get('move_quality', 'NORMAL')
        noise_level = 0.2 if move_quality == 'CLEAN_TRENDING' else 0.8 if move_quality == 'NOISY' else 0.5
        
        rsi_extreme_bull = rsi > 75
        rsi_extreme_bear = rsi < 25
        
        price_above_ma20 = close > m5.get('ema20', close)
        price_above_ma50 = close > m5.get('ema50', close)
        
        wick_dominance = pa.get('wick_dominance', 'BALANCED')
        wick_lower_ratio = 0.6 if wick_dominance == 'HIGH_LOWER_WICK' else 0.3
        wick_upper_ratio = 0.6 if wick_dominance == 'HIGH_UPPER_WICK' else 0.3
        
        compression_detected = bbw < 0.05 or m5.get('box_tightness', 10.0) < 1.0
        
        sr_interaction = pa.get('sr_interaction', 'NONE')
        divergence_detected = False
        if rsi < 35 and sr_interaction == 'NEAR_SUPPORT':
            divergence_detected = True
        elif rsi > 65 and sr_interaction == 'NEAR_RESISTANCE':
            divergence_detected = True
            
        adaptive_adx_threshold = 18 if atr_percentile < 60 else 28 if atr_percentile > 140 else 22
        
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
    

